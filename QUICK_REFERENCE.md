# Quick Reference - Spiritual Library MCP Server

## Common Commands After Reorganization

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
# Start web monitor
source venv_mcp/bin/activate
python -m personal_doc_library.monitoring.monitor_web_enhanced
# Open http://localhost:8888
```

### Testing
```bash
# Test search functionality
source venv_mcp/bin/activate
python tests/test_search_simple.py
```

### Selective Indexing
```bash
source venv_mcp/bin/activate

# Ensure package imports work when running from the repo
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

# Index specific files
python -m personal_doc_library.indexing.index_specific "book name pattern"

# Force re-index
python -m personal_doc_library.indexing.index_specific "book name" --force

# List matching files only
python -m personal_doc_library.indexing.index_specific "pattern" --list-only
```

## File Locations

### Core Components
- **MCP Server**: `src/personal_doc_library/servers/mcp_complete_server.py`
- **RAG System**: `src/personal_doc_library/core/shared_rag.py`
- **Configuration**: `src/personal_doc_library/core/config.py`

### Data Directories
- **Books**: `books/` (place PDFs here)
- **Database**: `chroma_db/`
- **Logs**: `logs/`

### Claude Desktop Config
Update your `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "spiritual-library": {
      "command": "/Users/KDP/AITools/venv_mcp/bin/python",
      "args": ["-m", "personal_doc_library.servers.mcp_complete_server"],
      "env": {
        "PYTHONPATH": "/Users/KDP/AITools/src",
        "PYTHONUNBUFFERED": "1",
        "OMP_NUM_THREADS": "4"
      }
    }
  }
}
```

## Troubleshooting

### Import Errors
All Python scripts now use proper imports:
```python
from personal_doc_library.core.shared_rag import SharedRAG
from personal_doc_library.core.config import config
```

### Path Issues
- Install via `pip install personal-doc-library` to avoid manual path tweaks
- Entry points (`pdlib-mcp`, `pdlib-indexer`, `pdlib-webmonitor`, `pdlib-cli`) work from any directory
- Legacy shell scripts in `scripts/` remain available if you prefer the original workflow

### Service Installation
```bash
# Install as LaunchAgent
./scripts/install_service.sh

# Uninstall service
./scripts/uninstall_service.sh
```