#!/bin/bash

# Start Web Monitor Script for Personal Document Library MCP Server

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Use Python directly from virtual environment
PYTHON_CMD="$PROJECT_ROOT/venv_mcp/bin/python"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔮 Starting Personal Document Library Web Monitor"
echo "========================================="
echo ""

# Check if already running
if pgrep -f monitor_web_enhanced > /dev/null; then
    echo -e "${YELLOW}⚠️  Web monitor is already running${NC}"
    echo "   Stop it first with: ./scripts/stop_web_monitor.sh"
    exit 1
fi

# Check Python exists
if [ ! -f "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ Python not found at $PYTHON_CMD!${NC}"
    echo "   Please run ./serviceInstall.sh first"
    exit 1
fi

# Set environment variables
if [[ -z "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$PROJECT_ROOT/src"
else
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
fi
export PERSONAL_LIBRARY_DOC_PATH="${PERSONAL_LIBRARY_DOC_PATH:-$PROJECT_ROOT/books}"
export PERSONAL_LIBRARY_DB_PATH="${PERSONAL_LIBRARY_DB_PATH:-$PROJECT_ROOT/chroma_db}"

# Create logs directory if needed
mkdir -p "$PROJECT_ROOT/logs"

# Start the web monitor
echo "📌 Starting web monitor with Python 3.12..."
nohup "$PYTHON_CMD" -m personal_doc_library.monitoring.monitor_web_enhanced \
    > "$PROJECT_ROOT/logs/webmonitor_stdout.log" 2>&1 &

PID=$!
echo "   Started with PID: $PID"

# Wait a moment and check if it's running
sleep 2
if ps -p $PID > /dev/null; then
    echo -e "${GREEN}✅ Web monitor is running${NC}"
    echo ""
    echo "📊 Access the dashboard at: http://localhost:8888"
    echo "📝 View logs: tail -f $PROJECT_ROOT/logs/webmonitor_stdout.log"
    echo "🛑 Stop monitor: ./scripts/stop_web_monitor.sh"
else
    echo -e "${RED}❌ Web monitor failed to start${NC}"
    echo "   Check logs: tail $PROJECT_ROOT/logs/webmonitor_stdout.log"
    exit 1
fi