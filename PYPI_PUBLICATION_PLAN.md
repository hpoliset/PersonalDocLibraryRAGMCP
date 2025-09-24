# PyPI Publication Plan for Personal Document Library MCP Server

## Current Status
The package is almost ready for PyPI publication with proper Python package structure and most metadata in place.

## Prerequisites Checklist

### ✅ Already Complete:
- [x] Modern pyproject.toml configuration
- [x] Proper package structure (src/personal_doc_library/)
- [x] CLI entry points defined
- [x] Dependencies listed
- [x] MIT License file
- [x] README.md documentation

### ❌ Missing Requirements:
- [ ] Unique package name verification
- [ ] Version management strategy
- [ ] Complete author information with email
- [ ] Project URLs in pyproject.toml
- [ ] Build artifacts (dist/ directory)
- [ ] PyPI account and API token
- [ ] MANIFEST.in for non-Python files
- [ ] Test coverage on Python 3.10, 3.11, 3.12

## Phase 1: Package Metadata & Configuration

### 1.1 Update pyproject.toml
Add the following sections:

```toml
[project.urls]
Homepage = "https://github.com/hpoliset/PersonalDocLibraryRAGMCP"
Documentation = "https://github.com/hpoliset/PersonalDocLibraryRAGMCP#readme"
Issues = "https://github.com/hpoliset/PersonalDocLibraryRAGMCP/issues"
Repository = "https://github.com/hpoliset/PersonalDocLibraryRAGMCP"

[project]
authors = [
  { name = "Your Name", email = "your.email@example.com" }
]
```

### 1.2 Choose Unique Package Name
Check availability on PyPI:
```bash
pip search personal-doc-library  # May not work
# Or visit: https://pypi.org/project/personal-doc-library/
```

Alternative names if taken:
- `personal-library-mcp`
- `doclib-mcp-server`
- `personal-rag-mcp`
- `mcp-document-library`

### 1.3 Create MANIFEST.in
Include non-Python files:
```
include LICENSE
include README.md
include requirements.txt
recursive-include scripts *.sh
recursive-include config *.json.template
recursive-include docs *.md *.html
exclude logs/*
exclude books/*
exclude chroma_db/*
exclude venv_mcp/*
```

## Phase 2: Build & Test

### 2.1 Install Build Tools
```bash
python -m pip install --upgrade pip
python -m pip install --upgrade build twine
```

### 2.2 Build Distribution
```bash
# Clean any previous builds
rm -rf dist/ build/ *.egg-info

# Build both wheel and source distribution
python -m build

# This creates:
# dist/personal_doc_library-0.1.0-py3-none-any.whl
# dist/personal_doc_library-0.1.0.tar.gz
```

### 2.3 Verify Package Contents
```bash
# Check wheel contents
unzip -l dist/personal_doc_library-0.1.0-py3-none-any.whl

# Check for issues
python -m twine check dist/*
```

### 2.4 Test Local Installation
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install from wheel
pip install dist/personal_doc_library-0.1.0-py3-none-any.whl

# Test CLI commands
pdlib-cli --help
pdlib-mcp --version

# Clean up
deactivate
rm -rf test_env
```

## Phase 3: TestPyPI Upload (Recommended First Step)

### 3.1 Create TestPyPI Account
1. Go to https://test.pypi.org/account/register/
2. Create account and verify email
3. Generate API token at https://test.pypi.org/manage/account/token/

### 3.2 Configure Authentication
Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = <your-pypi-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-test-pypi-token>
```

### 3.3 Upload to TestPyPI
```bash
python -m twine upload --repository testpypi dist/*
```

### 3.4 Test Installation from TestPyPI
```bash
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    personal-doc-library
```

## Phase 4: Production PyPI Upload

### 4.1 Create PyPI Account
1. Go to https://pypi.org/account/register/
2. Create account and verify email
3. Enable 2FA (recommended)
4. Generate API token at https://pypi.org/manage/account/token/

### 4.2 Upload to PyPI
```bash
python -m twine upload dist/*
```

### 4.3 Verify Installation
```bash
# With pip
pip install personal-doc-library

# With uv
uv pip install personal-doc-library

# With pipx for CLI tools
pipx install personal-doc-library
```

## Phase 5: Post-Publication

### 5.1 Create GitHub Release
1. Tag the release:
```bash
git tag -a v0.1.0 -m "Initial PyPI release"
git push origin v0.1.0
```

2. Create release on GitHub with changelog

### 5.2 Update Documentation
- Add PyPI badge to README:
```markdown
[![PyPI version](https://badge.fury.io/py/personal-doc-library.svg)](https://pypi.org/project/personal-doc-library/)
[![Python versions](https://img.shields.io/pypi/pyversions/personal-doc-library.svg)](https://pypi.org/project/personal-doc-library/)
```

- Update installation instructions:
```markdown
## Installation

### From PyPI
```bash
pip install personal-doc-library
```

### With optional dependencies
```bash
pip install personal-doc-library[document-processing,services]
```
```

### 5.3 Version Management
For future releases:
1. Update version in `pyproject.toml`
2. Tag git commit
3. Build and upload

Consider using:
- `bump2version` for version management
- GitHub Actions for automated releases
- Semantic versioning (MAJOR.MINOR.PATCH)

## Phase 6: Automation (Optional but Recommended)

### 6.1 GitHub Actions Workflow
Create `.github/workflows/publish.yml`:
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### 6.2 Testing Workflow
Create `.github/workflows/test.yml` for automated testing on push

## Troubleshooting

### Common Issues:

1. **Name already taken**: Choose alternative name
2. **Missing dependencies**: Ensure all deps are in pyproject.toml
3. **Import errors**: Check package structure and __init__.py files
4. **Authentication fails**: Verify API token and .pypirc
5. **Build fails**: Check for syntax errors in pyproject.toml

### Testing Commands:
```bash
# Validate package
python -m build --sdist
python -m twine check dist/*

# Test imports
python -c "from personal_doc_library import __version__"
python -c "from personal_doc_library.servers.mcp_complete_server import main"
```

## Timeline Estimate

- Phase 1: 30 minutes (configuration updates)
- Phase 2: 30 minutes (build and local test)
- Phase 3: 1 hour (TestPyPI setup and testing)
- Phase 4: 30 minutes (Production upload)
- Phase 5: 30 minutes (Documentation updates)
- Phase 6: 2 hours (CI/CD setup - optional)

**Total: 2.5-4.5 hours**

## Next Steps

1. ✅ Review this plan
2. ⏳ Update package metadata in pyproject.toml
3. ⏳ Create MANIFEST.in
4. ⏳ Build package
5. ⏳ Test on TestPyPI
6. ⏳ Publish to PyPI

---
*Last updated: 2025-01-24*