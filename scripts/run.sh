#!/bin/bash
# Unified script to run the MCP server or perform indexing with optional retry/monitoring

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔮 Personal Document Library MCP Server"
echo "==============================="
echo ""

# Parse arguments
INDEX_ONLY=false
WITH_RETRY=false
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --index-only)
            INDEX_ONLY=true
            shift
            ;;
        --retry)
            WITH_RETRY=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            HELP=true
            shift
            ;;
    esac
done

# Show help
if [ "$HELP" = true ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  (no args)       Start MCP server (default)"
    echo "  --index-only    Run indexing only (no server)"
    echo "  --retry         Enable auto-retry with memory monitoring"
    echo "  --help, -h      Show this help"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                           # Start MCP server"
    echo "  $0 --index-only              # Simple indexing"
    echo "  $0 --index-only --retry      # Robust indexing with retries"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  INDEXING_MEMORY_LIMIT_GB     Memory limit in GB (default: 16)"
    exit 0
fi

# Check if we're in the right directory
if [ ! -f "src/servers/mcp_complete_server.py" ]; then
    echo "❌ Error: src/servers/mcp_complete_server.py not found!"
    echo "   Please run this script from the AITools directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv_mcp" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "   Please run ./setup-script.sh first."
    exit 1
fi

# Change to project root directory
cd "$PROJECT_ROOT"

# Activate virtual environment
echo "📌 Activating virtual environment..."
source "$PROJECT_ROOT/venv_mcp/bin/activate"

# Set Python command
PYTHON_CMD="$PROJECT_ROOT/venv_mcp/bin/python"

# Note: Ollama is no longer required - using direct RAG results

if [ "$INDEX_ONLY" = true ]; then
    if [ "$WITH_RETRY" = true ]; then
        # Robust indexing with retry and memory monitoring
        echo ""
        echo "📌 Running robust indexing with auto-retry..."
        echo "   Memory limit: ${INDEXING_MEMORY_LIMIT_GB:-16}GB"
        echo "   Max retries: 10"
        echo ""
        
        # Maximum number of retries
        MAX_RETRIES=10
        RETRY_COUNT=0
        
        # Function to run indexing
        run_indexing() {
            echo "📌 Starting indexing attempt #$((RETRY_COUNT + 1))..."
            
            "$PYTHON_CMD" -c "
import os
import sys
import signal
import psutil
from datetime import datetime
from src.core.shared_rag import SharedRAG

# Monitor memory usage
def check_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    
    # Get memory limit from environment or use conservative default
    memory_limit_gb = int(os.environ.get('INDEXING_MEMORY_LIMIT_GB', 12))
    memory_limit_mb = memory_limit_gb * 1024
    
    if memory_mb > memory_limit_mb:
        print(f'⚠️  High memory usage: {memory_mb:.0f}MB (limit: {memory_limit_mb:.0f}MB)')
        return False
    
    # Show memory usage for monitoring
    usage_percent = (memory_mb / memory_limit_mb) * 100
    print(f'💾 Memory usage: {memory_mb:.0f}MB ({usage_percent:.1f}% of {memory_limit_gb}GB limit)')
    return True

# Set up signal handler for graceful shutdown
def signal_handler(signum, frame):
    print('\\n⚠️  Received interrupt signal, saving progress...')
    sys.exit(1)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

try:
    rag = SharedRAG()
    pdfs = rag.find_new_or_modified_pdfs()
    
    if pdfs:
        print(f'Found {len(pdfs)} PDFs to index')
        for i, (filepath, rel_path) in enumerate(pdfs):
            print(f'\\n[{i+1}/{len(pdfs)}] Indexing: {rel_path}')
            
            # Check memory before processing
            if not check_memory():
                print(f'⚠️  Skipping {rel_path} due to memory constraints')
                # Mark as skipped
                rag.book_index[rel_path] = {
                    'hash': 'SKIPPED_MEMORY_LIMIT',
                    'chunks': 0,
                    'pages': 0,
                    'indexed_at': datetime.now().isoformat(),
                    'note': 'Skipped due to memory constraints'
                }
                rag.save_book_index()
                continue
            
            # Process with timeout
            success = rag.process_pdf_with_timeout(filepath, rel_path, timeout_minutes=15)
            if not success:
                print(f'⚠️  Failed to index {rel_path}, will retry in next run')
        
        print('\\n✅ Indexing batch complete!')
    else:
        print('All PDFs are up to date.')
        sys.exit(0)
        
except Exception as e:
    print(f'\\n❌ Error during indexing: {e}')
    sys.exit(1)
"
            return $?
        }
        
        # Main retry loop
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            run_indexing
            EXIT_CODE=$?
            
            if [ $EXIT_CODE -eq 0 ]; then
                echo "✅ Indexing completed successfully!"
                exit 0
            elif [ $EXIT_CODE -eq 130 ] || [ $EXIT_CODE -eq 143 ]; then
                echo "⚠️  Indexing interrupted by user"
                exit $EXIT_CODE
            else
                RETRY_COUNT=$((RETRY_COUNT + 1))
                
                if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                    echo ""
                    echo "⚠️  Indexing failed with exit code $EXIT_CODE"
                    echo "🔄 Retrying in 10 seconds... (Attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
                    sleep 10
                else
                    echo "❌ Maximum retries reached. Indexing failed."
                    exit 1
                fi
            fi
        done
    else
        # Simple indexing (original behavior)
        echo ""
        echo "📌 Running simple indexing..."
        echo "   This will index any new or modified documents (PDFs, Word docs, EPUBs)"
        echo ""
        "$PYTHON_CMD" -c "
import os
from src.core.shared_rag import SharedRAG

# Use environment variables or defaults
books_path = os.getenv('PERSONAL_LIBRARY_DOC_PATH')
db_path = os.getenv('PERSONAL_LIBRARY_DB_PATH')

if books_path:
    print(f'Using books directory: {books_path}')
if db_path:
    print(f'Using database directory: {db_path}')

rag = SharedRAG(books_path, db_path)
documents = rag.find_new_or_modified_documents()
if documents:
    print(f'Found {len(documents)} documents to index')
    for filepath, rel_path in documents:
        print(f'Indexing: {rel_path}')
        rag.process_document_with_timeout(filepath, rel_path)
    print('Indexing complete!')
else:
    print('All documents are up to date.')
"
    fi
else
    # Run the MCP server
    echo ""
    echo "📌 Starting Complete MCP server..."
    echo "   This server communicates with Claude Desktop via MCP protocol"
    echo "   New books will be indexed automatically on first use"
    echo "   Press Ctrl+C to stop"
    echo ""
    python src/servers/mcp_complete_server.py
fi