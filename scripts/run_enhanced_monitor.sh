#!/bin/bash
# Run the enhanced web monitor for Spiritual Library

echo "🔮 Starting Enhanced Spiritual Library Web Monitor..."
echo "📌 Open http://localhost:8888 in your browser"
echo ""

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
    echo "   Please run ./quick_start.sh first."
    exit 1
fi

# Set environment variables for proper path resolution
# Use existing environment variable or default to local books directory
export SPIRITUAL_LIBRARY_BOOKS_PATH="${SPIRITUAL_LIBRARY_BOOKS_PATH:-$PROJECT_ROOT/books}"
export SPIRITUAL_LIBRARY_DB_PATH="${SPIRITUAL_LIBRARY_DB_PATH:-$PROJECT_ROOT/chroma_db}"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Change to project root directory
cd "$PROJECT_ROOT"

# Run the enhanced monitor
echo "📌 Starting Enhanced Web Monitor..."
echo "   Open your browser to: http://localhost:8888"
echo "   Press Ctrl+C to stop"
echo ""
python src/monitoring/monitor_web_enhanced.py