#!/bin/bash

# Install ragdex services from PyPI version
# This script installs both the indexer and web monitor as LaunchAgent services

set -e

echo "🚀 Ragdex Service Installer"
echo "==========================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse command line arguments
NON_INTERACTIVE=false
CUSTOM_DOCS_PATH=""
CUSTOM_DB_PATH=""
CUSTOM_LOGS_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --non-interactive)
            NON_INTERACTIVE=true
            shift
            ;;
        --docs-path)
            CUSTOM_DOCS_PATH="$2"
            shift 2
            ;;
        --db-path)
            CUSTOM_DB_PATH="$2"
            shift 2
            ;;
        --logs-path)
            CUSTOM_LOGS_PATH="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --non-interactive       Run without prompts (use env vars or defaults)"
            echo "  --docs-path PATH        Specify documents directory"
            echo "  --db-path PATH          Specify database directory"
            echo "  --logs-path PATH        Specify logs directory"
            echo "  --help                  Show this help message"
            echo ""
            echo "Environment variables (if set, take precedence over prompts):"
            echo "  PERSONAL_LIBRARY_DOC_PATH"
            echo "  PERSONAL_LIBRARY_DB_PATH"
            echo "  PERSONAL_LIBRARY_LOGS_PATH"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Determine ragdex installation path
RAGDEX_ENV="$HOME/ragdex_env"

# Check multiple possible locations for ragdex installation
if command -v ragdex-mcp &> /dev/null; then
    # Found in PATH
    RAGDEX_MCP_PATH=$(which ragdex-mcp)
    RAGDEX_INDEX_PATH=$(which ragdex-index)
    RAGDEX_WEB_PATH=$(which ragdex-web)
    echo -e "${GREEN}✓${NC} Found ragdex in PATH"
elif [ -f "$RAGDEX_ENV/bin/ragdex-mcp" ]; then
    # Found in default ragdex_env
    RAGDEX_MCP_PATH="$RAGDEX_ENV/bin/ragdex-mcp"
    RAGDEX_INDEX_PATH="$RAGDEX_ENV/bin/ragdex-index"
    RAGDEX_WEB_PATH="$RAGDEX_ENV/bin/ragdex-web"
    echo -e "${GREEN}✓${NC} Found ragdex at $RAGDEX_ENV"
else
    # Look for ragdex in current directory's parent
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PARENT_DIR="$(dirname "$SCRIPT_DIR")"
    if [ -f "$PARENT_DIR/bin/ragdex-mcp" ]; then
        RAGDEX_MCP_PATH="$PARENT_DIR/bin/ragdex-mcp"
        RAGDEX_INDEX_PATH="$PARENT_DIR/bin/ragdex-index"
        RAGDEX_WEB_PATH="$PARENT_DIR/bin/ragdex-web"
        echo -e "${GREEN}✓${NC} Found ragdex at $PARENT_DIR"
    else
        echo -e "${RED}✗${NC} Ragdex not found!"
        echo "Please install ragdex first:"
        echo "  uv venv ~/ragdex_env"
        echo "  cd ~/ragdex_env"
        echo "  uv pip install ragdex"
        exit 1
    fi
fi

# Configure paths - Priority: CLI args > env vars > interactive prompts > defaults
echo ""
echo "${BLUE}📁 Configuring paths...${NC}"
echo ""

# Documents path
if [ -n "$CUSTOM_DOCS_PATH" ]; then
    DOCS_PATH="$CUSTOM_DOCS_PATH"
    echo "📚 Using documents path from command line: $DOCS_PATH"
elif [ -n "$PERSONAL_LIBRARY_DOC_PATH" ]; then
    DOCS_PATH="$PERSONAL_LIBRARY_DOC_PATH"
    echo "📚 Using documents path from environment: $DOCS_PATH"
elif [ "$NON_INTERACTIVE" = true ]; then
    DOCS_PATH="$HOME/Documents/Library"
    echo "📚 Using default documents path: $DOCS_PATH"
else
    echo "📚 Where should your documents be stored?"
    echo -e "   ${YELLOW}Default: $HOME/Documents/Library${NC}"
    read -p "   Enter path (or press Enter for default): " user_docs_path
    DOCS_PATH="${user_docs_path:-$HOME/Documents/Library}"
