#!/bin/bash

# TestPyPI Upload Script for ragdex
# Usage: ./upload_to_testpypi.sh

set -e

echo "🚀 TestPyPI Upload Script for ragdex"
echo "================================================"

# Check if distribution files exist
if [ ! -f "dist/ragdex-0.1.0-py3-none-any.whl" ] || [ ! -f "dist/ragdex-0.1.0.tar.gz" ]; then
    echo "❌ Distribution files not found in dist/"
    echo "Run: venv_mcp/bin/python -m build"
    exit 1
fi

# Check for token
if [ -z "$TESTPYPI_TOKEN" ]; then
    echo ""
    echo "⚠️  TestPyPI token not found in environment"
    echo ""
    echo "To set your token:"
    echo "  export TESTPYPI_TOKEN='your-token-here'"
    echo ""
    echo "Or create ~/.pypirc with:"
    echo "[testpypi]"
    echo "repository = https://test.pypi.org/legacy/"
    echo "username = __token__"
    echo "password = your-token-here"
    echo ""
    read -p "Enter your TestPyPI token (or press Ctrl+C to cancel): " TESTPYPI_TOKEN
    if [ -z "$TESTPYPI_TOKEN" ]; then
        echo "❌ Token required"
        exit 1
    fi
fi

# Install/upgrade twine if needed
echo "📦 Ensuring twine is installed..."
venv_mcp/bin/pip install --quiet --upgrade twine

# Upload to TestPyPI
echo ""
echo "📤 Uploading to TestPyPI..."
echo ""

if [ -f ~/.pypirc ] && grep -q "testpypi" ~/.pypirc; then
    # Use .pypirc if configured
    venv_mcp/bin/python -m twine upload --repository testpypi dist/*
else
    # Use environment variables
    TWINE_USERNAME=__token__ TWINE_PASSWORD=$TESTPYPI_TOKEN \
    venv_mcp/bin/python -m twine upload \
        --repository-url https://test.pypi.org/legacy/ \
        dist/*
fi

echo ""
echo "✅ Upload complete!"
echo ""
echo "📋 Next steps:"
echo "1. View your package at:"
echo "   https://test.pypi.org/project/ragdex/"
echo ""
echo "2. Test installation with uv:"
echo "   uv pip install \\"
echo "     --index-url https://test.pypi.org/simple/ \\"
echo "     --extra-index-url https://pypi.org/simple/ \\"
echo "     ragdex"
echo ""
echo "3. Once verified, upload to production PyPI:"
echo "   ./upload_to_pypi.sh"