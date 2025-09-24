# TestPyPI Upload Instructions

## Package Status ✅
- Package built successfully
- Wheel and source distributions created
- Package name `personal-doc-library` is available

## Files Ready for Upload
- `dist/personal_doc_library-0.1.0-py3-none-any.whl` (221KB)
- `dist/personal_doc_library-0.1.0.tar.gz` (80KB)

## Step 1: Create TestPyPI Account

1. Go to https://test.pypi.org/account/register/
2. Create an account with your email
3. Verify your email address
4. Enable 2FA (recommended)

## Step 2: Generate API Token

1. Go to https://test.pypi.org/manage/account/token/
2. Create a new API token with name: `personal-doc-library-upload`
3. Copy the token (starts with `pypi-...`)
4. Save it securely

## Step 3: Configure Authentication

Create or update `~/.pypirc`:

```ini
[distutils]
index-servers =
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-test-pypi-token-here>
```

Or use environment variables:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-test-pypi-token-here>
```

## Step 4: Upload to TestPyPI

Using twine:
```bash
venv_mcp/bin/python -m twine upload --repository testpypi dist/*
```

Or using uv (if it supports upload - check latest docs):
```bash
uv publish --index-url https://test.pypi.org/legacy/ dist/*
```

## Step 5: Test Installation with uv

```bash
# Create test environment
uv venv test_install
cd test_install

# Install from TestPyPI
uv pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    personal-doc-library

# Test the CLI
./bin/pdlib-cli --help
```

Note: The `--extra-index-url` is needed because dependencies are pulled from regular PyPI.

## Step 6: Verify Everything Works

```bash
# Test imports
./bin/python -c "from personal_doc_library import __version__; print(__version__)"

# Test CLI commands
./bin/pdlib-cli --help
./bin/pdlib-cli config
```

## Expected Output

After upload, you should see:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading personal_doc_library-0.1.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 221.5/221.5 kB
Uploading personal_doc_library-0.1.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 80.0/80.0 kB

View at:
https://test.pypi.org/project/personal-doc-library/0.1.0/
```

## Production PyPI Upload

Once TestPyPI works:

1. Create account at https://pypi.org
2. Generate production API token
3. Upload with:
   ```bash
   venv_mcp/bin/python -m twine upload dist/*
   ```
4. Install with uv:
   ```bash
   uv pip install personal-doc-library
   ```

## Troubleshooting

### Authentication Issues
- Ensure token starts with `pypi-`
- Check ~/.pypirc permissions (should be 600)
- Try environment variables instead

### Package Not Found After Upload
- Wait 1-2 minutes for index to update
- Check the exact package name
- Verify at https://test.pypi.org/project/personal-doc-library/

### Installation Fails
- Use `--extra-index-url` for dependencies
- Check Python version compatibility (requires >=3.10)

---
*Generated: 2025-01-24*