# Quick Reference - Ragdex (RAG Document Indexer for MCP)

## Package Installation

### Install from PyPI
```bash
# Using uv (recommended)
uv venv ~/ragdex_env
cd ~/ragdex_env
uv pip install ragdex

# Or using pip
pip install ragdex

# With optional extras
pip install ragdex[document-processing,services]
```

### Install from Source (Development)
```bash
# Clone and install in editable mode
git clone https://github.com/hpoliset/DocumentIndexerMCP
cd DocumentIndexerMCP
pip install -e .

# With optional extras
pip install -e ".[document-processing,services]"
```

## Command-Line Tools (After Installation)

### Main CLI Commands
```bash
# Configuration and setup
ragdex --help                       # Show all commands
ragdex ensure-dirs                  # Create necessary directories
ragdex config                       # View configuration

# Service launchers
ragdex-mcp                          # Start MCP server
ragdex-index                        # Start background indexer
ragdex-web                          # Start web dashboard (localhost:8888)

# Utilities
ragdex index-status                 # Check indexing progress
ragdex find-unindexed               # Find unindexed documents
ragdex manage-failed                 # Manage failed documents
ragdex config                       # Display detailed config
```

## Traditional Scripts (Alternative)

### Starting the Server
```bash
# Run MCP server (from project root)
./scripts/run.sh

# Index only
./scripts/run.sh --index-only

# Index with retry
./scripts/run.sh --index-only --retry
```

### Background Monitoring
```bash
# Start background monitor
./scripts/index_monitor.sh

# Stop monitor
./scripts/stop_monitor.sh

# Check service status
./scripts/service_status.sh
```

### Web Interface
```bash
# Using package command
ragdex-web

# Or traditional method (if using source)
./scripts/start_web_monitor.sh

# Access at http://localhost:8888
```

### Service Installation
```bash
# Install as LaunchAgent
./scripts/install_service.sh
./scripts/install_webmonitor_service.sh

# Uninstall services
./scripts/uninstall_service.sh
./scripts/uninstall_webmonitor_service.sh

# Check status
./scripts/service_status.sh
./scripts/webmonitor_service_status.sh
```

## MCP Protocol Features

### Tools (17 Available)
```
Search & Discovery:
- search                  # Semantic search with synthesis
- list_books             # List by pattern/author
- recent_books           # Find recent additions
- find_practices         # Find specific techniques

Content Extraction:
- extract_pages          # Extract specific pages
- extract_quotes         # Find notable quotes
- summarize_book         # Generate AI summaries

Analysis & Synthesis:
- compare_perspectives   # Compare across sources
- question_answer        # Direct Q&A
- daily_reading          # Suggested passages

System Management:
- library_stats          # Library statistics
- index_status           # Indexing progress
- refresh_cache          # Refresh search cache
- warmup                 # Initialize RAG system
- find_unindexed         # Find unindexed docs
- reindex_book           # Force reindex
- clear_failed           # Clear failed list
```

### Prompts (5 Templates)
```
- analyze_theme          # Theme analysis
- compare_authors        # Author comparison
- extract_practices      # Extract techniques
- research_topic         # Deep research
- daily_wisdom           # Daily wisdom
```

### Resources (4 Dynamic)
```
- library://stats        # Current statistics
- library://recent       # Recent additions
- library://search-tips  # Usage examples
- library://config       # Configuration
```

## Testing

### Test MCP Features
```bash
# Test protocol implementation
python test_mcp_features.py

# Test resources functionality
python test_resources.py

# Test search functionality
python tests/test_search_simple.py
```

### Manual Testing
```bash
# Using venv directly
venv_mcp/bin/python -m personal_doc_library.servers.mcp_complete_server

# Test specific modules
venv_mcp/bin/python -c "
from personal_doc_library.core.shared_rag import SharedRAG
rag = SharedRAG()
print(f'Books: {rag.get_book_count()}')
"
```

## File Locations

### Source Code (New Package Structure)
- **Package**: `src/personal_doc_library/`
- **MCP Server**: `src/personal_doc_library/servers/mcp_complete_server.py`
- **RAG System**: `src/personal_doc_library/core/shared_rag.py`
- **Configuration**: `src/personal_doc_library/core/config.py`
- **CLI**: `src/personal_doc_library/cli.py`

### Data Directories
- **Books**: `books/` or `$PERSONAL_LIBRARY_DOC_PATH`
- **Database**: `chroma_db/` or `$PERSONAL_LIBRARY_DB_PATH`
- **Logs**: `logs/` or `$PERSONAL_LIBRARY_LOGS_PATH`

### Configuration Files
- **Package Config**: `pyproject.toml`
- **Dependencies**: `requirements.txt`
- **Claude Config**: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Claude Desktop Configuration

Update your `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ragdex": {
      "command": "/Users/YOUR_USERNAME/ragdex_env/bin/ragdex-mcp",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "CHROMA_TELEMETRY": "false",
        "PERSONAL_LIBRARY_DOC_PATH": "/path/to/books",
        "PERSONAL_LIBRARY_DB_PATH": "/path/to/database",
        "PERSONAL_LIBRARY_LOGS_PATH": "/path/to/logs"
      }
    }
  }
}
```

## Environment Variables

```bash
# Set document paths
export PERSONAL_LIBRARY_DOC_PATH="/path/to/books"
export PERSONAL_LIBRARY_DB_PATH="/path/to/database"
export PERSONAL_LIBRARY_LOGS_PATH="/path/to/logs"

# Disable telemetry
export CHROMA_TELEMETRY=false
export TOKENIZERS_PARALLELISM=false
export ANONYMIZED_TELEMETRY=false
```

## Troubleshooting

### Import Errors
```bash
# Ensure package is installed
pip install -e .

# Or set PYTHONPATH manually
export PYTHONPATH="/path/to/DocumentIndexerMCP/src:${PYTHONPATH:-}"
```

### Service Issues
```bash
# Check logs
tail -f logs/index_monitor_stderr.log
tail -f logs/webmonitor_stdout.log

# View MCP logs
./scripts/view_mcp_logs.sh

# Reset services
./scripts/uninstall_service.sh
./scripts/install_service.sh
```

### Indexing Problems
```bash
# Check status
ragdex check-indexing-status

# Find unindexed
ragdex find-unindexed

# Manage failed documents
ragdex manage-failed-pdfs

# Force reindex (if using source)
./scripts/run.sh --index-only --retry
```

### Memory Issues
```bash
# Set memory limit for indexing
export INDEXING_MEMORY_LIMIT_GB=8
./scripts/run.sh --index-only --retry
```

## Common Workflows

### Initial Setup
```bash
pip install ragdex
ragdex ensure-dirs
ragdex config
ragdex-mcp  # Start server
```

### Daily Use
```bash
# Option 1: Package commands
ragdex-web &        # Start web dashboard
ragdex-index &      # Start indexer
ragdex-mcp          # Run MCP server

# Option 2: Services (macOS)
# Download and run service installer
curl -O https://raw.githubusercontent.com/hpoliset/DocumentIndexerMCP/main/install_ragdex_services.sh
chmod +x install_ragdex_services.sh
./install_ragdex_services.sh
# Services run automatically

# Option 3: Manual scripts (if using source)
./scripts/index_monitor.sh &
./scripts/start_web_monitor.sh &
./scripts/run.sh
```

### Development
```bash
# Edit code
vim src/personal_doc_library/servers/mcp_complete_server.py

# Test changes
python test_mcp_features.py

# Restart Claude Desktop to apply changes
```