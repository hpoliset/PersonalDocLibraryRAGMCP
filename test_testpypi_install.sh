#!/bin/bash

# Test installation from TestPyPI using uv
# Usage: ./test_testpypi_install.sh

set -e

echo "🧪 Testing TestPyPI Installation with uv"
echo "======================================="

# Clean up any previous test
echo "🧹 Cleaning up previous test environment..."
rm -rf /tmp/testpypi_test

# Create test directory
echo "📁 Creating test environment..."
cd /tmp
uv venv testpypi_test
cd testpypi_test

echo ""
echo "📦 Installing ragdex from TestPyPI..."
echo ""

# Install from TestPyPI with dependencies from PyPI
uv pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    ragdex

echo ""
echo "✅ Installation complete!"
echo ""
echo "🧪 Running tests..."
echo ""

# Test 1: Check version
echo "1. Testing package import and version..."
./bin/python -c "
from personal_doc_library import __version__
print(f'   ✓ Package version: {__version__}')
"

# Test 2: Check CLI commands exist
echo ""
echo "2. Testing CLI commands..."
for cmd in ragdex ragdex-mcp ragdex-index ragdex-web; do
    if [ -f "./bin/$cmd" ]; then
        echo "   ✓ $cmd found"
    else
        echo "   ✗ $cmd NOT found"
    fi
done

# Test 3: Test CLI help (basic functionality)
echo ""
echo "3. Testing CLI help..."
if ./bin/ragdex --help > /dev/null 2>&1; then
    echo "   ✓ ragdex --help works"
else
    echo "   ✗ ragdex --help failed"
fi

# Test 4: Check core imports
echo ""
echo "4. Testing core module imports..."
./bin/python -c "
try:
    from personal_doc_library.core.config import config
    print('   ✓ Core config imports successfully')
except ImportError as e:
    print(f'   ✗ Core config import failed: {e}')

try:
    from personal_doc_library.servers.mcp_complete_server import main
    print('   ✓ MCP server imports successfully')
except ImportError as e:
    print(f'   ✗ MCP server import failed: {e}')
"

echo ""
echo "📊 Test Summary"
echo "==============="
echo ""
echo "If all tests passed (✓), your package is ready for production PyPI!"
echo ""
echo "Next steps:"
echo "1. Upload to production PyPI: ./upload_to_pypi.sh"
echo "2. Test with: uv pip install ragdex"
echo ""
echo "Test environment location: /tmp/testpypi_test"
echo "To manually test: cd /tmp/testpypi_test && source bin/activate"