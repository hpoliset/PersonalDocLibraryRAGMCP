#!/bin/bash

# Service wrapper script for Web Monitor
# This script is called by LaunchAgent to start the web monitor with proper environment

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Use Python directly from virtual environment
PYTHON_CMD="$PROJECT_ROOT/venv_mcp/bin/python"

# Set up environment
if [[ -z "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$PROJECT_ROOT/src"
else
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
fi
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Use environment variables if set, otherwise use defaults
export PERSONAL_LIBRARY_DOC_PATH="${PERSONAL_LIBRARY_DOC_PATH:-$PROJECT_ROOT/books}"
export PERSONAL_LIBRARY_DB_PATH="${PERSONAL_LIBRARY_DB_PATH:-$PROJECT_ROOT/chroma_db}"
export PERSONAL_LIBRARY_LOGS_PATH="${PERSONAL_LIBRARY_LOGS_PATH:-$PROJECT_ROOT/logs}"

# Log startup
echo "[$(date)] Starting Web Monitor Service" >> "$PROJECT_ROOT/logs/webmonitor_service.log"
echo "[$(date)] PYTHONPATH: $PYTHONPATH" >> "$PROJECT_ROOT/logs/webmonitor_service.log"
echo "[$(date)] Books Path: $PERSONAL_LIBRARY_DOC_PATH" >> "$PROJECT_ROOT/logs/webmonitor_service.log"

# Change to project directory
cd "$PROJECT_ROOT"

# Start the web monitor
exec "$PYTHON_CMD" -m personal_doc_library.monitoring.monitor_web_enhanced