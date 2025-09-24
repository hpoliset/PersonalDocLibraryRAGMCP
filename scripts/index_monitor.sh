#!/bin/bash
# Start the background index monitor

echo "🔮 Personal Document Library Index Monitor"
echo "=================================="
echo ""

# Check if already running
if pgrep -f "python.*personal_doc_library.indexing.index_monitor" > /dev/null; then
    echo "❌ Index monitor is already running!"
    echo "   Use ./stop_monitor.sh to stop it first."
    exit 1
fi

# Get the script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate virtual environment with full path
if [ -d "$PROJECT_ROOT/venv_mcp" ]; then
    echo "📌 Activating ARM64 virtual environment..."
    source "$PROJECT_ROOT/venv_mcp/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found at $PROJECT_ROOT/venv_mcp"
    echo "   Please run ./install_interactive_nonservicemode.sh first."
    exit 1
fi

# Check dependencies
if ! python -c "import watchdog" 2>/dev/null; then
    echo "📌 Installing watchdog dependency..."
    pip install watchdog
fi

# Set environment variables for proper path resolution
# Use existing environment variable or default to local books directory
export PERSONAL_LIBRARY_DOC_PATH="${PERSONAL_LIBRARY_DOC_PATH:-$PROJECT_ROOT/books}"
export PERSONAL_LIBRARY_DB_PATH="${PERSONAL_LIBRARY_DB_PATH:-$PROJECT_ROOT/chroma_db}"
if [[ -z "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$PROJECT_ROOT/src"
else
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
fi

# Change to project root directory
cd "$PROJECT_ROOT"

# Start monitor
echo "📌 Starting index monitor..."
echo "   Monitor will watch for changes in $PERSONAL_LIBRARY_DOC_PATH"
echo "   Press Ctrl+C to stop"
echo ""
python -m personal_doc_library.indexing.index_monitor
