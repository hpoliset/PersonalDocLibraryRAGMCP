#!/usr/bin/env python3
"""
Simple test to verify failed document tracking uses relative paths
"""

import os
import json
from pathlib import Path

# Test the current failed_pdfs.json
failed_file = "/Users/hpoliset/DocumentIndexerMCP/chroma_db/failed_pdfs.json"

if os.path.exists(failed_file):
    with open(failed_file) as f:
        failed_docs = json.load(f)
    
    print(f"Current failed documents: {len(failed_docs)}")
    print("\nKeys in failed list:")
    for key in list(failed_docs.keys())[:10]:  # Show first 10
        if key.startswith("/"):
            print(f"  ✗ ABSOLUTE: {key}")
        else:
            print(f"  ✓ RELATIVE: {key}")
    
    # Check for duplicates that might be due to basename collision
    basenames = {}
    for key in failed_docs.keys():
        basename = os.path.basename(key)
        if basename not in basenames:
            basenames[basename] = []
        basenames[basename].append(key)
    
    print("\nChecking for basename collisions:")
    collisions = 0
    for basename, paths in basenames.items():
        if len(paths) > 1:
            collisions += 1
            print(f"  Collision on '{basename}': {len(paths)} files")
            for p in paths:
                print(f"    - {p}")
    
    if collisions == 0:
        print("  No basename collisions found")
    
    # Simulate what would be tracked with the fix
    books_dir = "/Users/hpoliset/SpiritualLibrary"
    print(f"\nSimulating fix with books_directory: {books_dir}")
    
    fixed_keys = {}
    for full_path in [
        "/Users/hpoliset/SpiritualLibrary/Babuji's Books/Letters of the Master/Letters of the Master 4/1971.doc",
        "/Users/hpoliset/SpiritualLibrary/Babuji's Books/Letters of the Master/Letters of the Master 4/1967.doc",
    ]:
        rel_path = os.path.relpath(full_path, books_dir)
        fixed_keys[rel_path] = {"full_path": full_path}
        print(f"  {full_path}")
        print(f"    -> {rel_path}")
else:
    print(f"Failed documents file not found: {failed_file}")