#!/bin/bash
# Foolproof fresh indexing script
# This script will backup data, install improved indexing, and start fresh

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔄 Starting Foolproof Fresh Indexing Process"
echo "============================================"
date

# Change to project root directory
cd "$PROJECT_ROOT"

# Step 1: Stop all services
echo -e "\n📍 Step 1: Stopping all services..."
./stop_monitor.sh 2>/dev/null || true
lsof -ti:8888 | xargs kill -9 2>/dev/null || true
echo "Services stopped"

# Step 2: Backup current data
echo -e "\n📍 Step 2: Creating backup of current data..."
backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r chroma_db "$backup_dir/" 2>/dev/null || true
cp shared_rag.py "$backup_dir/" 2>/dev/null || true
echo "Backup created in $backup_dir"

# Step 3: Install improved shared_rag
echo -e "\n📍 Step 3: Installing improved indexing system..."
cp shared_rag_improved.py shared_rag.py
echo "Improved system installed"

# Step 4: Clear all existing data
echo -e "\n📍 Step 4: Clearing existing data for fresh start..."
rm -rf chroma_db
mkdir -p chroma_db
echo "Data cleared"

# Step 5: Create indexing status file
echo -e "\n📍 Step 5: Initializing status tracking..."
cat > "$PROJECT_ROOT/chroma_db/index_status.json" << EOF
{
  "status": "ready",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
  "details": {
    "message": "Ready for fresh indexing"
  }
}
EOF

# Step 6: Activate virtual environment
echo -e "\n📍 Step 6: Activating virtual environment..."
source "$PROJECT_ROOT/venv_mcp/bin/activate"

# Step 7: Start fresh indexing
echo -e "\n📍 Step 7: Starting fresh indexing..."
echo "This will index all PDFs in the books/ directory"
echo "Features of the improved system:"
echo "  ✓ Hash-based deduplication (no duplicates)"
echo "  ✓ Max 2 retry attempts per failed PDF"
echo "  ✓ Automatic PDF cleanup attempts"
echo "  ✓ Comprehensive error tracking"
echo "  ✓ Never gets stuck on failures"
echo ""
echo "Starting indexing in 5 seconds..."
sleep 5

# Run indexing
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from shared_rag import ImprovedSharedRAG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n🚀 Starting fresh indexing with improved system...")
rag = ImprovedSharedRAG()

# Clear any existing data
rag.clear_all_data()

# Find all PDFs
pdfs = rag.find_new_or_modified_pdfs()
print(f"\n📚 Found {len(pdfs)} PDFs to index")

# Process all PDFs
success_count = 0
failed_count = 0

for i, (filepath, rel_path) in enumerate(pdfs, 1):
    print(f"\n[{i}/{len(pdfs)}] Processing: {rel_path}")
    rag.update_status("indexing", {
        "current_file": rel_path,
        "progress": f"{i}/{len(pdfs)}",
        "success": success_count,
        "failed": failed_count
    })
    
    if rag.process_pdf(filepath, rel_path):
        success_count += 1
    else:
        failed_count += 1

# Final status
rag.update_status("idle", {
    "last_run": rag.book_index.get('last_indexed', 'Just now'),
    "indexed": success_count,
    "failed": failed_count
})

# Get final stats
stats = rag.get_stats()

print("\n✅ Indexing Complete!")
print("=" * 50)
print(f"Total books indexed: {stats['total_books']}")
print(f"Unique books: {stats['unique_books']}")
print(f"Duplicate books: {stats['duplicate_books']}")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Successful: {stats['successful_books']}")
print(f"Failed: {stats['failed_books']}")
print(f"Max retries exceeded: {stats['retry_exceeded']}")
print(f"Total size: {stats['total_size_gb']} GB")
print("=" * 50)
EOF

echo -e "\n✅ Fresh indexing complete!"
echo ""
echo "Next steps:"
echo "1. Run the web monitor: ./scripts/start_web_monitor.sh"
echo "2. View the results at http://localhost:8888"
echo ""
echo "The improved system ensures:"
echo "- No duplicate entries (hash-based deduplication)"
echo "- Failed PDFs are tracked but don't block progress"
echo "- Automatic cleanup attempts for problematic PDFs"
echo "- Clear separation of successful and failed books"