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
python src/monitoring/monitor_web_enhanced.py
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

# Index specific files
python src/indexing/index_specific.py "book name pattern"

# Force re-index
python src/indexing/index_specific.py "book name" --force

# List matching files only
python src/indexing/index_specific.py "pattern" --list-only
```

## File Locations

### Core Components
- **MCP Server**: `src/servers/mcp_complete_server.py`
- **RAG System**: `src/core/shared_rag.py`
- **Configuration**: `src/core/config.py`

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
      "args": ["/Users/KDP/AITools/src/servers/mcp_complete_server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "OMP_NUM_THREADS": "4",
        "OLLAMA_NUM_PARALLEL": "2",
        "OLLAMA_MAX_LOADED_MODELS": "1",
        "OLLAMA_KEEP_ALIVE": "5m"
      }
    }
  }
}
```

## Troubleshooting

### Import Errors
All Python scripts now use proper imports:
```python
from src.core.shared_rag import SharedRAG
from src.core.config import config
```

### Path Issues
- Always run scripts from the project root directory
- Shell scripts in `scripts/` automatically handle paths
- Python modules add the project root to sys.path

### Service Installation
```bash
# Install as LaunchAgent
./scripts/install_service.sh

# Uninstall service
./scripts/uninstall_service.sh
```