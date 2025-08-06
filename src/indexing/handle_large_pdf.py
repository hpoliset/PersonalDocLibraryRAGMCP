#!/usr/bin/env python3
"""
Large PDF Handler - Solution for indexing very large PDFs like 799MB Whispers Vol 6

This script provides multiple strategies for handling large PDFs:
1. Use pre-cleaned version if available
2. Split PDF into smaller chunks
3. Process with reduced memory footprint
4. Stream processing for massive files

Author: Claude Code Assistant
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader
import hashlib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.shared_rag import SharedRAG
from src.core.config import config

class LargePDFHandler:
    def __init__(self):
        self.rag = SharedRAG()
        self.books_directory = Path(config.books_directory)
        self.temp_directory = Path(config.db_directory) / "temp_splits"
        self.temp_directory.mkdir(exist_ok=True)
        
    def get_file_hash(self, filepath):
        """Get file hash for tracking"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def check_cleaned_version(self, pdf_path):
        """Check if a cleaned version exists"""
        cleaned_path = str(pdf_path) + ".cleaned.tmp"
        if os.path.exists(cleaned_path):
            file_size = os.path.getsize(cleaned_path) / (1024 * 1024)  # MB
            print(f"✅ Found cleaned version: {cleaned_path} ({file_size:.1f}MB)")
            return cleaned_path
        return None
    
    def split_large_pdf(self, pdf_path, max_pages_per_chunk=100):
        """Split large PDF into smaller chunks"""
        print(f"📄 Splitting large PDF: {pdf_path}")
        
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            print(f"📊 Total pages: {total_pages}")
            
            if total_pages <= max_pages_per_chunk:
                print("📝 PDF is small enough, no splitting needed")
                return [pdf_path]
            
            chunk_files = []
            base_name = Path(pdf_path).stem
            
            for i in range(0, total_pages, max_pages_per_chunk):
                end_page = min(i + max_pages_per_chunk, total_pages)
                chunk_filename = f"{base_name}_chunk_{i+1:03d}_{end_page:03d}.pdf"
                chunk_path = self.temp_directory / chunk_filename
                
                print(f"📦 Creating chunk {len(chunk_files)+1}: pages {i+1}-{end_page}")
                
                writer = PdfWriter()
                for page_num in range(i, end_page):
                    writer.add_page(reader.pages[page_num])
                
                with open(chunk_path, 'wb') as output_file:
                    writer.write(output_file)
                
                chunk_files.append(str(chunk_path))
                
                # Check chunk size
                chunk_size = os.path.getsize(chunk_path) / (1024 * 1024)
                print(f"   💾 Chunk size: {chunk_size:.1f}MB")
            
            print(f"✅ Split into {len(chunk_files)} chunks")
            return chunk_files
            
        except Exception as e:
            print(f"❌ Error splitting PDF: {e}")
            return [pdf_path]  # Return original if splitting fails
    
    def process_large_pdf_strategy(self, pdf_path, rel_path):
        """
        Multi-strategy approach for large PDFs:
        1. Try cleaned version first
        2. Split into chunks if too large
        3. Process each chunk separately
        4. Combine results
        """
        print(f"\n🔍 Processing large PDF: {rel_path}")
        
        # Strategy 1: Check for cleaned version
        cleaned_path = self.check_cleaned_version(pdf_path)
        if cleaned_path:
            print("🔄 Using cleaned version...")
            try:
                if self.rag.process_pdf_with_timeout(cleaned_path, rel_path + " (cleaned)"):
                    print("✅ Successfully indexed cleaned version")
                    return True
                else:
                    print("⚠️ Cleaned version failed, trying splitting...")
            except Exception as e:
                print(f"⚠️ Cleaned version error: {e}, trying splitting...")
        
        # Strategy 2: Split into chunks
        original_size = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"📏 Original size: {original_size:.1f}MB")
        
        if original_size > 100:  # Split if larger than 100MB
            chunk_files = self.split_large_pdf(pdf_path, max_pages_per_chunk=50)
            
            if len(chunk_files) > 1:
                success_count = 0
                total_chunks = 0
                
                for i, chunk_path in enumerate(chunk_files):
                    chunk_rel_path = f"{rel_path} (chunk {i+1}/{len(chunk_files)})"
                    print(f"\n📦 Processing chunk {i+1}/{len(chunk_files)}: {Path(chunk_path).name}")
                    
                    try:
                        if self.rag.process_pdf_with_timeout(chunk_path, chunk_rel_path):
                            success_count += 1
                            print(f"✅ Chunk {i+1} indexed successfully")
                        else:
                            print(f"❌ Chunk {i+1} failed")
                        total_chunks += 1
                    except Exception as e:
                        print(f"❌ Chunk {i+1} error: {e}")
                        total_chunks += 1
                
                # Cleanup chunks
                for chunk_path in chunk_files:
                    if chunk_path != pdf_path:  # Don't delete original
                        try:
                            os.remove(chunk_path)
                        except:
                            pass
                
                print(f"\n📊 Chunk processing summary: {success_count}/{total_chunks} successful")
                
                if success_count > 0:
                    # Update book index with combined result
                    self.update_chunked_book_entry(rel_path, chunk_files, success_count, total_chunks)
                    return True
                else:
                    return False
        
        # Strategy 3: Try direct processing with extended timeout (last resort)
        print("🔄 Attempting direct processing with extended timeout...")
        try:
            return self.rag.process_pdf_with_timeout(pdf_path, rel_path, timeout_minutes=20)
        except Exception as e:
            print(f"❌ Direct processing failed: {e}")
            return False
    
    def update_chunked_book_entry(self, rel_path, chunk_files, success_count, total_chunks):
        """Update book index for chunked processing"""
        book_index_path = Path(config.db_directory) / "book_index.json"
        
        try:
            if book_index_path.exists():
                with open(book_index_path, 'r') as f:
                    book_index = json.load(f)
            else:
                book_index = {}
            
            # Calculate approximate stats
            total_chunks_indexed = success_count * 50  # Approximate chunks per split
            total_pages_estimated = total_chunks * 50  # Approximate pages per split
            
            book_index[rel_path] = {
                "hash": "CHUNKED_PROCESSING",
                "chunks": total_chunks_indexed,
                "pages": total_pages_estimated,
                "indexed_at": datetime.now().isoformat(),
                "note": f"Processed as {success_count}/{total_chunks} chunks due to large size"
            }
            
            with open(book_index_path, 'w') as f:
                json.dump(book_index, f, indent=2)
                
            print(f"📝 Updated book index: {success_count}/{total_chunks} chunks processed")
            
        except Exception as e:
            print(f"⚠️ Error updating book index: {e}")

