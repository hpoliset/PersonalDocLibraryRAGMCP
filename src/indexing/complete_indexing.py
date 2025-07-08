#!/usr/bin/env python3
"""Complete the indexing of spiritual library PDFs with robust error handling."""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('complete_indexing.log')
    ]
)

# Maximum file size (500MB)
MAX_FILE_SIZE = 500 * 1024 * 1024

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared_rag import SharedRAG

def calculate_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def should_skip_pdf(filepath, rel_path):
    """Determine if a PDF should be skipped."""
    # Skip files in originals directory (these are backups)
    if 'originals/' in rel_path:
        return True, "Backup file in originals directory"
    
    # Check file size
    file_size = os.path.getsize(filepath)
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        return True, f"File too large ({size_mb:.1f}MB > 500MB limit)"
    
    # Known problematic files that produce 0 chunks
    problematic_files = [
        "Vrads-dedication.jpg.pdf",  # Image file
        "13 chakras-colored.pdf",    # Image file
        "Yearning of the Heart _Vol 1_Wrapper_190419.pdf",  # Cover/wrapper
        "CWRL 2_Curves.pdf",         # Graphics file
        "ShriRamSandesh - By Lalaji.pdf"  # Problematic formatting
    ]
    
    for problem_file in problematic_files:
        if problem_file in rel_path:
            return True, "Known problematic file (image/graphics only)"
    
    return False, None

def main():
    """Main indexing function."""
    logging.info("Starting complete indexing process...")
    
    try:
        # Initialize SharedRAG
        rag = SharedRAG()
        
        # Get all PDFs
        books_dir = Path("books")
        all_pdfs = []
        
        for root, dirs, files in os.walk(books_dir):
            for file in files:
                if file.endswith('.pdf'):
                    full_path = Path(root) / file
                    rel_path = str(full_path.relative_to(books_dir))
                    all_pdfs.append((full_path, rel_path))
        
        logging.info(f"Found {len(all_pdfs)} total PDF files")
        
        # Filter out already indexed PDFs
        unindexed_pdfs = []
        skipped_pdfs = []
        
        for filepath, rel_path in all_pdfs:
            # Check if should skip
            should_skip, skip_reason = should_skip_pdf(filepath, rel_path)
            if should_skip:
                skipped_pdfs.append((rel_path, skip_reason))
                # Add to index as skipped
                rag.book_index[rel_path] = {
                    'hash': 'SKIPPED',
                    'chunks': 0,
                    'pages': 0,
                    'indexed_at': datetime.now().isoformat(),
                    'note': skip_reason
                }
                continue
            
            # Check if already indexed
            if rel_path not in rag.book_index:
                unindexed_pdfs.append((filepath, rel_path))
        
        logging.info(f"Already indexed: {len(rag.book_index)} PDFs")
        logging.info(f"Skipped: {len(skipped_pdfs)} PDFs")
        logging.info(f"To index: {len(unindexed_pdfs)} PDFs")
        
        # Log skipped files
        if skipped_pdfs:
            logging.info("\nSkipped PDFs:")
            for pdf, reason in skipped_pdfs:
                logging.info(f"  - {pdf}: {reason}")
        
        # Save updated index with skipped files
        rag.save_book_index()
        
        # Index remaining PDFs
        if unindexed_pdfs:
            logging.info(f"\nIndexing {len(unindexed_pdfs)} PDFs...")
            
            for i, (filepath, rel_path) in enumerate(unindexed_pdfs, 1):
                logging.info(f"\n[{i}/{len(unindexed_pdfs)}] Processing: {rel_path}")
                
                try:
                    # Try to index with timeout
                    success = rag.process_pdf_with_timeout(
                        str(filepath), 
                        rel_path, 
                        timeout_minutes=10
                    )
                    
                    if success:
                        logging.info(f"✅ Successfully indexed: {rel_path}")
                    else:
                        logging.warning(f"⚠️  Failed to index: {rel_path}")
                        # Mark as failed in index
                        rag.book_index[rel_path] = {
                            'hash': 'FAILED',
                            'chunks': 0,
                            'pages': 0,
                            'indexed_at': datetime.now().isoformat(),
                            'note': 'Failed to process within timeout'
                        }
                        rag.save_book_index()
                        
                except Exception as e:
                    logging.error(f"❌ Error processing {rel_path}: {str(e)}")
                    # Mark as failed in index
                    rag.book_index[rel_path] = {
                        'hash': 'FAILED',
                        'chunks': 0,
                        'pages': 0,
                        'indexed_at': datetime.now().isoformat(),
                        'note': f'Error: {str(e)}'
                    }
                    rag.save_book_index()
        
        # Final summary
        logging.info("\n" + "="*60)
        logging.info("INDEXING COMPLETE!")
        logging.info("="*60)
        
        # Count statistics
        total_indexed = 0
        total_chunks = 0
        failed_count = 0
        skipped_count = 0
        
        for pdf, info in rag.book_index.items():
            if info['hash'] == 'SKIPPED':
                skipped_count += 1
            elif info['hash'] == 'FAILED':
                failed_count += 1
            elif info['chunks'] > 0:
                total_indexed += 1
                total_chunks += info['chunks']
        
        logging.info(f"\nFinal Statistics:")
        logging.info(f"  Total PDF files: {len(all_pdfs)}")
        logging.info(f"  Successfully indexed: {total_indexed}")
        logging.info(f"  Failed to index: {failed_count}")
        logging.info(f"  Skipped (backups/problematic): {skipped_count}")
        logging.info(f"  Total chunks in database: {total_chunks}")
        
        # List any failed PDFs
        if failed_count > 0:
            logging.info("\nFailed PDFs:")
            for pdf, info in rag.book_index.items():
                if info['hash'] == 'FAILED':
                    logging.info(f"  - {pdf}: {info.get('note', 'Unknown error')}")
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()