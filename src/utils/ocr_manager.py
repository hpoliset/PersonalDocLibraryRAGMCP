#!/usr/bin/env python3
"""
OCR Manager - Handles OCR processing, tracking, and auto-reindexing
"""

import os
import json
import hashlib
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class OCRManager:
    def __init__(self, books_dir, db_dir):
        self.books_dir = books_dir
        self.db_dir = db_dir
        self.ocr_cache_dir = os.path.join(books_dir, '.ocr_cache')
        self.ocr_history_file = os.path.join(db_dir, 'ocr_history.json')
        
        # Create OCR cache directory if it doesn't exist
        os.makedirs(self.ocr_cache_dir, exist_ok=True)
        
        # Load OCR history
        self.ocr_history = self.load_ocr_history()
    
    def load_ocr_history(self):
        """Load OCR processing history"""
        if os.path.exists(self.ocr_history_file):
            try:
                with open(self.ocr_history_file, 'r') as f:
                    return json.load(f)
            except:
                logger.error("Failed to load OCR history, starting fresh")
        return {}
    
    def save_ocr_history(self):
        """Save OCR processing history"""
        try:
            with open(self.ocr_history_file, 'w') as f:
                json.dump(self.ocr_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save OCR history: {e}")
    
    def get_file_hash(self, file_path):
        """Get MD5 hash of file for tracking"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def has_been_ocrd(self, file_path):
        """Check if a file has already been OCR'd"""
        # Get relative path for consistent tracking
        rel_path = os.path.relpath(file_path, self.books_dir)
        
        # Check if file is in OCR history
        if rel_path in self.ocr_history:
            history = self.ocr_history[rel_path]
            
            # Check if current file hash matches OCR'd version
            # This handles cases where original was replaced with OCR version
            current_hash = self.get_file_hash(file_path)
            if history.get('ocr_hash') == current_hash:
                return True
            
            # File has been OCR'd before (even if it failed or was modified)
            if history.get('ocr_attempted'):
                return True
        
        return False
    
    def mark_as_ocrd(self, original_path, ocr_path=None, success=True, error_msg=None):
        """Mark a file as having been OCR'd"""
        rel_path = os.path.relpath(original_path, self.books_dir)
        
        entry = {
            'ocr_attempted': True,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'original_hash': self.get_file_hash(original_path) if os.path.exists(original_path) else None
        }
        
        if ocr_path and os.path.exists(ocr_path):
            entry['ocr_hash'] = self.get_file_hash(ocr_path)
            entry['ocr_path'] = os.path.relpath(ocr_path, self.books_dir)
        
        if error_msg:
            entry['error'] = error_msg
        
        self.ocr_history[rel_path] = entry
        self.save_ocr_history()
    
    def process_ocr(self, file_path, force=False):
        """
        Process OCR for a PDF file
        
        Args:
            file_path: Path to PDF file
            force: Force OCR even if already processed
        
        Returns:
            dict with status and details
        """
        # Check if already OCR'd
        if not force and self.has_been_ocrd(file_path):
            logger.info(f"Skipping OCR for {os.path.basename(file_path)} - already processed")
            return {
                'status': 'skipped',
                'reason': 'already_processed',
                'file': file_path
            }
        
        # Generate OCR output path
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        ocr_output = os.path.join(self.ocr_cache_dir, f"{base_name}_OCR.pdf")
        
        logger.info(f"Starting OCR for {os.path.basename(file_path)}")
        
        try:
            # Run OCR with ocrmypdf
            cmd = [
                'ocrmypdf',
                '--force-ocr',  # OCR all pages, even those with text
                '--continue-on-soft-render-error',  # Continue on PDF errors
                '--output-type', 'pdf',
                '--optimize', '1',
                '--jobs', '4',
                file_path,
                ocr_output
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode == 0:
                # OCR successful
                logger.info(f"OCR successful for {os.path.basename(file_path)}")
                
                # Save OCR version alongside original
                ocr_dest = self.save_ocr_alongside_original(file_path, ocr_output)
                
                return {
                    'status': 'success',
                    'original': file_path,
                    'ocr_file': ocr_dest if ocr_dest else ocr_output
                }
            else:
                # OCR failed
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                logger.error(f"OCR failed for {os.path.basename(file_path)}: {error_msg}")
                
                # Mark as attempted but failed
                self.mark_as_ocrd(file_path, success=False, error_msg=error_msg)
                
                return {
                    'status': 'failed',
                    'error': error_msg,
                    'file': file_path
                }
                
        except subprocess.TimeoutExpired:
            error_msg = "OCR timeout after 30 minutes"
            logger.error(f"OCR timeout for {os.path.basename(file_path)}")
            self.mark_as_ocrd(file_path, success=False, error_msg=error_msg)
            return {
                'status': 'timeout',
                'error': error_msg,
                'file': file_path
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"OCR exception for {os.path.basename(file_path)}: {e}")
            self.mark_as_ocrd(file_path, success=False, error_msg=error_msg)
            return {
                'status': 'error',
                'error': error_msg,
                'file': file_path
            }
    
    def save_ocr_alongside_original(self, original_path, ocr_path):
        """Save OCR version alongside original and add original to skip list"""
        try:
            # Generate OCR filename in same directory as original
            original_dir = os.path.dirname(original_path)
            original_name = os.path.splitext(os.path.basename(original_path))[0]
            ocr_dest = os.path.join(original_dir, f"{original_name}_OCR.pdf")
            
            # Copy OCR version to destination
            logger.info(f"Saving OCR version as {os.path.basename(ocr_dest)}")
            shutil.copy2(ocr_path, ocr_dest)
            
            # Add original to skip list
            self.add_to_skip_list(original_path)
            
            # Update OCR history with new location
            self.mark_as_ocrd(original_path, ocr_dest, success=True)
            
            logger.info(f"Successfully saved OCR version, original added to skip list")
            
            return ocr_dest
            
        except Exception as e:
            logger.error(f"Failed to save OCR version: {e}")
            return None
    
    def add_to_skip_list(self, file_path):
        """Add a file to the skip list (files that have OCR versions)"""
        skip_list_file = os.path.join(self.db_dir, 'skip_list.json')
        
        # Load existing skip list
        skip_list = {}
        if os.path.exists(skip_list_file):
            try:
                with open(skip_list_file, 'r') as f:
                    skip_list = json.load(f)
            except:
                pass
        
        # Add to skip list with metadata
        rel_path = os.path.relpath(file_path, self.books_dir)
        original_name = os.path.splitext(os.path.basename(file_path))[0]
        ocr_version = f"{original_name}_OCR.pdf"
        
        skip_list[rel_path] = {
            'reason': 'has_ocr_version',
            'ocr_file': ocr_version,
            'added': datetime.now().isoformat()
        }
        
        # Save skip list
        try:
            with open(skip_list_file, 'w') as f:
                json.dump(skip_list, f, indent=2)
            logger.info(f"Added {rel_path} to skip list")
        except Exception as e:
            logger.error(f"Failed to save skip list: {e}")
    
    def get_ocr_candidates(self, failed_pdfs_file=None):
        """
        Get list of PDFs that could benefit from OCR
        
        Args:
            failed_pdfs_file: Path to failed PDFs JSON file
        
        Returns:
            List of file paths that haven't been OCR'd yet
        """
        candidates = []
        
        # Load failed PDFs if provided
        failed_pdfs = {}
        if failed_pdfs_file and os.path.exists(failed_pdfs_file):
            try:
                with open(failed_pdfs_file, 'r') as f:
                    failed_pdfs = json.load(f)
            except:
                pass
        
        # Check all failed PDFs
        for rel_path in failed_pdfs.keys():
            full_path = os.path.join(self.books_dir, rel_path)
            
            # Skip if doesn't exist or already OCR'd
            if not os.path.exists(full_path):
                continue
            
            if not self.has_been_ocrd(full_path):
                candidates.append(full_path)
        
        return candidates
    
    def cleanup_ocr_cache(self, keep_days=7):
        """Clean up old OCR cache files"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (keep_days * 24 * 3600)
        
        for file_name in os.listdir(self.ocr_cache_dir):
            file_path = os.path.join(self.ocr_cache_dir, file_name)
            
            # Check file age
            if os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed old OCR cache file: {file_name}")
                except:
                    pass


if __name__ == "__main__":
    # Test/utility mode
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR Manager for Personal Document Library")
    parser.add_argument('--books-dir', default=os.environ.get('PERSONAL_LIBRARY_DOC_PATH', '/Users/hpoliset/SpiritualLibrary'))
    parser.add_argument('--db-dir', default=os.environ.get('PERSONAL_LIBRARY_DB_PATH', '/Users/hpoliset/DocumentIndexerMCP/chroma_db'))
    parser.add_argument('--check', help="Check if file has been OCR'd", metavar='FILE')
    parser.add_argument('--process', help="Process OCR for a file", metavar='FILE')
    parser.add_argument('--list-candidates', action='store_true', help="List OCR candidates from failed PDFs")
    parser.add_argument('--cleanup', action='store_true', help="Clean up old OCR cache files")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = OCRManager(args.books_dir, args.db_dir)
    
    if args.check:
        has_ocr = manager.has_been_ocrd(args.check)
        print(f"File {'HAS' if has_ocr else 'has NOT'} been OCR'd: {args.check}")
        
    elif args.process:
        result = manager.process_ocr(args.process)
        print(json.dumps(result, indent=2))
        
    elif args.list_candidates:
        failed_file = os.path.join(args.db_dir, 'failed_pdfs.json')
        candidates = manager.get_ocr_candidates(failed_file)
        print(f"Found {len(candidates)} OCR candidates:")
        for file_path in candidates[:10]:  # Show first 10
            print(f"  - {os.path.basename(file_path)}")
        if len(candidates) > 10:
            print(f"  ... and {len(candidates) - 10} more")
            
    elif args.cleanup:
        manager.cleanup_ocr_cache()
        print("OCR cache cleanup complete")
    
    else:
        parser.print_help()