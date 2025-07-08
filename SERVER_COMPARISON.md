# MCP Server Comparison

## mcp_complete_server.py (Primary - Recommended)
- **Full-featured** implementation using SharedRAG
- **Tools available**: 
  - `search` - Advanced search with optional AI synthesis
  - `find_practices` - Find specific spiritual practices
  - `compare_perspectives` - Compare views across sources
  - `library_stats` - Enhanced statistics
  - `index_status` - Detailed indexing status
- **Features**:
  - Automatic indexing of new PDFs on startup
  - AI synthesis of search results using Ollama
  - Lock handling to prevent conflicts
  - Integration with background monitor
  - Automatic PDF cleaning on failure
- **Dependencies**: Requires sentence-transformers, HuggingFace, Ollama

## mcp_final_server.py (Fallback)
- **Simplified** implementation with direct SQLite access
- **Tools available**:
  - `search_spiritual_library` - Basic search
  - `library_stats` - Basic statistics
- **Features**:
  - Read-only access to existing index
  - No dependencies on embeddings or LLM
  - Faster startup (no model loading)
  - Works even if Ollama is down
- **Limitations**:
  - No automatic indexing
  - No AI synthesis
  - No ability to add new books

## When to use which?

**Use mcp_complete_server.py when:**
- You want full functionality
- You're adding new books regularly
- You want AI-powered synthesis
- You have Ollama running

**Use mcp_final_server.py when:**
- You have dependency issues
- You just need basic search
- Ollama is not available
- You want faster startup

## Configuration

Update Claude Desktop settings to switch servers:
```json
{
  "mcpServers": {
    "spiritual-library": {
      "command": "/Users/KDP/AITools/venv/bin/python",
      "args": ["/Users/KDP/AITools/mcp_complete_server.py"]  // or mcp_final_server.py
    }
  }
}
```