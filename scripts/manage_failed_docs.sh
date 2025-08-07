#!/bin/bash

# Script to manage failed documents list
# Provides commands to view, add, remove, and clear failed documents

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FAILED_DOCS_FILE="$PROJECT_ROOT/chroma_db/failed_pdfs.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command
COMMAND="${1:-list}"

case "$COMMAND" in
    list)
        echo -e "${BLUE}📋 Failed Documents List${NC}"
        echo ""
        if [ -f "$FAILED_DOCS_FILE" ]; then
            if [ -s "$FAILED_DOCS_FILE" ]; then
                python3 -c "
import json
import os
from datetime import datetime

with open('$FAILED_DOCS_FILE', 'r') as f:
    failed = json.load(f)
    
if not failed:
    print('No failed documents.')
else:
    print(f'Total failed documents: {len(failed)}')
    print('')
    for path, info in failed.items():
        basename = os.path.basename(path)
        error = info.get('error', 'Unknown error')
        print(f'  • {basename}')
        print(f'    Path: {path}')
        print(f'    Error: {error}')
        if 'attempted_at' in info:
            print(f'    Last attempt: {info[\"attempted_at\"]}')
        print('')
"
            else
                echo "No failed documents."
            fi
        else
            echo "Failed documents file not found."
        fi
        ;;
        
    add)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please provide a file path to add${NC}"
            echo "Usage: $0 add <file_path> [error_message]"
            exit 1
        fi
        
        FILE_PATH="$2"
        ERROR_MSG="${3:-Manual skip}"
        
        echo -e "${YELLOW}Adding to failed list: $FILE_PATH${NC}"
        
        python3 -c "
import json
import os
from datetime import datetime

failed_file = '$FAILED_DOCS_FILE'
file_path = '$FILE_PATH'
error_msg = '$ERROR_MSG'

# Load existing failed docs
if os.path.exists(failed_file):
    with open(failed_file, 'r') as f:
        try:
            failed = json.load(f)
        except:
            failed = {}
else:
    failed = {}

# Add new entry
failed[file_path] = {
    'error': error_msg,
    'cleaned': False,
    'attempted_at': datetime.now().isoformat()
}

# Save back
os.makedirs(os.path.dirname(failed_file), exist_ok=True)
with open(failed_file, 'w') as f:
    json.dump(failed, f, indent=2)

print(f'✅ Added {os.path.basename(file_path)} to failed list')
"
        ;;
        
    remove)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please provide a file path to remove${NC}"
            echo "Usage: $0 remove <file_path>"
            exit 1
        fi
        
        FILE_PATH="$2"
        
        echo -e "${YELLOW}Removing from failed list: $FILE_PATH${NC}"
        
        python3 -c "
import json
import os

failed_file = '$FAILED_DOCS_FILE'
file_path = '$FILE_PATH'

if not os.path.exists(failed_file):
    print('❌ Failed documents file not found')
    exit(1)

with open(failed_file, 'r') as f:
    failed = json.load(f)

if file_path in failed:
    del failed[file_path]
    with open(failed_file, 'w') as f:
        json.dump(failed, f, indent=2)
    print(f'✅ Removed {os.path.basename(file_path)} from failed list')
else:
    # Try to find partial match
    matches = [k for k in failed.keys() if file_path in k or os.path.basename(file_path) == os.path.basename(k)]
    if matches:
        for match in matches:
            del failed[match]
            print(f'✅ Removed {os.path.basename(match)} from failed list')
        with open(failed_file, 'w') as f:
            json.dump(failed, f, indent=2)
    else:
        print('⚠️  File not found in failed list')
"
        ;;
        
    clear)
        echo -e "${YELLOW}⚠️  This will clear all failed documents from the list${NC}"
        read -p "Are you sure? [y/N]: " response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "{}" > "$FAILED_DOCS_FILE"
            echo -e "${GREEN}✅ Failed documents list cleared${NC}"
        else
            echo "Cancelled."
        fi
        ;;
        
    retry)
        echo -e "${BLUE}🔄 Clearing failed list to retry all documents${NC}"
        echo "{}" > "$FAILED_DOCS_FILE"
        echo -e "${GREEN}✅ Failed list cleared. Run indexing to retry all documents.${NC}"
        echo ""
        echo "To start indexing, run:"
        echo "  ./scripts/run.sh --index-only"
        ;;
        
    *)
        echo -e "${BLUE}Failed Documents Manager${NC}"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  list              Show all failed documents (default)"
        echo "  add <path> [msg]  Add a document to failed list"
        echo "  remove <path>     Remove a document from failed list"
        echo "  clear             Clear all failed documents (with confirmation)"
        echo "  retry             Clear list to retry all documents"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 add 'books/large_file.pdf' 'Too large to process'"
        echo "  $0 remove 'books/large_file.pdf'"
        echo "  $0 clear"
        echo "  $0 retry"
        ;;
esac