#!/usr/bin/env python3
"""Monitor indexing progress"""

import json
import time
import os

def check_progress():
    """Check current indexing progress"""
    try:
        # Read book index
        with open('chroma_db/book_index.json', 'r') as f:
            indexed_books = json.load(f)
        
        # Count total PDFs
        total_pdfs = 0
        for root, dirs, files in os.walk('books/'):
            for file in files:
                if file.endswith('.pdf'):
                    total_pdfs += 1
        
        # Read current status
        try:
            with open('chroma_db/index_status.json', 'r') as f:
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

if __name__ == "__main__":
    print("🔍 Monitoring indexing progress...")
    print("   Press Ctrl+C to stop")
    
    while True:
        indexed, total = check_progress()
        
        if indexed >= total and total > 0:
            print("\n✅ Indexing complete!")
            break
            
        time.sleep(10)  # Check every 10 seconds