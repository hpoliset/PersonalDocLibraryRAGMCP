#!/usr/bin/env python3
"""Fix the skipped file to use actual file hash"""

import json
import hashlib
import os

def get_file_hash(filepath):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Load book index
with open('chroma_db/book_index.json', 'r') as f:
    book_index = json.load(f)

# Get actual hash of the problematic file
problematic_file = 'books/Whispers/Whispers Vol 6 - Lowres.pdf'
if os.path.exists(problematic_file):
    print(f"Calculating hash for {problematic_file}...")
    actual_hash = get_file_hash(problematic_file)
    print(f"Hash: {actual_hash}")
    
    # Update the entry with actual hash so it won't be re-processed
    book_index['Whispers/Whispers Vol 6 - Lowres.pdf'] = {
        'hash': actual_hash,
        'chunks': 0,
        'pages': 0,
        'indexed_at': book_index['Whispers/Whispers Vol 6 - Lowres.pdf']['indexed_at'],
        'note': 'Skipped due to memory issues - file too large (799MB)'
    }
    
    # Save updated index
    with open('chroma_db/book_index.json', 'w') as f:
        json.dump(book_index, f, indent=2)
    
    print("✅ Updated file hash - it won't be processed again")
else:
    print("❌ File not found!")