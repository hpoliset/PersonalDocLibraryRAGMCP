<div align="center">

# 🚀 Ragdex

### Transform Your Documents & Emails into an AI-Powered Knowledge Base

[![PyPI version](https://badge.fury.io/py/ragdex.svg)](https://badge.fury.io/py/ragdex)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)
[![Downloads](https://img.shields.io/pypi/dm/ragdex.svg)](https://pypi.org/project/ragdex/)

**Ragdex** is a powerful Model Context Protocol (MCP) server that transforms your personal document library and email archives into an AI-queryable knowledge base. Built for Claude Desktop and compatible with any MCP client.

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples) • [Support](#-support)

</div>

---

## ✨ Features

### 🎯 Core Capabilities

<table>
<tr>
<td width="50%">

#### 📚 Universal Document Support
- **PDFs** with OCR for scanned documents
- **Office Files** (Word, PowerPoint, Excel)
- **E-books** (EPUB, MOBI, AZW, AZW3)
- **Plain Text** and Markdown files
- **Automatic format detection**

</td>
<td width="50%">

#### 📧 Email Intelligence (v0.2.0+)
- **Apple Mail** (EMLX) support
- **Outlook** (OLM export) support
- **Smart filtering** - Skip marketing & spam
- **Attachment processing**
- **Thread reconstruction**

</td>
</tr>
<tr>
<td width="50%">

#### 🔍 Advanced Search & RAG
- **Semantic search** with vector embeddings
- **Cross-document insights**
- **Context-aware responses**
- **17+ specialized MCP tools**
- **Real-time index updates**

</td>
<td width="50%">

#### 🎨 Beautiful Web Dashboard
- **Real-time monitoring** at `localhost:8888`
- **Indexing progress tracking**
- **Document & email statistics**
- **Failed document management**
- **Search interface with filters**

</td>
</tr>
</table>

### 🛠️ MCP Tools Available

| Tool | Description |
|------|-------------|
| 🔍 **search** | Semantic search with optional filters |
| 📊 **compare_perspectives** | Compare viewpoints across documents |
| 📈 **library_stats** | Get comprehensive statistics |
| 📖 **summarize_book** | Generate AI summaries |
| 💭 **extract_quotes** | Find relevant quotes on topics |
| ❓ **question_answer** | Direct Q&A from your library |
| 📚 **list_books** | Browse by pattern/author/directory |
| 📅 **recent_books** | Find recently indexed content |
| 🔄 **refresh_cache** | Update search cache |
| ...and 8 more! | |

### 🎯 Smart Email Filtering

Ragdex intelligently filters out noise from your email archives:

- ❌ **Auto-skips**: Marketing, promotions, shopping receipts, newsletters
- ❌ **Excludes**: Spam, junk, trash folders
- ✅ **Focuses on**: Personal communications, important discussions
- ⚙️ **Configurable**: Whitelist important senders, set date ranges

---

## 🚀 Quick Start

### Installation (30 seconds)

```bash
# Using uv (fastest)
uv venv ~/ragdex_env
uv pip install ragdex

# Or standard pip
python -m venv ~/ragdex_env
source ~/ragdex_env/bin/activate
pip install ragdex
```

### Setup Services (2 minutes)

```bash
# Download installer
curl -O https://raw.githubusercontent.com/hpoliset/DocumentIndexerMCP/main/install_ragdex_services.sh
chmod +x install_ragdex_services.sh

# Run interactive setup
./install_ragdex_services.sh

# That's it! Services are running
```

### Configure Claude Desktop

The installer will show you the exact configuration to add to Claude Desktop. Or run:

```bash
curl -O https://raw.githubusercontent.com/hpoliset/DocumentIndexerMCP/main/update_claude_config.sh
chmod +x update_claude_config.sh
./update_claude_config.sh
```

**You're done!** 🎉 Ragdex is now indexing your documents and ready to use with Claude.

---

## 📖 Documentation

### System Requirements

- **Python 3.10+** (3.10, 3.11, or 3.12)
- **macOS** or **Linux**
- **4GB RAM** for embeddings
- **Claude Desktop** or MCP client

### Configuration Options

#### Environment Variables

```bash
# Core paths
export PERSONAL_LIBRARY_DOC_PATH="/path/to/documents"
export PERSONAL_LIBRARY_DB_PATH="/path/to/database"
export PERSONAL_LIBRARY_LOGS_PATH="/path/to/logs"

# Email settings (v0.2.0+)
export PERSONAL_LIBRARY_INDEX_EMAILS=true
export PERSONAL_LIBRARY_EMAIL_SOURCES=apple_mail,outlook_local
export PERSONAL_LIBRARY_EMAIL_MAX_AGE_DAYS=365
export PERSONAL_LIBRARY_EMAIL_EXCLUDED_FOLDERS=Spam,Junk,Trash
```

### Advanced Installation

<details>
<summary>📦 Install with Optional Dependencies</summary>

```bash
# Document processing extras
pip install ragdex[document-processing]

# Service management
pip install ragdex[services]

# Everything
pip install ragdex[document-processing,services]
```

</details>

<details>
<summary>🔧 Install from Source</summary>

```bash
git clone https://github.com/hpoliset/DocumentIndexerMCP
cd DocumentIndexerMCP
pip install -e .

# With extras
pip install -e ".[document-processing,services]"
```

</details>

<details>
<summary>📋 Available CLI Commands</summary>

```bash
# Main commands
ragdex-mcp            # Start MCP server
ragdex-index          # Start background indexer
ragdex-web            # Launch web dashboard

# Management commands
ragdex --help                        # Show all commands
ragdex ensure-dirs                   # Create directories
ragdex config                        # View configuration
ragdex check-indexing-status         # Check status
ragdex find-unindexed                # Find new documents
ragdex manage-failed-pdfs            # Handle failures
```

</details>

---

## 💡 Examples

### Using with Claude Desktop

Once configured, you can ask Claude:

```
"Search my library for information about machine learning"
"Compare perspectives on climate change across my documents"
"Summarize the main themes in my recent emails"
"Find all documents mentioning Python programming"
"What meetings did I have last month?" (from emails)
```

### Programmatic Usage

```python
from ragdex import RAGSystem

# Initialize the system
rag = RAGSystem()

# Search documents
results = rag.search("artificial intelligence", max_results=5)

# Get statistics
stats = rag.get_library_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Total emails: {stats['total_emails']}")
```

---

## 🎯 Use Cases

### 📚 Personal Knowledge Management
- Build a searchable archive of your books, papers, and notes
- Never lose track of important information
- Connect ideas across different sources

### 💼 Professional Research
- Analyze technical documentation
- Compare different approaches from papers
- Extract key insights from reports

### 📧 Email Intelligence
- Search through years of communications
- Find important attachments
- Track project discussions

### 🎓 Academic Study
- Research across textbooks and papers
- Extract quotes for citations
- Compare author perspectives

---

## 🏗️ Architecture

```mermaid
graph TD
    A[Document Sources] --> B[Ragdex Indexer]
    B --> C[ChromaDB Vector Store]
    C --> D[MCP Server]
    D --> E[Claude Desktop]

    F[Email Archives] --> B
    G[Web Dashboard] --> C

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#9f9,stroke:#333,stroke-width:2px
```

### Components

- **Indexer**: Background service monitoring document changes
- **Vector Store**: ChromaDB with 768-dim embeddings
- **MCP Server**: 17 tools for document interaction
- **Web Monitor**: Real-time dashboard at localhost:8888

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and install in dev mode
git clone https://github.com/hpoliset/DocumentIndexerMCP
cd DocumentIndexerMCP
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black src/
```

---

## 📊 Stats & Performance

- **Indexing Speed**: ~100 documents/minute
- **Search Latency**: <100ms for most queries
- **Memory Usage**: ~2GB base + 2GB for embeddings
- **Storage**: ~1MB per 100 pages indexed

---

## 🐛 Troubleshooting

<details>
<summary>📝 Common Issues</summary>

**Services not starting?**
```bash
# Check service status
launchctl list | grep ragdex

# View logs
tail -f ~/ragdex/logs/ragdex_*.log
```

**Documents not indexing?**
```bash
# Check for failed documents
ragdex manage-failed-pdfs

# Verify paths
ragdex config
```

**Permission errors?**
```bash
# Ensure directories exist
ragdex ensure-dirs

# Check permissions
ls -la ~/Documents/Library
```

</details>

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - LLM framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Sentence Transformers](https://sbert.net/) - Embeddings
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification

---

## 📞 Support

- 📧 **Issues**: [GitHub Issues](https://github.com/hpoliset/DocumentIndexerMCP/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/hpoliset/DocumentIndexerMCP/discussions)
- 📖 **Wiki**: [Documentation Wiki](https://github.com/hpoliset/DocumentIndexerMCP/wiki)

---

<div align="center">
Made with ❤️ for the AI community

**[⭐ Star us on GitHub](https://github.com/hpoliset/DocumentIndexerMCP)**
</div>