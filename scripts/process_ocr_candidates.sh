#!/bin/bash

# Process OCR Candidates Script
# Automatically OCRs failed PDFs that haven't been OCR'd yet

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source configuration
source "$PROJECT_ROOT/scripts/config.sh" 2>/dev/null || true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 OCR Candidate Processor"
echo "=========================="

# Check for ocrmypdf
if ! command -v ocrmypdf &> /dev/null; then
    echo -e "${RED}❌ Error: ocrmypdf is not installed${NC}"
    echo "Install with: brew install ocrmypdf"
    exit 1
fi

# Get OCR candidates
echo -e "\n${YELLOW}Finding OCR candidates from failed PDFs...${NC}"

cd "$PROJECT_ROOT"

# Use Python to get and process candidates
"$VENV_PYTHON" << 'EOF'
import json
import os
import sys
from src.utils.ocr_manager import OCRManager

# Initialize manager
books_dir = os.environ.get('PERSONAL_LIBRARY_DOC_PATH', '/Users/hpoliset/SpiritualLibrary')
db_dir = os.environ.get('PERSONAL_LIBRARY_DB_PATH', '/Users/hpoliset/DocumentIndexerMCP/chroma_db')

manager = OCRManager(books_dir, db_dir)

# Get candidates
failed_file = os.path.join(db_dir, 'failed_pdfs.json')
candidates = manager.get_ocr_candidates(failed_file)

if not candidates:
    print("✅ No OCR candidates found - all failed PDFs have been processed")
    sys.exit(0)

print(f"\n📚 Found {len(candidates)} PDFs that could benefit from OCR:")
for i, path in enumerate(candidates[:5], 1):
    print(f"  {i}. {os.path.basename(path)}")

if len(candidates) > 5:
    print(f"  ... and {len(candidates) - 5} more")

# Ask for confirmation
print("\nOptions:")
print("  1. Process ALL candidates")
print("  2. Process first 5 only")
print("  3. Select specific file")
print("  4. Cancel")

try:
    choice = input("\nEnter choice (1-4): ").strip()
except KeyboardInterrupt:
    print("\nCancelled")
    sys.exit(0)

if choice == '4':
    print("Cancelled")
    sys.exit(0)

# Determine which files to process
if choice == '1':
    to_process = candidates
elif choice == '2':
    to_process = candidates[:5]
elif choice == '3':
    print("\nAvailable files:")
    for i, path in enumerate(candidates, 1):
        print(f"  {i}. {os.path.basename(path)}")
    try:
        idx = int(input("Enter file number: ")) - 1
        if 0 <= idx < len(candidates):
            to_process = [candidates[idx]]
        else:
            print("Invalid selection")
            sys.exit(1)
    except:
        print("Invalid input")
        sys.exit(1)
else:
    print("Invalid choice")
    sys.exit(1)

# Process selected files
print(f"\n🚀 Processing {len(to_process)} file(s)...")
success_count = 0
failed_count = 0

for file_path in to_process:
    print(f"\n📄 Processing: {os.path.basename(file_path)}")
    result = manager.process_ocr(file_path)
    
    if result['status'] == 'success':
        print(f"  ✅ OCR successful - file will be reindexed")
        success_count += 1
    elif result['status'] == 'skipped':
        print(f"  ⏭️  Skipped - {result['reason']}")
    else:
        print(f"  ❌ OCR failed: {result.get('error', 'Unknown error')}")
        failed_count += 1

print(f"\n📊 Summary:")
print(f"  ✅ Successful: {success_count}")
print(f"  ❌ Failed: {failed_count}")

if success_count > 0:
    print(f"\n💡 The index monitor will automatically reindex the {success_count} OCR'd file(s)")
EOF

echo -e "\n${GREEN}✅ OCR processing complete${NC}"