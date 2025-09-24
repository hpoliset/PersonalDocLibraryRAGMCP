#!/bin/bash

# Script to update or create Claude Desktop configuration for ragdex

set -e

echo "🤖 Ragdex Claude Desktop Configuration Helper"
echo "============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Claude config file location
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Load saved ragdex configuration if it exists
CONFIG_FILE="$HOME/.ragdex/service_config"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    echo -e "${GREEN}✓${NC} Loaded ragdex configuration from $CONFIG_FILE"
else
    # Use environment variables or defaults
    PERSONAL_LIBRARY_DOC_PATH="${PERSONAL_LIBRARY_DOC_PATH:-$HOME/Documents/Library}"
    PERSONAL_LIBRARY_DB_PATH="${PERSONAL_LIBRARY_DB_PATH:-$HOME/.ragdex/chroma_db}"
    PERSONAL_LIBRARY_LOGS_PATH="${PERSONAL_LIBRARY_LOGS_PATH:-$HOME/.ragdex/logs}"
fi

# Find ragdex command
if command -v ragdex-mcp &> /dev/null; then
    RAGDEX_MCP_PATH=$(which ragdex-mcp)
elif [ -f "$HOME/ragdex_env/bin/ragdex-mcp" ]; then
    RAGDEX_MCP_PATH="$HOME/ragdex_env/bin/ragdex-mcp"
elif [ -f "$HOME/ragdex/bin/ragdex-mcp" ]; then
    RAGDEX_MCP_PATH="$HOME/ragdex/bin/ragdex-mcp"
else
    echo -e "${RED}✗${NC} ragdex-mcp not found! Please install ragdex first."
    exit 1
fi

echo ""
echo "📋 Configuration:"
echo "   Ragdex command: $RAGDEX_MCP_PATH"
echo "   Documents: $PERSONAL_LIBRARY_DOC_PATH"
echo "   Database: $PERSONAL_LIBRARY_DB_PATH"
echo "   Logs: $PERSONAL_LIBRARY_LOGS_PATH"
echo ""

# Generate the ragdex configuration
RAGDEX_CONFIG=$(cat << EOF
{
  "command": "$RAGDEX_MCP_PATH",
  "env": {
    "PYTHONUNBUFFERED": "1",
    "CHROMA_TELEMETRY": "false",
    "PERSONAL_LIBRARY_DOC_PATH": "$PERSONAL_LIBRARY_DOC_PATH",
    "PERSONAL_LIBRARY_DB_PATH": "$PERSONAL_LIBRARY_DB_PATH",
    "PERSONAL_LIBRARY_LOGS_PATH": "$PERSONAL_LIBRARY_LOGS_PATH"
  }
}
EOF
)

# Check if Claude config exists
if [ -f "$CLAUDE_CONFIG" ]; then
    echo "📄 Found existing Claude configuration"

    # Check if it already has ragdex configured
    if grep -q '"ragdex"' "$CLAUDE_CONFIG"; then
        echo -e "${YELLOW}⚠️  Ragdex is already configured in Claude Desktop${NC}"
        echo ""
        read -p "Do you want to update the existing configuration? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Configuration not updated."
            exit 0
        fi

        # Backup existing config
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✓${NC} Backed up existing configuration"

        # Update existing ragdex configuration using Python
        python3 -c "
import json
import sys

with open('$CLAUDE_CONFIG', 'r') as f:
    config = json.load(f)

config['mcpServers']['ragdex'] = $RAGDEX_CONFIG

with open('$CLAUDE_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)
"
        echo -e "${GREEN}✓${NC} Updated ragdex configuration in Claude Desktop"
    else
        # Add ragdex to existing config
        echo "Adding ragdex to existing configuration..."

        # Backup existing config
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✓${NC} Backed up existing configuration"

        # Add ragdex configuration using Python
        python3 -c "
import json
import sys

with open('$CLAUDE_CONFIG', 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['ragdex'] = $RAGDEX_CONFIG

with open('$CLAUDE_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)
"
        echo -e "${GREEN}✓${NC} Added ragdex to Claude Desktop configuration"
    fi
else
    echo "📄 Creating new Claude configuration..."

    # Create config directory if it doesn't exist
    mkdir -p "$(dirname "$CLAUDE_CONFIG")"

    # Create new config with ragdex
    cat > "$CLAUDE_CONFIG" << EOF
{
  "mcpServers": {
    "ragdex": $RAGDEX_CONFIG
  }
}
EOF
    echo -e "${GREEN}✓${NC} Created Claude Desktop configuration with ragdex"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Claude Desktop configuration updated successfully!"
echo ""
echo "📌 Next steps:"
echo "   1. Restart Claude Desktop for changes to take effect"
echo "   2. Look for 'ragdex' in Claude's MCP server list"
echo "   3. Try asking Claude about your document library!"
echo ""
echo "💡 Example queries:"
echo "   - 'Search for information about [topic] in my library'"
echo "   - 'What books do I have about [subject]?'"
echo "   - 'Compare perspectives on [topic] across my books'"