fi

# Database path
if [ -n "$CUSTOM_DB_PATH" ]; then
    DB_PATH="$CUSTOM_DB_PATH"
    echo "💾 Using database path from command line: $DB_PATH"
elif [ -n "$PERSONAL_LIBRARY_DB_PATH" ]; then
    DB_PATH="$PERSONAL_LIBRARY_DB_PATH"
    echo "💾 Using database path from environment: $DB_PATH"
elif [ "$NON_INTERACTIVE" = true ]; then
    DB_PATH="$HOME/.ragdex/chroma_db"
    echo "💾 Using default database path: $DB_PATH"
else
    echo ""
    echo "💾 Where should the vector database be stored?"
    echo -e "   ${YELLOW}Default: $HOME/.ragdex/chroma_db${NC}"
    read -p "   Enter path (or press Enter for default): " user_db_path
    DB_PATH="${user_db_path:-$HOME/.ragdex/chroma_db}"
fi

# Logs path
if [ -n "$CUSTOM_LOGS_PATH" ]; then
    LOGS_PATH="$CUSTOM_LOGS_PATH"
    echo "📝 Using logs path from command line: $LOGS_PATH"
elif [ -n "$PERSONAL_LIBRARY_LOGS_PATH" ]; then
    LOGS_PATH="$PERSONAL_LIBRARY_LOGS_PATH"
    echo "📝 Using logs path from environment: $LOGS_PATH"
elif [ "$NON_INTERACTIVE" = true ]; then
    LOGS_PATH="$HOME/.ragdex/logs"
    echo "📝 Using default logs path: $LOGS_PATH"
else
    echo ""
    echo "📝 Where should logs be stored?"
    echo -e "   ${YELLOW}Default: $HOME/.ragdex/logs${NC}"
    read -p "   Enter path (or press Enter for default): " user_logs_path
    LOGS_PATH="${user_logs_path:-$HOME/.ragdex/logs}"
fi

# Expand paths
DOCS_PATH="${DOCS_PATH/#\~/$HOME}"
DB_PATH="${DB_PATH/#\~/$HOME}"
LOGS_PATH="${LOGS_PATH/#\~/$HOME}"

# Show configuration summary
echo ""
echo "${BLUE}📋 Configuration Summary:${NC}"
echo "   Documents: $DOCS_PATH"
echo "   Database:  $DB_PATH"
echo "   Logs:      $LOGS_PATH"
echo ""

# Confirm installation
if [ "$NON_INTERACTIVE" = false ]; then
    read -p "Proceed with installation? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

# Create service plists
echo ""
echo "📝 Creating service configurations..."

# Service 1: Background Indexer
INDEX_PLIST="$HOME/Library/LaunchAgents/com.ragdex.indexer.plist"
cat > "$INDEX_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ragdex.indexer</string>

    <key>ProgramArguments</key>
    <array>
        <string>$RAGDEX_INDEX_PATH</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PERSONAL_LIBRARY_DOC_PATH</key>
        <string>$DOCS_PATH</string>
        <key>PERSONAL_LIBRARY_DB_PATH</key>
        <string>$DB_PATH</string>
        <key>PERSONAL_LIBRARY_LOGS_PATH</key>
        <string>$LOGS_PATH</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
        <key>CHROMA_TELEMETRY</key>
        <string>false</string>
    </dict>

    <key>StandardOutPath</key>
    <string>$LOGS_PATH/ragdex_indexer_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$LOGS_PATH/ragdex_indexer_stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>ProcessType</key>
    <string>Background</string>

    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
EOF

echo -e "${GREEN}✓${NC} Created indexer service configuration"

# Service 2: Web Monitor
WEB_PLIST="$HOME/Library/LaunchAgents/com.ragdex.webmonitor.plist"
cat > "$WEB_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ragdex.webmonitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>$RAGDEX_WEB_PATH</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PERSONAL_LIBRARY_DOC_PATH</key>
        <string>$DOCS_PATH</string>
        <key>PERSONAL_LIBRARY_DB_PATH</key>
        <string>$DB_PATH</string>
        <key>PERSONAL_LIBRARY_LOGS_PATH</key>
        <string>$LOGS_PATH</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
        <key>CHROMA_TELEMETRY</key>
        <string>false</string>
    </dict>

    <key>StandardOutPath</key>
    <string>$LOGS_PATH/ragdex_web_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$LOGS_PATH/ragdex_web_stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

