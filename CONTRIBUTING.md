# Contributing to Spiritual Library MCP Server

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- Python 3.9+ (ARM64 version for Apple Silicon)
- Ollama with llama3.3:70b model
- Ghostscript for PDF cleaning
- Git

### Setup Development Environment
```bash
# Clone the repository
git clone <your-fork-url>
cd spiritual-library-mcp

# Create virtual environment (use ARM64 Python on Apple Silicon)
python3 -m venv venv_dev
source venv_dev/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8 mypy
```

## Project Structure

```
spiritual-library-mcp/
├── mcp_complete_server.py    # Main MCP server implementation
├── shared_rag.py            # Core RAG functionality
├── index_monitor.py         # Background indexing service
├── monitor_web_simple.py    # Web monitoring dashboard
├── clean_pdfs.py           # PDF cleaning utilities
├── scripts/
│   ├── setup-script.sh     # Initial setup
│   ├── run.sh             # Manual server runner
│   ├── index_monitor.sh   # Start background monitor
│   └── service_*.sh       # Service management
├── docs/
│   ├── README.md          # Main documentation
│   ├── CLAUDE.md          # Claude Code instructions
│   └── CHANGELOG.md       # Version history
└── tests/                 # Test suite (coming soon)
```

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Maximum line length: 100 characters

### Formatting
```bash
# Format code with black
black *.py

# Check linting
flake8 *.py

# Type checking
mypy *.py
```

### Testing
```bash
# Run tests (when available)
pytest tests/

# Test MCP server manually
python test-server-py.py

# Test specific functionality
./run.sh
```

## Contributing Process

### 1. Fork and Branch
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourusername/spiritual-library-mcp.git

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write clear, well-documented code
- Follow existing patterns and conventions
- Add tests for new functionality
- Update documentation as needed

### 3. Test Thoroughly
- Test MCP server integration with Claude Desktop
- Verify search functionality works correctly
- Test with sample PDFs in books/ directory
- Check web monitoring interface
- Ensure ARM64 compatibility (if applicable)

### 4. Submit Pull Request
- Write clear commit messages
- Include description of changes
- Reference any related issues
- Ensure all tests pass

## Areas for Contribution

### High Priority
- **Test Suite**: Comprehensive test coverage for all components
- **Error Handling**: Better error recovery and user messaging
- **Performance**: Optimization for large libraries (1000+ books)
- **Documentation**: More detailed setup guides and troubleshooting

### Medium Priority
- **Additional MCP Tools**: New tools for spiritual practice guidance
- **Alternative Embedding Models**: Support for other embedding providers
- **Export Functionality**: Export search results and syntheses
- **Configuration Management**: Better config file handling

### Low Priority
- **UI Improvements**: Enhanced web monitoring interface
- **Internationalization**: Support for non-English spiritual texts
- **Cloud Storage**: Integration with cloud storage providers
- **Mobile Interface**: Mobile-friendly monitoring dashboard

## Specific Contribution Guidelines

### Adding New MCP Tools
1. Add tool definition to `mcp_complete_server.py` in the `tools/list` response
2. Implement the handler in the `tools/call` method
3. Add proper error handling and validation
4. Update documentation in README.md
5. Test integration with Claude Desktop

Example tool structure:
```python
{
    "name": "your_tool_name",
    "description": "Clear description of what the tool does",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param1"]
    }
}
```

### Modifying RAG Functionality
- Changes to `shared_rag.py` affect both MCP server and background monitor
- Test both usage modes: MCP integration and manual operation
- Consider impact on indexing performance
- Maintain backward compatibility with existing ChromaDB collections

### Web Interface Changes
- Keep interface lightweight and responsive
- Maintain real-time updates with 2-second refresh
- Ensure mobile compatibility
- Test with various library sizes

## Bug Reports

### Before Reporting
1. Search existing issues
2. Test with latest version
3. Check troubleshooting section in README.md
4. Try with minimal test case

### Report Template
```markdown
**Bug Description**
Clear description of the issue

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.11.13]
- Architecture: [e.g., ARM64/x86_64]
- Claude Desktop version: [e.g., 0.11.6]

**Logs**
```
Relevant log entries
```
```

## Feature Requests

Feature requests are welcome! Please:
1. Check existing issues first
2. Clearly describe the use case
3. Explain how it fits with project goals
4. Consider implementation complexity
5. Offer to help implement if possible

## Code Review Process

All contributions go through code review:
1. **Automated checks**: Style, linting, basic tests
2. **Functionality review**: Does it work as intended?
3. **Design review**: Does it fit the architecture?
4. **Documentation review**: Is it properly documented?
5. **Testing review**: Are there adequate tests?

## Questions?

- Create an issue for general questions
- Use discussions for design questions
- Check existing documentation first
- Be patient and respectful

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to the Spiritual Library MCP Server!