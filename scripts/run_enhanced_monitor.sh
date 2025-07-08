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
export SPIRITUAL_LIBRARY_BOOKS_PATH="/Users/KDP/Library/Mobile Documents/com~apple~CloudDocs/Documents/Books"
export SPIRITUAL_LIBRARY_DB_PATH="$(pwd)/chroma_db"
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Run the enhanced monitor
python src/monitoring/monitor_web_enhanced.py