#!/usr/bin/env python3
"""Monitor indexing progress"""

import json
import time
import os

from personal_doc_library.core.config import config

def check_progress():
    """Check current indexing progress"""
    try:
        # Read book index
        book_index_path = config.db_directory / 'book_index.json'
        with open(book_index_path, 'r') as f:
            indexed_books = json.load(f)
        
        # Count total PDFs
        total_pdfs = 0
        for root, dirs, files in os.walk(config.books_directory):
            for file in files:
                if file.endswith('.pdf'):
                    total_pdfs += 1
        
        # Read current status
        try:
            status_path = config.db_directory / 'index_status.json'
            with open(status_path, 'r') as f:
                status = json.load(f)
                current_file = status.get('details', {}).get('current_file', 'Unknown')
        except:
            current_file = "Unknown"
        
        indexed_count = len(indexed_books)
        percentage = (indexed_count / total_pdfs * 100) if total_pdfs > 0 else 0
        
        print(f"\n📊 Indexing Progress:")
        print(f"   Indexed: {indexed_count}/{total_pdfs} PDFs ({percentage:.1f}%)")
        print(f"   Currently processing: {current_file}")
        
        # Show recently indexed
        recent = sorted(indexed_books.items(), 
                       key=lambda x: x[1].get('indexed_at', ''), 
                       reverse=True)[:3]
        
        if recent:
            print(f"\n   Recently indexed:")
            for book, info in recent:
                print(f"   - {book} ({info.get('chunks', 0)} chunks)")
        
        return indexed_count, total_pdfs
        
    except Exception as e:
        print(f"Error: {e}")
        return 0, 0

def main() -> None:
    """Continuously report indexing progress."""
    print("🔍 Monitoring indexing progress...")
    print("   Press Ctrl+C to stop")

    while True:
        indexed, total = check_progress()

        if indexed >= total and total > 0:
            print("\n✅ Indexing complete!")
            break

        time.sleep(10)  # Check every 10 seconds


if __name__ == "__main__":
    main()