def main():
    """Handle the large Whispers Vol 6 PDF specifically"""
    handler = LargePDFHandler()
    
    # Target the problematic file
    rel_path = "Whispers/Whispers Vol 6 - Lowres.pdf"
    large_pdf_path = str(config.books_directory / rel_path)
    
    if not os.path.exists(large_pdf_path):
        print(f"❌ File not found: {large_pdf_path}")
        return False
    
    print("🚀 Starting large PDF processing...")
    success = handler.process_large_pdf_strategy(large_pdf_path, rel_path)
    
    if success:
        print("✅ Large PDF processing completed successfully!")
        
        # Remove from failed PDFs list
        failed_pdfs_path = Path(config.db_directory) / "failed_pdfs.json"
        if failed_pdfs_path.exists():
            try:
                with open(failed_pdfs_path, 'r') as f:
                    failed_pdfs = json.load(f)
                
                key_to_remove = "Whispers Vol 6 - Lowres.pdf"
                if key_to_remove in failed_pdfs:
                    del failed_pdfs[key_to_remove]
                    
                    with open(failed_pdfs_path, 'w') as f:
                        json.dump(failed_pdfs, f, indent=2)
                    
                    print(f"🗑️ Removed {key_to_remove} from failed PDFs list")
            except Exception as e:
                print(f"⚠️ Error updating failed PDFs: {e}")
    else:
        print("❌ Large PDF processing failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)