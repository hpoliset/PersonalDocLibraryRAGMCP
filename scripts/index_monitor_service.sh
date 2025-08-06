#!/bin/bash
#
# Service wrapper for Spiritual Library Index Monitor
# This script is designed to be run by LaunchAgent and provides proper
# environment setup and signal handling for the Python indexer.
#

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set up environment variables if not already set
export SPIRITUAL_LIBRARY_BOOKS_PATH="${SPIRITUAL_LIBRARY_BOOKS_PATH:-$PROJECT_ROOT/books}"
export SPIRITUAL_LIBRARY_DB_PATH="${SPIRITUAL_LIBRARY_DB_PATH:-$PROJECT_ROOT/chroma_db}"

# Set up logging
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

SERVICE_LOG="$LOG_DIR/index_monitor_service.log"
SERVICE_PID_FILE="/tmp/spiritual_library_index_monitor_service.pid"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SERVICE_LOG"
}

# Function to handle shutdown signals
cleanup() {
    log "Service received shutdown signal"
    
    # When using exec, this process becomes the Python process
    # So we just need to clean up and exit gracefully
    rm -f "$SERVICE_PID_FILE" 2>/dev/null || true
    
    log "Service shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT SIGQUIT

# Function to check if virtual environment exists
check_venv() {
    local venv_python="$PROJECT_ROOT/venv_mcp/bin/python"
    if [[ ! -f "$venv_python" ]]; then
        log "ERROR: Virtual environment not found at $venv_python"
        log "Please run setup-script.sh first"
        exit 1
    fi
    echo "$venv_python"
}

# Function to validate environment
validate_environment() {
    log "Validating environment..."
    log "Project root: $PROJECT_ROOT"
    log "Books directory: $SPIRITUAL_LIBRARY_BOOKS_PATH"
    log "Database directory: $SPIRITUAL_LIBRARY_DB_PATH"
    
    # Check if books directory exists
    if [[ ! -d "$SPIRITUAL_LIBRARY_BOOKS_PATH" ]]; then
        log "WARNING: Books directory does not exist: $SPIRITUAL_LIBRARY_BOOKS_PATH"
    else
        # Count documents in books directory (with timeout for LaunchAgent)
        local doc_count
        doc_count=$(gtimeout 10 find "$SPIRITUAL_LIBRARY_BOOKS_PATH" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.epub" \) 2>/dev/null | wc -l || echo "0")
        log "Found $doc_count documents in books directory"
    fi
    
    # Ensure database directory exists
    mkdir -p "$SPIRITUAL_LIBRARY_DB_PATH"
    log "Environment validation complete"
}

# Main service function
run_service() {
    local venv_python
    venv_python=$(check_venv)
    
    validate_environment
    
    log "Starting Spiritual Library Index Monitor Service"
    log "Using Python: $venv_python"
    
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    # Start the Python indexer in service mode
    local python_script="$PROJECT_ROOT/src/indexing/index_monitor.py"
    
    # Execute Python process with full permission inheritance
    # Use exec to replace this shell process so Python inherits all permissions
    log "Executing Python indexer with full permissions"
    
    # Store our PID for the health check
    echo "$$" > "$SERVICE_PID_FILE"
    
    # Use exec to replace the shell with Python, inheriting all permissions
    exec "$venv_python" "$python_script" --service \
        --books-dir "$SPIRITUAL_LIBRARY_BOOKS_PATH" \
        --db-dir "$SPIRITUAL_LIBRARY_DB_PATH"
}

# Health check function
health_check() {
    if [[ -f "$SERVICE_PID_FILE" ]]; then
        local python_pid
        python_pid=$(cat "$SERVICE_PID_FILE" 2>/dev/null || echo "")
        
        if [[ -n "$python_pid" && "$python_pid" =~ ^[0-9]+$ ]]; then
            if kill -0 "$python_pid" 2>/dev/null; then
                echo "Service is running (PID: $python_pid)"
                return 0
            else
                echo "Service PID file exists but process is not running"
                rm -f "$SERVICE_PID_FILE"
                return 1
            fi
        else
            echo "Invalid PID file"
            rm -f "$SERVICE_PID_FILE"
            return 1
        fi
    else
        echo "Service is not running"
        return 1
    fi
}

# Handle command line arguments
case "${1:-run}" in
    "run")
        run_service
        ;;
    "health"|"status")
        health_check
        ;;
    "stop")
        if health_check >/dev/null 2>&1; then
            log "Stopping service..."
            cleanup
        else
            echo "Service is not running"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 [run|health|status|stop]"
        echo "  run    - Start the service (default)"
        echo "  health - Check if service is running"
        echo "  status - Alias for health"
        echo "  stop   - Stop the service"
        exit 1
        ;;
esac