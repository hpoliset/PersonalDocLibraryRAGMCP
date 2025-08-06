#!/usr/bin/env python3
"""
Check and diagnose indexing status
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import config
from index_lock import IndexLock

def main():
    print("🔍 Checking Indexing Status")
    print("=" * 60)
    
    # Check lock status
    lock = IndexLock()
    lock_info = lock.get_lock_info()
    
    print("\n📌 Lock Status:")
    if lock_info['exists']:
        print(f"   Lock exists: Yes")
        print(f"   PID: {lock_info['pid']}")
        print(f"   Age: {lock_info['age_minutes']:.1f} minutes")
        print(f"   Stale: {'Yes' if lock_info['stale'] else 'No'}")
        
        if lock_info['stale']:
            print("\n   ⚠️  Lock is stale - removing it")
            lock.clean_stale_lock()
            print("   ✅ Stale lock removed")
    else:
        print("   Lock exists: No")
    
    # Check status file
    status_file = config.db_directory / "index_status.json"
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        print("\n📊 Last Status:")
        print(f"   Status: {status.get('status', 'unknown')}")
        if 'timestamp' in status:
            timestamp = datetime.fromisoformat(status['timestamp'])
            age_minutes = (datetime.now() - timestamp).total_seconds() / 60
            print(f"   Updated: {age_minutes:.1f} minutes ago")
        
        if 'details' in status:
            details = status['details']
            if 'current_file' in details:
                print(f"   Last file: {details['current_file']}")
    
    # Check book index
    book_index_file = config.db_directory / "book_index.json"
    books = {}
    if os.path.exists(book_index_file):
        with open(book_index_file, 'r') as f:
            books = json.load(f)
    print(f"\n📚 Books indexed: {len(books)}")
    
    # Check failed PDFs
    failed_file = config.db_directory / "failed_pdfs.json"
    failed = {}
    if os.path.exists(failed_file):
        with open(failed_file, 'r') as f:
            failed = json.load(f)
    print(f"❌ Failed books: {len(failed)}")
    
    if failed:
        print("\nFailed books:")
        for path, info in list(failed.items())[:5]:
            print(f"   - {path}")
            print(f"     Error: {info.get('error', 'Unknown')}")
            print(f"     Retries: {info.get('retry_count', 0)}")
    
    # Count total PDFs
    total_pdfs = 0
    books_dir = config.books_directory
    if books_dir.exists():
        for root, dirs, files in os.walk(books_dir):
            total_pdfs += sum(1 for f in files if f.lower().endswith('.pdf'))
    
    indexed_count = len(books)
    failed_count = len(failed)
    remaining_count = total_pdfs - indexed_count - failed_count
    
    print(f"\n📁 Total PDFs in {books_dir.name} folder: {total_pdfs}")
    print(f"📊 Remaining to index: {remaining_count}")
    print(f"   ✅ Successfully indexed: {indexed_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   ⏳ Pending: {remaining_count}")
    
    # Check for specific problematic file
    whispers_path = "Babuji's Books/Whispers/Vol. 2 1944-45/For Print_Whispers_Vol. 2/Whispers_Inner_Vol2.pdf"
    if whispers_path not in books:
        print(f"\n⚠️  Whispers_Inner_Vol2.pdf is NOT indexed")
        full_path = config.books_directory / whispers_path
        if os.path.exists(full_path):
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"   File exists: {size_mb:.1f} MB")
            if whispers_path in failed:
                print(f"   Status: Failed")
                print(f"   Error: {failed[whispers_path].get('error', 'Unknown')}")
            else:
                print(f"   Status: Not attempted yet")

if __name__ == "__main__":
    main()