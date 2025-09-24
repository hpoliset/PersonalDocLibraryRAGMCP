#!/bin/bash

# Quick local test for ragdex package

echo "🚀 Quick Ragdex Local Test"
echo "========================="
echo ""

# Test in existing environment
TEST_ENV="/tmp/ragdex_test"

if [ ! -d "$TEST_ENV" ]; then
    echo "Creating test environment..."
    cd /tmp && uv venv ragdex_test
    cd ragdex_test
    echo "Installing ragdex..."
    uv pip install /Users/hpoliset/DocumentIndexerMCP/dist/ragdex-0.1.0-py3-none-any.whl
else
    echo "Using existing test environment at $TEST_ENV"
    cd "$TEST_ENV"
fi

echo ""
echo "✅ Testing Commands:"
echo ""

# Test 1: Main CLI
echo -n "1. ragdex --help: "
if ./bin/ragdex --help >/dev/null 2>&1; then
    echo "✓ Works"
else
    echo "✗ Failed"
fi

# Test 2: MCP Server
echo -n "2. ragdex-mcp: "
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | timeout 2 ./bin/ragdex-mcp 2>/dev/null | grep -q "result" && echo "✓ Works" || echo "✗ Failed"

# Test 3: Python imports
echo -n "3. Python imports: "
./bin/python -c "
from personal_doc_library import __version__
from personal_doc_library.core.config import config
from personal_doc_library.servers.mcp_complete_server import CompleteMCPServer
print('✓ Works')
" 2>/dev/null || echo "✗ Failed"

# Test 4: List tools
echo -n "4. MCP tools count: "
./bin/python -c "
from personal_doc_library.servers.mcp_complete_server import CompleteMCPServer
server = CompleteMCPServer()
response = server.handle_list_tools()
tools = response.get('result', {}).get('tools', [])
print(f'✓ {len(tools)} tools available')
" 2>/dev/null || echo "✗ Failed"

echo ""
echo "📦 Package Info:"
./bin/python -c "
import personal_doc_library
import os
print(f'   Version: {personal_doc_library.__version__}')
print(f'   Location: {os.path.dirname(personal_doc_library.__file__)}')
"

echo ""
echo "🎯 Ready for PyPI upload!"
echo "   Next: ./upload_to_testpypi.sh"