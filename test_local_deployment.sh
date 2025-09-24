#!/bin/bash

# Comprehensive local deployment test for ragdex
# This tests the package as if it were installed from PyPI

set -e

echo "🧪 Ragdex Local Deployment Test"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test environment location
TEST_DIR="/tmp/ragdex_local_test_$(date +%s)"

# Function to print test results
print_test() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        return 1
    fi
}

# Clean up previous test if exists
echo "📁 Setting up test environment..."
rm -rf "$TEST_DIR" 2>/dev/null || true

# Create test environment
echo "   Creating virtual environment with uv..."
cd /tmp
uv venv "$(basename $TEST_DIR)" > /dev/null 2>&1
cd "$TEST_DIR"

echo "   Installing ragdex from local wheel..."
if [ -f "/Users/hpoliset/DocumentIndexerMCP/dist/ragdex-0.1.0-py3-none-any.whl" ]; then
    uv pip install /Users/hpoliset/DocumentIndexerMCP/dist/ragdex-0.1.0-py3-none-any.whl > /dev/null 2>&1
    print_test $? "Package installed successfully"
else
    echo -e "${RED}✗${NC} Wheel file not found. Run: venv_mcp/bin/python -m build"
    exit 1
fi

echo ""
echo "🔍 Testing CLI Commands"
echo "-----------------------"

# Test 1: Check all CLI commands exist
echo ""
echo "1. Checking CLI command availability:"
for cmd in ragdex ragdex-mcp ragdex-index ragdex-web; do
    if [ -f "./bin/$cmd" ]; then
        print_test 0 "$cmd exists"
    else
        print_test 1 "$cmd missing"
    fi
done

# Test 2: Test ragdex --help
echo ""
echo "2. Testing main CLI help:"
if ./bin/ragdex --help > /dev/null 2>&1; then
    print_test 0 "ragdex --help works"
else
    print_test 1 "ragdex --help failed"
fi

# Test 3: Test config command (may have errors but should run)
echo ""
echo "3. Testing config command:"
if ./bin/ragdex config 2>&1 | grep -q "Personal Document Library"; then
    print_test 0 "ragdex config runs"
else
    print_test 1 "ragdex config failed"
fi

# Test 4: Test MCP server startup
echo ""
echo "4. Testing MCP server startup:"
timeout 1 ./bin/ragdex-mcp > /tmp/mcp_test.log 2>&1 || true
if grep -q "Starting CompleteMCPServer\|Complete MCP Server starting" /tmp/mcp_test.log; then
    print_test 0 "ragdex-mcp starts correctly"
else
    print_test 1 "ragdex-mcp failed to start"
    echo "     Debug: $(head -3 /tmp/mcp_test.log)"
fi
rm -f /tmp/mcp_test.log

echo ""
echo "🐍 Testing Python Imports"
echo "-------------------------"

# Test 5: Test core imports
echo ""
echo "5. Testing Python module imports:"
./bin/python -c "
import sys
errors = []

try:
    from personal_doc_library import __version__
    print('   ✓ Package version accessible')
except ImportError as e:
    errors.append(f'Package import failed: {e}')
    print('   ✗ Package import failed')

try:
    from personal_doc_library.core.config import config
    print('   ✓ Config module loads')
except ImportError as e:
    errors.append(f'Config import failed: {e}')
    print('   ✗ Config module failed')

try:
    from personal_doc_library.servers.mcp_complete_server import CompleteMCPServer
    print('   ✓ MCP server module loads')
except ImportError as e:
    errors.append(f'MCP server import failed: {e}')
    print('   ✗ MCP server module failed')

try:
    from personal_doc_library.core.shared_rag import SharedRAG
    print('   ✓ SharedRAG module loads')
except ImportError as e:
    errors.append(f'SharedRAG import failed: {e}')
    print('   ✗ SharedRAG module failed')

if errors:
    for error in errors:
        print(f'     Error: {error}', file=sys.stderr)
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_test 0 "All Python imports successful"
else
    print_test 1 "Some Python imports failed"
fi

echo ""
echo "📊 Testing MCP Protocol Features"
echo "--------------------------------"

# Test 6: Check MCP tools registration
echo ""
echo "6. Testing MCP tools availability:"
./bin/python -c "
from personal_doc_library.servers.mcp_complete_server import CompleteMCPServer
import json

server = CompleteMCPServer()

# Count tools
tools_response = server.handle_list_tools()
tools = tools_response.get('result', {}).get('tools', [])
print(f'   ✓ {len(tools)} MCP tools registered')

# List first 5 tools
for tool in tools[:5]:
    print(f'     - {tool[\"name\"]}')
if len(tools) > 5:
    print(f'     ... and {len(tools) - 5} more')
"

echo ""
echo "🔧 Configuration Paths"
echo "----------------------"

# Test 7: Show configuration
echo ""
echo "7. Current configuration:"
./bin/python -c "
from personal_doc_library.core.config import config
import os

print(f'   Books directory: {config.books_directory}')
print(f'   Database path: {config.database_path}')
print(f'   Logs directory: {config.logs_directory}')

# Check if directories exist
if os.path.exists(config.books_directory):
    print('   ✓ Books directory exists')
else:
    print('   ⚠️  Books directory does not exist (will be created on first use)')
"

echo ""
echo "="*50
echo ""
echo "📋 Test Summary"
echo "---------------"

# Count successes
echo ""
echo -e "${GREEN}✅ Ragdex is ready for local use!${NC}"
echo ""
echo "The package works correctly. You can now:"
echo ""
echo "1. Upload to TestPyPI for wider testing:"
echo "   ${YELLOW}./upload_to_testpypi.sh${NC}"
echo ""
echo "2. Or upload directly to production PyPI:"
echo "   ${YELLOW}./upload_to_pypi.sh${NC}"
echo ""
echo "Test environment location: $TEST_DIR"
echo "To manually test: cd $TEST_DIR && source bin/activate"
echo ""
echo "To clean up test environment:"
echo "   rm -rf $TEST_DIR"