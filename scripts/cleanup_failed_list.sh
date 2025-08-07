#!/bin/bash

# Script to clean up the failed documents list by removing documents that have been successfully indexed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔮 Cleaning up failed documents list"
echo "===================================="
echo ""

python3 -c "
import json
import os

failed_file = '$PROJECT_ROOT/chroma_db/failed_pdfs.json'
index_file = '$PROJECT_ROOT/chroma_db/book_index.json'

if not os.path.exists(failed_file):
    print('No failed documents file found.')
    exit(0)

if not os.path.exists(index_file):
    print('No book index file found.')
    exit(0)

# Load both files
with open(failed_file, 'r') as f:
    failed_docs = json.load(f)

with open(index_file, 'r') as f:
    indexed_docs = json.load(f)

# Create a set of indexed document names for faster lookup
indexed_names = set()
for path in indexed_docs.keys():
    indexed_names.add(os.path.basename(path))
    indexed_names.add(path)

# Find documents to remove from failed list
to_remove = []
for failed_path in list(failed_docs.keys()):
    # Check if this document has been successfully indexed
    if failed_path in indexed_names or os.path.basename(failed_path) in indexed_names:
        to_remove.append(failed_path)

# Remove the documents
if to_remove:
    print(f'Found {len(to_remove)} documents to remove from failed list:')
    for doc in to_remove:
        print(f'  - {os.path.basename(doc)}')
        del failed_docs[doc]
    
    # Save the updated failed list
    with open(failed_file, 'w') as f:
        json.dump(failed_docs, f, indent=2)
    
    print(f'\\n✅ Removed {len(to_remove)} successfully indexed documents from failed list')
    print(f'📊 Remaining failed documents: {len(failed_docs)}')
else:
    print('✅ No successfully indexed documents found in failed list')
    print(f'📊 Total failed documents: {len(failed_docs)}')

# Show summary of remaining failed documents
if failed_docs:
    print('\\nRemaining failed documents by type:')
    type_counts = {}
    for path in failed_docs.keys():
        ext = os.path.splitext(path)[1].lower()
        type_counts[ext] = type_counts.get(ext, 0) + 1
    
    for ext, count in sorted(type_counts.items()):
        print(f'  {ext}: {count}')
"