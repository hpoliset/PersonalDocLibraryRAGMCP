#!/usr/bin/env python3
"""Skip problematic PDF and continue indexing"""

import json
import os
from datetime import datetime

# Load book index
with open('chroma_db/book_index.json', 'r') as f:
    book_index = json.load(f)

# Mark the problematic file as "indexed" to skip it
book_index['Whispers/Whispers Vol 6 - Lowres.pdf'] = {
    'hash': 'SKIPPED_TOO_LARGE',
    'chunks': 0,
    'pages': 0,
    'indexed_at': datetime.now().isoformat(),
    'note': 'Skipped due to memory issues - file too large (799MB)'
}

# Save updated index
with open('chroma_db/book_index.json', 'w') as f:
    json.dump(book_index, f, indent=2)

# Update failed PDFs log
failed_pdfs = {}
if os.path.exists('chroma_db/failed_pdfs.json'):
    with open('chroma_db/failed_pdfs.json', 'r') as f:
        failed_pdfs = json.load(f)

failed_pdfs['Whispers Vol 6 - Lowres.pdf'] = {
    'error': 'Process killed - file too large (799MB)',
    'cleaned': False,
    'skipped': True,
    'attempted_at': datetime.now().isoformat()
}

with open('chroma_db/failed_pdfs.json', 'w') as f:
    json.dump(failed_pdfs, f, indent=2)

print("✅ Marked 'Whispers Vol 6 - Lowres.pdf' as skipped")
print("📊 You can now continue indexing the remaining PDFs")