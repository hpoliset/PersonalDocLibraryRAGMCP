#!/bin/bash

# Start Web Monitor Script for Spiritual Library MCP Server

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔮 Starting Spiritual Library Web Monitor"
echo "========================================="
echo ""

# Check if already running
if pgrep -f monitor_web_enhanced > /dev/null; then
    echo -e "${YELLOW}⚠️  Web monitor is already running${NC}"
    echo "   Stop it first with: ./scripts/stop_web_monitor.sh"
    exit 1
fi

# Check virtual environment
if [ ! -d "$PROJECT_ROOT/venv_mcp" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "   Please run ./setup.sh first"
    exit 1
fi

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT"
export SPIRITUAL_LIBRARY_BOOKS_PATH="${SPIRITUAL_LIBRARY_BOOKS_PATH:-$PROJECT_ROOT/books}"
export SPIRITUAL_LIBRARY_DB_PATH="${SPIRITUAL_LIBRARY_DB_PATH:-$PROJECT_ROOT/chroma_db}"

# Create logs directory if needed
mkdir -p "$PROJECT_ROOT/logs"

# Start the web monitor
echo "📌 Starting web monitor..."
nohup "$PROJECT_ROOT/venv_mcp/bin/python" "$PROJECT_ROOT/src/monitoring/monitor_web_enhanced.py" \
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