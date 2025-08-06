#!/usr/bin/env python3
"""Find PDFs that haven't been indexed yet."""
import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import config

books_dir = config.books_directory
index_file = config.db_directory / "book_index.json"

# Load existing index
with open(index_file) as f:
    book_index = json.load(f)

# Get all PDFs
all_pdfs = []
for root, dirs, files in os.walk(books_dir):
    for file in files:
        if file.endswith('.pdf'):
            full_path = Path(root) / file
            rel_path = str(full_path.relative_to(books_dir))
            all_pdfs.append(rel_path)

# Find unindexed
indexed_pdfs = set(book_index.keys())
all_pdfs_set = set(all_pdfs)
unindexed = sorted(all_pdfs_set - indexed_pdfs)

print(f"Total PDFs: {len(all_pdfs)}")
print(f"Indexed PDFs: {len(indexed_pdfs)}")
print(f"Unindexed PDFs: {len(unindexed)}")
print("\nUnindexed PDFs:")
for pdf in unindexed:
    print(f"  - {pdf}")