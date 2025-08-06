#!/bin/bash

# Service wrapper script for Web Monitor
# This script is called by LaunchAgent to start the web monitor with proper environment

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set up environment
export PYTHONPATH="$PROJECT_ROOT"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Use environment variables if set, otherwise use defaults
export SPIRITUAL_LIBRARY_BOOKS_PATH="${SPIRITUAL_LIBRARY_BOOKS_PATH:-$PROJECT_ROOT/books}"
export SPIRITUAL_LIBRARY_DB_PATH="${SPIRITUAL_LIBRARY_DB_PATH:-$PROJECT_ROOT/chroma_db}"
export SPIRITUAL_LIBRARY_LOGS_PATH="${SPIRITUAL_LIBRARY_LOGS_PATH:-$PROJECT_ROOT/logs}"

# Log startup
echo "[$(date)] Starting Web Monitor Service" >> "$PROJECT_ROOT/logs/webmonitor_service.log"
echo "[$(date)] PYTHONPATH: $PYTHONPATH" >> "$PROJECT_ROOT/logs/webmonitor_service.log"
echo "[$(date)] Books Path: $SPIRITUAL_LIBRARY_BOOKS_PATH" >> "$PROJECT_ROOT/logs/webmonitor_service.log"

# Change to project directory
cd "$PROJECT_ROOT"

# Start the web monitor
exec "$PROJECT_ROOT/venv_mcp/bin/python" "$PROJECT_ROOT/src/monitoring/monitor_web_enhanced.py"