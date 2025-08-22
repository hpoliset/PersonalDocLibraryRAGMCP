#!/usr/bin/env python3
"""
Complete MCP Server for Personal Document Library
Full-featured server with search, synthesis, and optional indexing capabilities
"""

import json
import sys
import os
import logging
import select
from typing import Dict, List, Any
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.shared_rag import SharedRAG, IndexLock
from src.core.config import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stderr)
logger = logging.getLogger(__name__)

class CompleteMCPServer:
    """Complete MCP server with all features"""
    
    def __init__(self):
        # Use configuration system for paths
        self.books_directory = str(config.books_directory)
        self.db_directory = str(config.db_directory)
        self.rag = None  # Initialize lazily to avoid timeout
        
    def ensure_rag_initialized(self):
        """Initialize RAG system if not already initialized"""
        if self.rag is None:
            logger.info("Initializing SharedRAG...")
            self.rag = SharedRAG(self.books_directory, self.db_directory)
            logger.info("SharedRAG initialized successfully")
        
    def check_and_index_if_needed(self):
        """Check for new books and index if monitor isn't running"""
        self.ensure_rag_initialized()
        status = self.rag.get_status()
        
        # Check if monitor is actively indexing
        if status.get("status") == "indexing":
            logger.info("Background indexer is currently running")
            return
        
        # Check for new PDFs
        pdfs_to_index = self.rag.find_new_or_modified_pdfs()
        
        if pdfs_to_index:
            logger.info(f"Found {len(pdfs_to_index)} new/modified PDFs")
            
            # Try to acquire lock
            try:
                with self.rag.lock.acquire(blocking=False):
                    logger.info("Starting automatic indexing...")
                    
                    for i, (filepath, rel_path) in enumerate(pdfs_to_index, 1):
                        logger.info(f"Indexing {i}/{len(pdfs_to_index)}: {rel_path}")
                        self.rag.process_pdf(filepath, rel_path)
                    
                    logger.info("Indexing complete")
                    
            except IOError:
                logger.info("Another process is indexing - proceeding with current index")
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        # Check for new books on initialization
        if method == "initialize":
            # Don't check for new books during initialization to avoid timeout
            # self.check_and_index_if_needed()
            return {
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "personal-library",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "result": {
                    "tools": [
                    {
                        "name": "search",
                        "description": "Search the personal library with optional synthesis",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Max results (default 10)",
                                    "default": 10
                                },
                                "filter_type": {
                                    "type": "string",
                                    "description": "Filter by content type",
                                    "enum": ["practice", "energy_work", "philosophy", "general"]
                                },
                                "synthesize": {
                                    "type": "boolean",
                                    "description": "Generate synthesis of results",
                                    "default": False
                                },
                                "book": {
                                    "type": "string",
                                    "description": "Optional: Search within a specific book (partial title match, case-insensitive)"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "find_practices",
                        "description": "Find specific practices or techniques",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "practice_type": {
                                    "type": "string",
                                    "description": "Type of practice to find"
                                }
                            },
                            "required": ["practice_type"]
                        }
                    },
                    {
                        "name": "compare_perspectives",
                        "description": "Compare perspectives on a topic across sources",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "topic": {
                                    "type": "string",
                                    "description": "Topic to compare"
                                }
                            },
                            "required": ["topic"]
                        }
                    },
                    {
                        "name": "library_stats",
                        "description": "Get library statistics and indexing status",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "index_status",
                        "description": "Get detailed indexing status",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "summarize_book",
                        "description": "Generate an AI summary of an entire book",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "book_name": {
                                    "type": "string",
                                    "description": "Name of the book to summarize"
                                },
                                "summary_length": {
                                    "type": "string",
                                    "description": "Length of summary",
                                    "enum": ["brief", "detailed"],
                                    "default": "brief"
                                }
                            },
                            "required": ["book_name"]
                        }
                    },
                    {
                        "name": "extract_quotes",
                        "description": "Find notable quotes on a specific topic",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "topic": {
                                    "type": "string",
                                    "description": "Topic to find quotes about"
                                },
                                "max_quotes": {
                                    "type": "integer",
                                    "description": "Maximum number of quotes",
                                    "default": 10
                                }
                            },
                            "required": ["topic"]
                        }
                    },
                    {
                        "name": "daily_reading",
                        "description": "Get suggested passages for daily reading",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "theme": {
                                    "type": "string",
                                    "description": "Theme for the reading (e.g., 'love', 'meditation', 'service')"
                                },
                                "length": {
                                    "type": "string",
                                    "description": "Reading length",
                                    "enum": ["short", "medium", "long"],
                                    "default": "medium"
                                }
                            }
                        }
                    },
                    {
                        "name": "question_answer",
                        "description": "Ask a direct question and get an answer from the library",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "Your question"
                                },
                                "detail_level": {
                                    "type": "string",
                                    "description": "Level of detail in answer",
                                    "enum": ["concise", "detailed"],
                                    "default": "concise"
                                }
                            },
                            "required": ["question"]
                        }
                    },
                    {
                        "name": "refresh_cache",
                        "description": "Refresh the search cache and reload the book index",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "warmup",
                        "description": "Initialize the RAG system to prevent timeouts on first use",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "list_books", 
                        "description": "List books in the library by author, title pattern, or directory",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "pattern": {
                                    "type": "string",
                                    "description": "Search pattern to match book titles/paths (case-insensitive, supports partial matches)"
                                },
                                "author": {
                                    "type": "string", 
                                    "description": "Author name or directory to filter by"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of books to return (default: 50)",
                                    "default": 50
                                }
                            }
                        }
                    },
                    {
                        "name": "recent_books",
                        "description": "Find books added or modified within a specified time period",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "days": {
                                    "type": "integer",
                                    "description": "Number of days to look back (e.g., 1 for last 24 hours, 7 for last week)",
                                    "default": 1
                                },
                                "include_content": {
                                    "type": "boolean",
                                    "description": "Include sample content from each book",
                                    "default": False
                                }
                            }
                        }
                    },
                    {
                        "name": "extract_pages",
                        "description": "Extract specific pages from a book in the library",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "book": {
                                    "type": "string",
                                    "description": "Book name or partial title to match (case-insensitive)"
                                },
                                "pages": {
                                    "oneOf": [
                                        {
                                            "type": "integer",
                                            "description": "Single page number"
                                        },
                                        {
                                            "type": "array",
                                            "items": {"type": "integer"},
                                            "description": "List of page numbers"
                                        },
                                        {
                                            "type": "string",
                                            "pattern": "^\\d+-\\d+$",
                                            "description": "Page range (e.g., '10-15')"
                                        }
                                    ],
                                    "description": "Page(s) to extract: single page (5), list ([1,3,5]), or range ('10-15')"
                                }
                            },
                            "required": ["book", "pages"]
                        }
                    },
                    {
                        "name": "book_pages",
                        "description": "List all page numbers available in the index for a specific book",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "book": {
                                    "type": "string",
                                    "description": "Book name or partial title to match (case-insensitive)"
                                }
                            },
                            "required": ["book"]
                        }
                    }
                ]
                }
            }
        
        elif method == "resources/list":
            return {
                "result": {
                    "resources": []
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            if tool_name == "search":
                self.ensure_rag_initialized()
                query = arguments.get("query", "")
                limit = arguments.get("limit", 10)
                filter_type = arguments.get("filter_type")
                synthesize = arguments.get("synthesize", False)
                book = arguments.get("book")
                
                # If a book is specified, filter results to that book
                if book:
                    # Find matching book
                    book_lower = book.lower()
                    matching_books = []
                    
                    for book_path in self.rag.book_index.keys():
                        if book_lower in book_path.lower():
                            matching_books.append(os.path.basename(book_path))
                    
                    if not matching_books:
                        return {
                            "result": {
                                "content": [{"type": "text", "text": f"No books found matching '{book}'"}]
                            }
                        }
                    
                    # If multiple matches, use the first one
                    book_name = matching_books[0]
                    
                    # Search with book filter
                    all_results = self.rag.search(query, limit * 3, filter_type, synthesize)
                    results = [r for r in all_results if r.get('source', '').startswith(book_name)][:limit]
                else:
                    results = self.rag.search(query, limit, filter_type, synthesize)
                
                # Enhanced formatting for article writing
                text = f"Found {len(results)} relevant passages for query: '{query}'\n\n"
                
                for i, result in enumerate(results, 1):
                    text += f"━━━ Result {i} ━━━\n"
                    text += f"📖 Source: {result['source']}\n"
                    text += f"📄 Page: {result['page']}\n"
                    text += f"🏷️  Type: {result['type']}\n"
                    text += f"📊 Relevance: {result['relevance_score']:.3f}\n\n"
                    
                    # Provide more content for article writing (up to 800 chars)
                    content = result['content']
                    if len(content) > 800:
                        text += f"{content[:800]}...\n\n"
                    else:
                        text += f"{content}\n\n"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "find_practices":
                self.ensure_rag_initialized()
                practice_type = arguments.get("practice_type", "")
                query = f"practice {practice_type} technique method"
                
                results = self.rag.search(query, k=15, filter_type="practice", synthesize=False)
                
                if results:
                    text = f"Found {len(results)} practices related to '{practice_type}':\n\n"
                    
                    # Group by source for better organization
                    by_source = {}
                    for result in results:
                        source = result['source']
                        if source not in by_source:
                            by_source[source] = []
                        by_source[source].append(result)
                    
                    for source, practices in by_source.items():
                        text += f"\n📚 {source}\n"
                        text += "─" * 40 + "\n"
                        for practice in practices:
                            text += f"• Page {practice['page']}: {practice['content'][:400]}...\n\n"
                else:
                    text = "No specific practices found for that query."
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "compare_perspectives":
                self.ensure_rag_initialized()
                topic = arguments.get("topic", "")
                query = f"{topic} perspective view understanding"
                
                results = self.rag.search(query, k=20, synthesize=False)
                
                if results:
                    text = f"Comparing perspectives on '{topic}' across {len(results)} passages:\n\n"
                    
                    # Group by type/tradition for comparison
                    by_type = {}
                    for result in results:
                        type_cat = result['type']
                        if type_cat not in by_type:
                            by_type[type_cat] = []
                        by_type[type_cat].append(result)
                    
                    for type_cat, perspectives in by_type.items():
                        text += f"\n🔸 {type_cat.title()} Perspective:\n"
                        text += "━" * 50 + "\n"
                        
                        # Show top 3 from each category
                        for i, persp in enumerate(perspectives[:3], 1):
                            text += f"\n{i}. {persp['source']} (p.{persp['page']}):\n"
                            text += f"   {persp['content'][:500]}...\n"
                            text += f"   [Relevance: {persp['relevance_score']:.3f}]\n"
                else:
                    text = "Not enough material found to compare perspectives."
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "library_stats":
                self.ensure_rag_initialized()
                stats = self.rag.get_stats()
                
                text = f"""Library Statistics:
- Total Books: {stats['total_books']}
- Total Chunks: {stats['total_chunks']:,}
- Failed Books: {stats['failed_books']}
- Auto-cleaned Books: {stats['cleaned_books']}

Content Categories:"""
                
                for category, count in stats.get('categories', {}).items():
                    text += f"\n- {category.title()}: {count:,} chunks"
                
                # Add indexing status
                status = stats.get('indexing_status', {})
                if status.get('status') == 'indexing':
                    text += f"\n\nCurrently indexing: {status.get('details', {}).get('current_file', 'Unknown')}"
                elif status.get('status') == 'idle' and 'last_run' in status.get('details', {}):
                    text += f"\n\nLast indexed: {status['details']['last_run']}"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "index_status":
                self.ensure_rag_initialized()
                status = self.rag.get_status()
                
                if status.get('status') == 'indexing':
                    details = status.get('details', {})
                    text = f"""Indexing Status: ACTIVE
Current File: {details.get('current_file', 'Unknown')}
Progress: {details.get('progress', 'Unknown')}
Success: {details.get('success', 0)}
Failed: {details.get('failed', 0)}"""
                else:
                    text = "Indexing Status: IDLE"
                    if 'details' in status and 'last_run' in status['details']:
                        text += f"\nLast Run: {status['details']['last_run']}"
                        if 'indexed' in status['details']:
                            text += f"\nIndexed: {status['details']['indexed']} files"
                        if 'failed' in status['details']:
                            text += f"\nFailed: {status['details']['failed']} files"
                
                # Check for new files
                self.ensure_rag_initialized()
                pdfs_to_index = self.rag.find_new_or_modified_pdfs()
                if pdfs_to_index:
                    text += f"\n\nNew/Modified PDFs waiting: {len(pdfs_to_index)}"
                    text += "\nRun any search to trigger indexing, or use background monitor."
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "summarize_book":
                self.ensure_rag_initialized()
                book_name = arguments.get("book_name", "")
                summary_length = arguments.get("summary_length", "brief")
                
                # Search for content from this specific book
                results = self.rag.search(
                    query=f"book:{book_name}",
                    k=50 if summary_length == "detailed" else 20,
                    synthesize=False
                )
                
                # Filter results to only include the specified book
                book_results = [r for r in results if book_name.lower() in r.get('source', '').lower()]
                
                if not book_results:
                    text = f"No content found for book: {book_name}"
                else:
                    # Return direct passages for Claude to summarize
                    text = f"Content from '{book_name}' ({len(book_results)} passages found):\n\n"
                    
                    # Determine how many passages to show based on summary length
                    max_passages = 30 if summary_length == "detailed" else 15
                    
                    for i, result in enumerate(book_results[:max_passages], 1):
                        text += f"━━━ Passage {i} (Page {result['page']}) ━━━\n"
                        text += f"🏷️  Type: {result['type']}\n"
                        text += f"📊 Relevance: {result['relevance_score']:.3f}\n\n"
                        
                        # Show more content for detailed summaries
                        content_length = 800 if summary_length == "detailed" else 500
                        if len(result['content']) > content_length:
                            text += f"{result['content'][:content_length]}...\n\n"
                        else:
                            text += f"{result['content']}\n\n"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "extract_quotes":
                self.ensure_rag_initialized()
                topic = arguments.get("topic", "")
                max_quotes = arguments.get("max_quotes", 10)
                
                # Search for quotes about the topic
                results = self.rag.search(
                    query=f"{topic} quote saying wisdom teaching",
                    k=max_quotes * 2,  # Get extra to filter
                    synthesize=False
                )
                
                if not results:
                    text = f"No quotes found about '{topic}'"
                else:
                    # Extract meaningful quotes
                    quotes = []
                    for result in results[:max_quotes]:
                        content = result['content']
                        # Look for sentence-like structures that could be quotes
                        sentences = content.split('. ')
                        for sentence in sentences:
                            if len(sentence) > 30 and len(sentence) < 200:
                                if any(word in sentence.lower() for word in topic.lower().split()):
                                    quotes.append({
                                        'quote': sentence.strip() + '.' if not sentence.endswith('.') else sentence,
                                        'source': result['source'],
                                        'page': result['page']
                                    })
                                    break
                    
                    if quotes:
                        text = f"Quotes about '{topic}':\n\n"
                        for i, q in enumerate(quotes[:max_quotes], 1):
                            text += f"{i}. \"{q['quote']}\"\n   - {q['source']}, p.{q['page']}\n\n"
                    else:
                        text = f"No specific quotes found about '{topic}', but found {len(results)} related passages."
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "daily_reading":
                self.ensure_rag_initialized()
                theme = arguments.get("theme", "general wisdom")
                length = arguments.get("length", "medium")
                
                # Determine number of passages based on length
                num_passages = {"short": 1, "medium": 3, "long": 5}.get(length, 3)
                
                # Search for themed content
                results = self.rag.search(
                    query=f"{theme} practice daily reflection",
                    k=num_passages * 2,
                    synthesize=False
                )
                
                if not results:
                    text = f"No readings found for theme: {theme}"
                else:
                    import random
                    # Select diverse passages
                    selected = random.sample(results, min(num_passages, len(results)))
                    
                    text = f"Daily Reading - Theme: {theme.title()}\n\n"
                    for i, passage in enumerate(selected, 1):
                        text += f"Reading {i}:\n"
                        text += f"From {passage['source']} (p.{passage['page']})\n\n"
                        # Adjust content length based on reading length
                        content_length = {"short": 200, "medium": 400, "long": 600}.get(length, 400)
                        text += f"{passage['content'][:content_length]}...\n\n"
                        text += "---\n\n"
                    
                    # Add reflection prompt
                    text += f"Reflection: Consider how these teachings on {theme} apply to your practice today."
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "question_answer":
                self.ensure_rag_initialized()
                question = arguments.get("question", "")
                detail_level = arguments.get("detail_level", "concise")
                
                # Search for relevant content
                results = self.rag.search(
                    query=question,
                    k=10 if detail_level == "detailed" else 5,
                    synthesize=False
                )
                
                if results:
                    text = f"Question: {question}\n\n"
                    text += f"Found {len(results)} relevant passages:\n\n"
                    
                    # For concise mode, show top 3; for detailed, show all
                    num_results = len(results) if detail_level == "detailed" else min(3, len(results))
                    
                    for i, result in enumerate(results[:num_results], 1):
                        text += f"━━━ Passage {i} ━━━\n"
                        text += f"📖 {result['source']} (Page {result['page']})\n"
                        text += f"🏷️  Category: {result['type']}\n"
                        text += f"📊 Relevance: {result['relevance_score']:.3f}\n\n"
                        
                        # Show more content for detailed mode
                        content_length = 800 if detail_level == "detailed" else 500
                        if len(result['content']) > content_length:
                            text += f"{result['content'][:content_length]}...\n\n"
                        else:
                            text += f"{result['content']}\n\n"
                else:
                    text = f"I couldn't find a clear answer to: {question}"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "refresh_cache":
                self.ensure_rag_initialized()
                # Reload the book index
                self.rag.load_book_index()
                
                text = "✅ Cache refreshed successfully!\n\n"
                text += f"📚 Total books: {len(self.rag.book_index)}\n"
                text += f"📊 Total chunks: {sum(info.get('chunks', 0) for info in self.rag.book_index.values())}"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "warmup":
                self.ensure_rag_initialized()
                text = "✅ RAG system initialized and warmed up!\n\n"
                text += f"📚 Books indexed: {len(self.rag.book_index)}\n"
                text += f"🔍 Search ready: Yes\n"
                text += f"💾 Vector store: Loaded"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "list_books":
                self.ensure_rag_initialized()
                
                pattern = arguments.get("pattern", "")
                author = arguments.get("author", "")  
                limit = arguments.get("limit", 50)
                
                # Get all books
                all_books = list(self.rag.book_index.keys())
                matching_books = []
                
                for book_path in all_books:
                    book_name = os.path.basename(book_path)
                    book_dir = os.path.dirname(book_path)
                    
                    # Apply filters
                    if pattern and pattern.lower() not in book_path.lower():
                        continue
                    if author and author.lower() not in book_dir.lower():
                        continue
                        
                    matching_books.append((book_path, book_name, self.rag.book_index[book_path]))
                
                # Sort by name
                matching_books.sort(key=lambda x: x[1])
                
                # Apply limit
                truncated = len(matching_books) > limit
                matching_books = matching_books[:limit]
                
                if not matching_books:
                    text = "No books found matching the criteria."
                else:
                    text = "📚 Matching Books:\n\n"
                    for i, (book_path, book_name, book_info) in enumerate(matching_books, 1):
                        text += f"{i}. **{book_name}**\n"
                        text += f"   📁 Path: {book_path}\n"
                        text += f"   📄 Chunks: {book_info.get('chunks', 'Unknown')}\n"
                        if 'indexed_at' in book_info:
                            text += f"   🕐 Indexed: {book_info['indexed_at']}\n"
                        text += "\n"
                    
                    text += f"Total: {len(matching_books)} book(s)"
                    if truncated:
                        text += f" (showing first {limit})"
                    text += f" from library of {len(all_books)} books"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "recent_books":
                self.ensure_rag_initialized()
                
                days = arguments.get("days", 1)
                include_content = arguments.get("include_content", False)
                
                # Calculate cutoff time
                from datetime import datetime, timedelta
                cutoff_time = datetime.now() - timedelta(days=days)
                
                # Find recent books from the index
                recent_books = []
                for book_path, book_info in self.rag.book_index.items():
                    # Check if book has indexed_at timestamp
                    if 'indexed_at' in book_info:
                        indexed_time = datetime.fromisoformat(book_info['indexed_at'])
                        if indexed_time > cutoff_time:
                            recent_books.append((book_path, book_info, indexed_time))
                
                # Sort by indexed time (most recent first)
                recent_books.sort(key=lambda x: x[2], reverse=True)
                
                if not recent_books:
                    text = f"No books found that were indexed in the last {days} day(s)."
                else:
                    time_period = "24 hours" if days == 1 else f"{days} days"
                    text = f"📚 Books indexed in the last {time_period}:\n\n"
                    
                    for i, (book_path, book_info, indexed_time) in enumerate(recent_books, 1):
                        book_name = os.path.basename(book_path)
                        time_ago = datetime.now() - indexed_time
                        
                        # Format time ago
                        if time_ago.days > 0:
                            time_str = f"{time_ago.days} day(s) ago"
                        elif time_ago.seconds > 3600:
                            hours = time_ago.seconds // 3600
                            time_str = f"{hours} hour(s) ago"
                        else:
                            minutes = time_ago.seconds // 60
                            time_str = f"{minutes} minute(s) ago"
                        
                        text += f"{i}. **{book_name}**\n"
                        text += f"   📁 Path: {book_path}\n"
                        text += f"   🕐 Indexed: {time_str} ({indexed_time.strftime('%Y-%m-%d %H:%M')})\n"
                        text += f"   📄 Chunks: {book_info.get('chunks', 'Unknown')}\n"
                        
                        if include_content:
                            # Search for a sample from this book
                            results = self.rag.search(f"book:{book_name}", k=1)
                            if results:
                                sample = results[0]['content'][:200] + "..." if len(results[0]['content']) > 200 else results[0]['content']
                                text += f"   📖 Sample: {sample}\n"
                        
                        text += "\n"
                    
                    text += f"\nTotal: {len(recent_books)} book(s) indexed in the last {time_period}"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "extract_pages":
                self.ensure_rag_initialized()
                book = arguments.get("book", "")
                pages = arguments.get("pages")
                
                if not book:
                    return {
                        "result": {
                            "content": [{"type": "text", "text": "Error: Book name is required"}]
                        }
                    }
                
                if pages is None:
                    return {
                        "result": {
                            "content": [{"type": "text", "text": "Error: Pages parameter is required"}]
                        }
                    }
                
                # Extract pages
                result = self.rag.extract_pages(book, pages)
                
                # Format response
                if "error" in result:
                    text = f"❌ {result['error']}\n\n"
                    if "matching_books" in result:
                        text += "Matching books:\n"
                        for i, book in enumerate(result["matching_books"][:10], 1):
                            text += f"{i}. {book}\n"
                    elif "available_books" in result:
                        text += "Available books (first 10):\n"
                        for i, book in enumerate(result["available_books"], 1):
                            text += f"{i}. {book}\n"
                else:
                    text = f"📚 Extracted pages from: {result['book']}\n"
                    text += f"📁 Path: {result['book_path']}\n"
                    text += f"📄 Requested pages: {result['requested_pages']}\n"
                    text += f"✅ Found: {result['total_pages_found']} pages\n\n"
                    
                    for page_num in sorted(result['extracted_pages'].keys()):
                        page_data = result['extracted_pages'][page_num]
                        text += f"\n━━━ Page {page_num} ━━━\n"
                        if page_data['chunks'] > 0:
                            text += f"({page_data['chunks']} chunks)\n\n"
                            text += page_data['content']
                        else:
                            text += page_data['content']
                        text += "\n"
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
            
            elif tool_name == "book_pages":
                self.ensure_rag_initialized()
                book = arguments.get("book", "")
                
                if not book:
                    return {
                        "result": {
                            "content": [{"type": "text", "text": "Error: Book name is required"}]
                        }
                    }
                
                # Get available pages for the book
                result = self.rag.get_book_pages(book)
                
                # Format response
                if "error" in result:
                    text = f"❌ {result['error']}\n\n"
                    if "matching_books" in result:
                        text += "Matching books:\n"
                        for i, book in enumerate(result["matching_books"][:10], 1):
                            text += f"{i}. {book}\n"
                    elif "available_books" in result:
                        text += "Available books (first 10):\n"
                        for i, book in enumerate(result["available_books"], 1):
                            text += f"{i}. {book}\n"
                else:
                    text = f"📚 Book: {result['book']}\n"
                    text += f"📁 Path: {result['book_path']}\n"
                    text += f"📄 Total pages in index: {result['total_pages']}\n"
                    text += f"📊 Total chunks: {result['total_chunks']}\n\n"
                    
                    if result['page_numbers']:
                        text += "Available pages:\n"
                        # Group consecutive pages for better display
                        pages = sorted(result['page_numbers'])
                        ranges = []
                        start = pages[0]
                        end = pages[0]
                        
                        for page in pages[1:]:
                            if page == end + 1:
                                end = page
                            else:
                                if start == end:
                                    ranges.append(str(start))
                                else:
                                    ranges.append(f"{start}-{end}")
                                start = page
                                end = page
                        
                        # Add the last range
                        if start == end:
                            ranges.append(str(start))
                        else:
                            ranges.append(f"{start}-{end}")
                        
                        text += ", ".join(ranges)
                    else:
                        text += "No pages found in index for this book."
                
                return {
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                }
        
        return {
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }
    
    def run(self):
        """Main loop to handle stdin/stdout communication"""
        logger.info("Complete MCP Server starting...")
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    logger.info("No more input, exiting...")
                    break
                logger.info(f"Received line: {line.strip()}")
                
                # Handle empty lines
                if not line.strip():
                    logger.info("Received empty line, continuing...")
                    continue
                
                request = json.loads(line)
                method = request.get("method", "")
                
                # Handle notifications (no response needed)
                if method.startswith("notifications/"):
                    logger.info(f"Received notification: {method}")
                    continue
                
                response = self.handle_request(request)
                
                # Add jsonrpc fields
                response["jsonrpc"] = "2.0"
                if "id" in request:
                    response["id"] = request["id"]
                
                print(json.dumps(response))
                sys.stdout.flush()
                logger.info(f"Sent response for method: {request.get('method', 'unknown')}")
                logger.info(f"Response sent: {json.dumps(response)[:200]}...")
                logger.info("Waiting for next request...")
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    },
                    "id": None  # Default id if request parsing failed
                }
                # Try to get the id from the request if available
                try:
                    if "request" in locals() and request and "id" in request:
                        error_response["id"] = request["id"]
                except:
                    pass
                print(json.dumps(error_response))
                sys.stdout.flush()

if __name__ == "__main__":
    try:
        # Ensure we're running from the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        os.chdir(project_root)
        logger.info(f"Working directory: {os.getcwd()}")
        
        logger.info("Starting CompleteMCPServer...")
        server = CompleteMCPServer()
        logger.info("Server initialized, starting main loop...")
        server.run()
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
        sys.exit(1)