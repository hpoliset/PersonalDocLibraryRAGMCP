#!/bin/bash

# Generate configuration files from templates
# This script replaces placeholders in template files with actual values

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root (parent of scripts directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔮 Generating Configuration Files"
echo "================================="
echo ""

# Detect user and environment
USER_HOME="$HOME"
USER_NAME="$(whoami)"
PYTHON_PATH="${PROJECT_ROOT}/venv_mcp/bin/python"

# Default paths (can be overridden by environment variables)
BOOKS_PATH="${PERSONAL_LIBRARY_DOC_PATH:-${PROJECT_ROOT}/books}"
DB_PATH="${PERSONAL_LIBRARY_DB_PATH:-${PROJECT_ROOT}/chroma_db}"
LOGS_PATH="${PERSONAL_LIBRARY_LOGS_PATH:-${PROJECT_ROOT}/logs}"

echo "📍 Environment Detection:"
echo "   User: $USER_NAME"
echo "   Home: $USER_HOME"
echo "   Project Root: $PROJECT_ROOT"
echo ""

echo "📚 Directory Configuration:"
echo "   Books: $BOOKS_PATH"
echo "   Database: $DB_PATH"
echo "   Logs: $LOGS_PATH"
echo ""

# Function to generate a config file from template
generate_config() {
    local template_file="$1"
    local output_file="$2"
    local description="$3"
    
    if [ ! -f "$template_file" ]; then
        echo -e "${YELLOW}⚠️  Template not found: $template_file${NC}"
        return 1
    fi
    
    echo -n "📝 Generating $description... "
    
    # Use sed to replace placeholders
    sed -e "s|{{PROJECT_ROOT}}|${PROJECT_ROOT}|g" \
        -e "s|{{USER_HOME}}|${USER_HOME}|g" \
        -e "s|{{USER_NAME}}|${USER_NAME}|g" \
        -e "s|{{PYTHON_PATH}}|${PYTHON_PATH}|g" \
        -e "s|{{BOOKS_PATH}}|${BOOKS_PATH}|g" \
        -e "s|{{DB_PATH}}|${DB_PATH}|g" \
        -e "s|{{LOGS_PATH}}|${LOGS_PATH}|g" \
        "$template_file" > "$output_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p "$BOOKS_PATH"
mkdir -p "$DB_PATH"  
mkdir -p "$LOGS_PATH"
mkdir -p "${PROJECT_ROOT}/config"
echo ""

# Generate configuration files
echo "🔧 Generating configuration files:"
echo ""

# Generate plist files
generate_config \
    "${PROJECT_ROOT}/config/com.personal-library.index-monitor.plist.template" \
    "${PROJECT_ROOT}/config/com.personal-library.index-monitor.plist" \
    "Index Monitor plist"

generate_config \
    "${PROJECT_ROOT}/config/com.personal-library.webmonitor.plist.template" \
    "${PROJECT_ROOT}/config/com.personal-library.webmonitor.plist" \
    "Web Monitor plist"

# Generate Claude Desktop config
if [ -f "${PROJECT_ROOT}/config/claude_desktop_config.json.template.new" ]; then
    generate_config \
        "${PROJECT_ROOT}/config/claude_desktop_config.json.template.new" \
        "${PROJECT_ROOT}/config/claude_desktop_config.json" \
        "Claude Desktop config"
elif [ -f "${PROJECT_ROOT}/config/claude_desktop_config.json.template" ]; then
    generate_config \
        "${PROJECT_ROOT}/config/claude_desktop_config.json.template" \
        "${PROJECT_ROOT}/config/claude_desktop_config.json" \
        "Claude Desktop config"
fi

echo ""
echo -e "${GREEN}✅ Configuration files generated successfully!${NC}"
echo ""
echo "📋 Next Steps:"
echo "   1. Review generated configs in: ${PROJECT_ROOT}/config/"
echo "   2. Install services: ./scripts/install_service.sh"
echo "   3. Copy Claude config to: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""

# Export paths for use by other scripts
export PERSONAL_LIBRARY_DOC_PATH="$BOOKS_PATH"
export PERSONAL_LIBRARY_DB_PATH="$DB_PATH"
export PERSONAL_LIBRARY_LOGS_PATH="$LOGS_PATH"