echo -e "${GREEN}✓${NC} Created web monitor service configuration"

# Create directories if needed
echo ""
echo "📂 Creating directories..."
mkdir -p "$DOCS_PATH"
mkdir -p "$DB_PATH"
mkdir -p "$LOGS_PATH"
echo -e "${GREEN}✓${NC} Directories created"

# Load services
echo ""
echo "🔧 Installing services..."

# Unload if already loaded
launchctl unload "$INDEX_PLIST" 2>/dev/null || true
launchctl unload "$WEB_PLIST" 2>/dev/null || true

# Load services
launchctl load "$INDEX_PLIST"
echo -e "${GREEN}✓${NC} Indexer service installed"

launchctl load "$WEB_PLIST"
echo -e "${GREEN}✓${NC} Web monitor service installed"

# Check status
echo ""
echo "📊 Service Status:"
echo ""

if launchctl list | grep -q com.ragdex.indexer; then
    echo -e "${GREEN}✓${NC} Indexer service is running"
else
    echo -e "${RED}✗${NC} Indexer service failed to start"
fi

if launchctl list | grep -q com.ragdex.webmonitor; then
    echo -e "${GREEN}✓${NC} Web monitor service is running"
    echo ""
    echo "🌐 Web interface available at: ${YELLOW}http://localhost:8888${NC}"
else
    echo -e "${RED}✗${NC} Web monitor service failed to start"
fi

# Save configuration for future reference
CONFIG_FILE="$HOME/.ragdex/service_config"
mkdir -p "$HOME/.ragdex"
cat > "$CONFIG_FILE" << EOF
# Ragdex service configuration
# Generated on $(date)
export PERSONAL_LIBRARY_DOC_PATH="$DOCS_PATH"
export PERSONAL_LIBRARY_DB_PATH="$DB_PATH"
export PERSONAL_LIBRARY_LOGS_PATH="$LOGS_PATH"
EOF
echo -e "${GREEN}✓${NC} Configuration saved to $CONFIG_FILE"

echo ""
echo "📝 Log files:"
echo "   Indexer: $LOGS_PATH/ragdex_indexer_*.log"
echo "   Web: $LOGS_PATH/ragdex_web_*.log"
echo ""
echo "🎯 Service Management:"
echo "   Status: launchctl list | grep ragdex"
echo "   Stop: launchctl unload ~/Library/LaunchAgents/com.ragdex.*.plist"
echo "   Start: launchctl load ~/Library/LaunchAgents/com.ragdex.*.plist"
echo "   Logs: tail -f $LOGS_PATH/ragdex_*.log"
echo ""
echo "💡 To use these paths in other sessions, run:"
echo "   source $CONFIG_FILE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🤖 ${BLUE}Claude Desktop Configuration${NC}"
echo ""
echo "Add this to your Claude Desktop configuration file:"
echo "   ${YELLOW}~/Library/Application Support/Claude/claude_desktop_config.json${NC}"
echo ""
echo "${GREEN}────────────────────────────────────────────────────${NC}"
cat << EOF
{
  "mcpServers": {
    "ragdex": {
      "command": "$RAGDEX_MCP_PATH",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "CHROMA_TELEMETRY": "false",
        "PERSONAL_LIBRARY_DOC_PATH": "$DOCS_PATH",
        "PERSONAL_LIBRARY_DB_PATH": "$DB_PATH",
        "PERSONAL_LIBRARY_LOGS_PATH": "$LOGS_PATH"
      }
    }
  }
}
EOF
echo "${GREEN}────────────────────────────────────────────────────${NC}"
echo ""
echo "📌 Note: If you have other MCP servers configured, merge this"
echo "   'ragdex' section into your existing mcpServers object."
echo ""
echo "After updating the config, restart Claude Desktop for changes to take effect."
echo ""
echo "✅ Ragdex services installed successfully!"