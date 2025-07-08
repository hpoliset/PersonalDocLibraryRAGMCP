#!/bin/bash
# Script to view MCP server logs in real-time

echo "📋 MCP Server Log Viewer"
echo "========================"
echo ""

# Log file location
LOG_FILE="$HOME/Library/Logs/Claude/mcp-server-spiritual-library.log"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo ""
    echo "The MCP server logs are created when Claude Desktop runs the server."
    echo "Make sure Claude Desktop is configured to use the spiritual library."
    exit 1
fi

# Display log file info
echo "📁 Log file: $LOG_FILE"
echo "📏 Size: $(ls -lh "$LOG_FILE" | awk '{print $5}')"
echo "🕐 Modified: $(ls -la "$LOG_FILE" | awk '{print $6, $7, $8}')"
echo ""

# Parse command line arguments
FOLLOW=false
FILTER=""
LINES=50

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -g|--grep)
            FILTER="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -f, --follow      Follow log in real-time (like tail -f)"
            echo "  -n, --lines NUM   Show last NUM lines (default: 50)"
            echo "  -g, --grep TERM   Filter logs by search term"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Show last 50 lines"
            echo "  $0 -f                 # Follow log in real-time"
            echo "  $0 -n 100            # Show last 100 lines"
            echo "  $0 -g 'search'       # Show lines containing 'search'"
            echo "  $0 -f -g 'ERROR'     # Follow log, show only errors"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h for help"
            exit 1
            ;;
    esac
done

# Build the command
if [ "$FOLLOW" = true ]; then
    echo "📡 Following log (Ctrl+C to stop)..."
    echo "─────────────────────────────────────"
    if [ -n "$FILTER" ]; then
        tail -f "$LOG_FILE" | grep --color=auto "$FILTER"
    else
        tail -f "$LOG_FILE"
    fi
else
    echo "📜 Showing last $LINES lines"
    if [ -n "$FILTER" ]; then
        echo "🔍 Filtered by: '$FILTER'"
    fi
    echo "─────────────────────────────────────"
    if [ -n "$FILTER" ]; then
        tail -n "$LINES" "$LOG_FILE" | grep --color=auto "$FILTER"
    else
        tail -n "$LINES" "$LOG_FILE"
    fi
fi