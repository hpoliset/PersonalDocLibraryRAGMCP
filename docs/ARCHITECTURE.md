# Personal Document Library Architecture

## System Overview

Ragdex is a Model Context Protocol (MCP) server that provides Claude Desktop with access to a local document library and email archives through a RAG (Retrieval-Augmented Generation) system. It supports documents (PDFs, Word, EPUB, MOBI) and emails (Apple Mail EMLX, Outlook OLM) with intelligent filtering.

## Architecture Diagram

```mermaid
graph TD
    CD[Claude Desktop Client]
    MCP[MCP Complete Server]
    INIT[Lazy Initialization]
    RAG[SharedRAG Engine]
    EMB[Embeddings Model]
    VDB[(ChromaDB)]
    IDX[Book Index]
    LOAD[Document Loaders]
    PDF[PDF Processor]
    WORD[Word/PPT]
    EPUB[EPUB]
    MOBI[MOBI/AZW]
    EMLX[Apple Mail]
    OLM[Outlook]
    MON[Index Monitor]
    WEB[Web Dashboard]
    LOCK[Lock Manager]
    BOOKS[Books Directory]
    LOGS[Logs]
    CACHE[Failed Cache]

    CD -->|MCP Protocol| MCP
    MCP --> INIT
    INIT --> RAG
    RAG --> EMB
    EMB --> VDB
    RAG --> IDX
    RAG --> LOAD
    LOAD --> PDF
    LOAD --> WORD
    LOAD --> EPUB
    LOAD --> MOBI
    LOAD --> EMLX
    LOAD --> OLM
    MON --> BOOKS
    MON --> RAG
    MON --> LOCK
    WEB --> RAG
    WEB --> VDB
    BOOKS --> LOAD
    RAG --> LOGS
    RAG --> CACHE

    style CD fill:#e1f5fe
    style MCP fill:#e1f5fe
    style RAG fill:#f3e5f5
    style VDB fill:#f3e5f5
    style LOAD fill:#fff3e0
    style PDF fill:#fff3e0
    style MON fill:#e8f5e9
    style WEB fill:#e8f5e9
    style BOOKS fill:#fce4ec
```

## MCP Protocol Implementation

### Tools Workflow

```mermaid
sequenceDiagram
    participant C as Claude Desktop
    participant M as MCP Server
    participant R as SharedRAG
    participant V as VectorDB
    participant F as File System

    Note over C,F: Search Tool Example
    C->>M: tools/call: search
    M->>R: Initialize if needed
    R->>V: Query embeddings
    V-->>R: Similar chunks
    R->>F: Load book metadata
    R-->>M: Search results
    M-->>C: Formatted response

    Note over C,F: Extract Pages Tool
    C->>M: tools/call: extract_pages
    M->>R: Get book path
    R->>F: Load PDF
    F-->>R: Page content
    R-->>M: Extracted text
    M-->>C: Page content

    Note over C,F: Library Stats Tool
    C->>M: tools/call: library_stats
    M->>R: Get statistics
    R->>V: Count chunks
    R->>F: Check index status
    R-->>M: Stats data
    M-->>C: Statistics report
```

### Prompts Workflow

```mermaid
graph LR
    P1[analyze_theme]
    P2[compare_authors]
    P3[extract_practices]
    P4[research_topic]
    P5[daily_wisdom]
    GET[prompts/get]
    LIST[prompts/list]
    ARG[Argument Resolution]
    TOOL[Tool Execution]
    SYNTH[Result Synthesis]

    P1 --> GET
    P2 --> GET
    P3 --> GET
    P4 --> GET
    P5 --> GET
    LIST --> GET
    GET --> ARG
    ARG --> TOOL
    TOOL --> SYNTH
```

### Resources Workflow

```mermaid
graph TD
    R1[library://stats]
    R2[library://recent]
    R3[library://search-tips]
    R4[library://config]
    LIST[resources/list]
    READ[resources/read]
    GEN[Dynamic Generation]
    DB[(ChromaDB)]
    IDX[Book Index]
    CFG[Config]

    LIST --> R1
    LIST --> R2
    LIST --> R3
    LIST --> R4
    R1 --> READ
    R2 --> READ
    R3 --> READ
    R4 --> READ
    READ --> GEN
    GEN --> DB
    GEN --> IDX
    GEN --> CFG
```

## Detailed Tool Implementation Flows

### Search & Discovery Tools

#### 1. `search` Tool Flow
```mermaid
graph TD
    START[search request]
    PARAMS[Parse parameters]
    INIT_CHECK{RAG initialized?}
    INIT_RAG[Initialize SharedRAG]
    EMBED[Generate embedding]
    FILTER{book_filter?}
    FILTERED_SEARCH[Filtered search]
    FULL_SEARCH[Full search]
    RETRIEVE[Retrieve chunks]
    SYNTH_CHECK{synthesize?}
    SYNTHESIZE[Generate summaries]
    FORMAT[Format results]
    RESPONSE[Return response]

    START --> PARAMS
    PARAMS --> INIT_CHECK
    INIT_CHECK -->|No| INIT_RAG
    INIT_CHECK -->|Yes| EMBED
    INIT_RAG --> EMBED
    EMBED --> FILTER
    FILTER -->|Yes| FILTERED_SEARCH
    FILTER -->|No| FULL_SEARCH
    FILTERED_SEARCH --> RETRIEVE
    FULL_SEARCH --> RETRIEVE
    RETRIEVE --> SYNTH_CHECK
    SYNTH_CHECK -->|Yes| SYNTHESIZE
    SYNTH_CHECK -->|No| FORMAT
    SYNTHESIZE --> RESPONSE
    FORMAT --> RESPONSE
```

**Internal Implementation:**
- Uses `SharedRAG.search()` method
- Embedding generation via HuggingFace transformers
- ChromaDB similarity search with optional metadata filtering
- Results include chunk text, source book, page numbers

#### 2. `list_books` Tool Flow
```mermaid
graph TD
    START[list_books request]
    PARAMS[Parse parameters]
    LOAD_INDEX[Load book_index.json]
    FILTER_TYPE{Filter type?}
    PATTERN_MATCH[Pattern match]
    AUTHOR_SEARCH[Author search]
    DIR_FILTER[Directory filter]
    ALL_BOOKS[List all books]
    SORT[Sort alphabetically]
    ENRICH[Add metadata]
    RESPONSE[Return book list]

    START --> PARAMS
    PARAMS --> LOAD_INDEX
    LOAD_INDEX --> FILTER_TYPE
    FILTER_TYPE -->|pattern| PATTERN_MATCH
    FILTER_TYPE -->|author| AUTHOR_SEARCH
    FILTER_TYPE -->|directory| DIR_FILTER
    FILTER_TYPE -->|none| ALL_BOOKS
    PATTERN_MATCH --> SORT
    AUTHOR_SEARCH --> SORT
    DIR_FILTER --> SORT
    ALL_BOOKS --> SORT
    SORT --> ENRICH
    ENRICH --> RESPONSE
```

**Internal Implementation:**
- Reads from `chroma_db/book_index.json`
- Uses Python's `fnmatch` for pattern matching
- Returns book paths with indexing metadata

#### 3. `recent_books` Tool Flow
```mermaid
graph TD
    START[recent_books request] --> PARAMS[Parse parameters: hours or days]
    PARAMS --> CALC_TIME[Calculate cutoff time: now - timedelta]
    CALC_TIME --> LOAD_INDEX[Load book_index.json]
    LOAD_INDEX --> FILTER_TIME[Filter books where: indexed_at > cutoff]
    FILTER_TIME --> SORT_TIME[Sort by indexed_at: descending]
    SORT_TIME --> FORMAT[Format with relative time: "2 hours ago"]
    FORMAT --> RESPONSE[Return recent books list]
```

**Internal Implementation:**
- Uses `datetime.fromisoformat()` for timestamp parsing
- Calculates relative time strings
- Groups by time periods (today, yesterday, this week)

#### 4. `find_practices` Tool Flow
```mermaid
graph TD
    START[find_practices request] --> PARAM[Parse practice_type]
    PARAM --> BUILD_QUERY[Build semantic query: "practical exercises {practice_type}"]
    BUILD_QUERY --> SEARCH_CAT[Search with category filter: category = 'practice']
    SEARCH_CAT --> EXTRACT[Extract practice descriptions: from chunks]
    EXTRACT --> DEDUPE[Deduplicate similar practices]
    DEDUPE --> GROUP[Group by practice type]
    GROUP --> RESPONSE[Return practices with sources]
```

**Internal Implementation:**
- Leverages categorization from indexing
- Uses semantic search with practice-focused queries
- Groups results by technique type

### Content Extraction Tools

#### 5. `extract_pages` Tool Flow
```mermaid
graph TD
    START[extract_pages request] --> PARAMS[Parse parameters: book_pattern, pages]
    PARAMS --> FIND_BOOK[Find matching book: in book_index.json]
    FIND_BOOK --> FOUND{Book: found?}
    FOUND -->|No| ERROR[Return error: Book not found]
    FOUND -->|Yes| PARSE_PAGES[Parse page specification: int, list, or range]
    PARSE_PAGES --> LOAD_PDF[Load PDF with PyPDF2]
    LOAD_PDF --> EXTRACT_LOOP[For each page number]
    EXTRACT_LOOP --> EXTRACT_TEXT[Extract page text]
    EXTRACT_TEXT --> APPEND[Append to results]
    APPEND --> MORE{More: pages?}
    MORE -->|Yes| EXTRACT_LOOP
    MORE -->|No| RESPONSE[Return extracted text]
```

**Internal Implementation:**
- Uses `PyPDF2.PdfReader` for PDF access
- Supports page ranges like "1-5" or lists like [1,3,5]
- Handles out-of-range pages gracefully

#### 6. `extract_quotes` Tool Flow
```mermaid
graph TD
    START[extract_quotes request] --> PARAMS[Parse parameters: topic, max_quotes]
    PARAMS --> SEARCH_QUOTES[Search for: "quotes about {topic}"]
    SEARCH_QUOTES --> RETRIEVE[Retrieve relevant chunks]
    RETRIEVE --> QUOTE_DETECT[Detect quote patterns: quotation marks, attribution]
    QUOTE_DETECT --> SCORE[Score by relevance: and quote quality]
    SCORE --> SELECT[Select top max_quotes]
    SELECT --> FORMAT[Format with context: and attribution]
    FORMAT --> RESPONSE[Return quotes list]
```

**Internal Implementation:**
- Uses regex patterns for quote detection
- Scores based on punctuation patterns and attribution
- Preserves context around quotes

#### 7. `summarize_book` Tool Flow
```mermaid
graph TD
    START[summarize_book request] --> PARAMS[Parse parameters: book_name, summary_length]
    PARAMS --> FIND_BOOK[Find book in index]
    FIND_BOOK --> GET_CHUNKS[Retrieve all book chunks: from ChromaDB]
    GET_CHUNKS --> SAMPLE{summary_length?}
    SAMPLE -->|brief| SAMPLE_CHUNKS[Sample key chunks: ~10-15 chunks]
    SAMPLE -->|detailed| ALL_CHUNKS[Use all chunks]
    SAMPLE_CHUNKS --> EXTRACT_THEMES[Extract main themes: via frequency analysis]
    ALL_CHUNKS --> EXTRACT_THEMES
    EXTRACT_THEMES --> BUILD_SUMMARY[Build structured summary: Overview, Key Points, Themes]
    BUILD_SUMMARY --> RESPONSE[Return formatted summary]
```

**Internal Implementation:**
- Retrieves chunks by metadata filter
- Uses TF-IDF for theme extraction
- Structures summary with sections

### Analysis & Synthesis Tools

#### 8. `compare_perspectives` Tool Flow
```mermaid
graph TD
    START[compare_perspectives request] --> PARAM[Parse topic parameter]
    PARAM --> SEARCH_MULTI[Search across all sources: for topic]
    SEARCH_MULTI --> GROUP_SOURCE[Group results by source book]
    GROUP_SOURCE --> EXTRACT_VIEW[Extract viewpoint: from each source]
    EXTRACT_VIEW --> IDENTIFY_SIM[Identify similarities]
    IDENTIFY_SIM --> IDENTIFY_DIFF[Identify differences]
    IDENTIFY_DIFF --> BUILD_COMP[Build comparison matrix]
    BUILD_COMP --> FORMAT_TABLE[Format as comparison table]
    FORMAT_TABLE --> RESPONSE[Return comparative analysis]
```

**Internal Implementation:**
- Groups search results by source metadata
- Extracts key points per source
- Creates structured comparison output

#### 9. `question_answer` Tool Flow
```mermaid
graph TD
    START[question_answer request] --> PARAMS[Parse parameters: question, detail_level]
    PARAMS --> ANALYZE_Q[Analyze question type: factual, conceptual, practical]
    ANALYZE_Q --> BUILD_QUERY[Build optimized query]
    BUILD_QUERY --> SEARCH[Semantic search]
    SEARCH --> RANK[Rank results by relevance]
    RANK --> DETAIL{detail_level?}
    DETAIL -->|concise| SELECT_TOP[Select top 3 chunks]
    DETAIL -->|detailed| SELECT_MORE[Select top 10 chunks]
    SELECT_TOP --> SYNTHESIZE[Synthesize answer]
    SELECT_MORE --> SYNTHESIZE
    SYNTHESIZE --> CITE[Add citations]
    CITE --> RESPONSE[Return answer with sources]
```

**Internal Implementation:**
- Question type detection for query optimization
- Relevance ranking using similarity scores
- Citation formatting with page numbers

#### 10. `daily_reading` Tool Flow
```mermaid
graph TD
    START[daily_reading request] --> PARAMS[Parse parameters: theme, length]
    PARAMS --> CHECK_HISTORY[Check reading history: in logs]
    CHECK_HISTORY --> AVOID_RECENT[Filter out recent selections]
    AVOID_RECENT --> THEME{theme: provided?}
    THEME -->|Yes| THEMED_SEARCH[Search for theme]
    THEME -->|No| RANDOM_SELECT[Random selection]
    THEMED_SEARCH --> LENGTH{length?}
    RANDOM_SELECT --> LENGTH
    LENGTH -->|short| SELECT_1[Select 1-2 passages]
    LENGTH -->|medium| SELECT_3[Select 3-4 passages]
    LENGTH -->|long| SELECT_5[Select 5-6 passages]
    SELECT_1 --> FORMAT_READING[Format with reflection prompts]
    SELECT_3 --> FORMAT_READING
    SELECT_5 --> FORMAT_READING
    FORMAT_READING --> LOG_SELECTION[Log selection to history]
    LOG_SELECTION --> RESPONSE[Return daily reading]
```

**Internal Implementation:**
- Maintains reading history in logs
- Weighted random selection
- Adds reflection questions

### System Management Tools

#### 11. `library_stats` Tool Flow
```mermaid
graph TD
    START[library_stats request] --> INIT_CHECK{RAG: initialized?}
    INIT_CHECK -->|No| INIT_RAG[Initialize SharedRAG]
    INIT_CHECK -->|Yes| GATHER
    INIT_RAG --> GATHER[Gather statistics]
    GATHER --> COUNT_BOOKS[Count books in index]
    COUNT_BOOKS --> COUNT_CHUNKS[Query ChromaDB: for chunk count]
    COUNT_CHUNKS --> COUNT_PAGES[Sum page counts: from metadata]
    COUNT_PAGES --> CHECK_FAILED[Check failed_pdfs.json]
    CHECK_FAILED --> CHECK_STATUS[Check index_status.json]
    CHECK_STATUS --> CALC_SIZE[Calculate DB size]
    CALC_SIZE --> FORMAT_STATS[Format statistics]
    FORMAT_STATS --> RESPONSE[Return stats object]
```

**Internal Implementation:**
- Aggregates data from multiple sources
- Calculates storage metrics
- Returns comprehensive statistics

#### 12. `index_status` Tool Flow
```mermaid
graph TD
    START[index_status request] --> READ_STATUS[Read index_status.json]
    READ_STATUS --> READ_PROGRESS[Read indexing_progress.json]
    READ_PROGRESS --> CHECK_LOCK[Check lock file status]
    CHECK_LOCK --> LOCKED{Lock: exists?}
    LOCKED -->|Yes| CHECK_PID[Check if PID active]
    LOCKED -->|No| STATUS_IDLE
    CHECK_PID --> ACTIVE{Process: active?}
    ACTIVE -->|Yes| STATUS_ACTIVE[Status: Indexing active]
    ACTIVE -->|No| STATUS_STALE[Status: Stale lock]
    STATUS_ACTIVE --> FORMAT_PROGRESS[Include progress details]
    STATUS_STALE --> SUGGEST_CLEANUP[Suggest cleanup action]
    STATUS_IDLE[Status: Idle]
    FORMAT_PROGRESS --> RESPONSE[Return status report]
    SUGGEST_CLEANUP --> RESPONSE
    STATUS_IDLE --> RESPONSE
```

**Internal Implementation:**
- Reads multiple status files
- Process checking via PID
- Real-time progress calculation

#### 13. `refresh_cache` Tool Flow
```mermaid
graph TD
    START[refresh_cache request] --> CLEAR_CACHE[Clear in-memory caches]
    CLEAR_CACHE --> RELOAD_INDEX[Reload book_index.json]
    RELOAD_INDEX --> RELOAD_FAILED[Reload failed_pdfs.json]
    RELOAD_FAILED --> RECONNECT_DB[Reconnect to ChromaDB]
    RECONNECT_DB --> VERIFY[Verify collection exists]
    VERIFY --> COUNT[Get updated counts]
    COUNT --> RESPONSE[Return refresh status]
```

**Internal Implementation:**
- Clears `SharedRAG._instance`
- Forces reload of all cached data
- Verifies database connectivity

#### 14. `warmup` Tool Flow
```mermaid
graph TD
    START[warmup request] --> INIT_RAG[Initialize SharedRAG]
    INIT_RAG --> LOAD_MODEL[Load embedding model: ~4GB memory]
    LOAD_MODEL --> CONNECT_DB[Connect to ChromaDB]
    CONNECT_DB --> LOAD_INDEX[Load book index]
    LOAD_INDEX --> TEST_QUERY[Run test query: "test warmup"]
    TEST_QUERY --> MEASURE[Measure load times]
    MEASURE --> RESPONSE[Return warmup stats]
```

**Internal Implementation:**
- Pre-loads heavy components
- Prevents timeout on first real query
- Returns performance metrics

#### 15. `find_unindexed` Tool Flow
```mermaid
graph TD
    START[find_unindexed request] --> SCAN_DIR[Scan books directory: for supported formats]
    SCAN_DIR --> LOAD_INDEX[Load book_index.json]
    LOAD_INDEX --> COMPARE[Compare file lists]
    COMPARE --> FILTER_NEW[Filter unindexed files]
    FILTER_NEW --> CHECK_FAILED[Check against failed_pdfs.json]
    CHECK_FAILED --> CATEGORIZE[Categorize: New, Modified, Failed]
    CATEGORIZE --> FORMAT_LIST[Format with file sizes: and modification times]
    FORMAT_LIST --> RESPONSE[Return unindexed list]
```

**Internal Implementation:**
- Uses `os.walk()` for directory scanning
- MD5 hash comparison for modifications
- Returns actionable file list

#### 16. `reindex_book` Tool Flow
```mermaid
graph TD
    START[reindex_book request] --> PARAM[Parse book_name]
    PARAM --> FIND_BOOK[Find book in index]
    FIND_BOOK --> FOUND{Found?}
    FOUND -->|No| ERROR[Return error]
    FOUND -->|Yes| REMOVE_CHUNKS[Delete chunks from ChromaDB: by metadata filter]
    REMOVE_CHUNKS --> REMOVE_INDEX[Remove from book_index.json]
    REMOVE_INDEX --> PROCESS_DOC[Process document again]
    PROCESS_DOC --> CHUNK[Chunk text]
    CHUNK --> EMBED[Generate embeddings]
    EMBED --> STORE[Store in ChromaDB]
    STORE --> UPDATE_INDEX[Update book_index.json]
    UPDATE_INDEX --> RESPONSE[Return reindex status]
```

**Internal Implementation:**
- Full cleanup before reindexing
- Uses same pipeline as initial indexing
- Preserves document categorization

#### 17. `clear_failed` Tool Flow
```mermaid
graph TD
    START[clear_failed request] --> BACKUP[Backup failed_pdfs.json]
    BACKUP --> CLEAR[Clear failed list]
    CLEAR --> SAVE[Save empty failed_pdfs.json]
    SAVE --> COUNT[Count cleared entries]
    COUNT --> RESPONSE[Return clear status]
```

**Internal Implementation:**
- Creates timestamped backup
- Resets failed tracking
- Allows retry of previously failed documents

## Component Details

### MCP Complete Server
- **Location**: `src/personal_doc_library/servers/mcp_complete_server.py`
- **Purpose**: Main entry point for Claude Desktop integration
- **Features**:
  - Lazy initialization (< 1 second startup)
  - 17 tools for document interaction
  - 5 prompt templates for common workflows
  - 4 dynamic resources for real-time information
  - Capability advertisement in initialize response

### SharedRAG Engine
- **Location**: `src/personal_doc_library/core/shared_rag.py`
- **Purpose**: Core RAG functionality
- **Features**:
  - Document chunking (1200 chars, 150 overlap)
  - Semantic embedding generation
  - Vector similarity search
  - Book index management
  - Category-based filtering

### Document Processing Pipeline

```mermaid
graph LR
    DOC[Document]
    HASH[MD5 Hash]
    CHECK{Already: Indexed?}
    LOAD[Load Document]
    CHUNK[Chunk Text: 1200 chars]
    CAT[Categorize]
    EMB[Generate: Embeddings]
    STORE[Store in: ChromaDB]
    INDEX[Update: Book Index]

    DOC --> HASH
    HASH --> CHECK
    CHECK -->|No| LOAD
    CHECK -->|Yes| END[Skip]
    LOAD --> CHUNK
    CHUNK --> CAT
    CAT --> EMB
    EMB --> STORE
    STORE --> INDEX
```

### Index Monitor Service
- **Location**: `src/personal_doc_library/indexing/index_monitor.py`
- **Purpose**: Background document indexing
- **Features**:
  - File system event monitoring
  - Automatic new document detection
  - 30-minute stale lock cleanup
  - Failed document tracking
  - Progress status updates

### Web Dashboard
- **Location**: `src/personal_doc_library/monitoring/monitor_web_enhanced.py`
- **Purpose**: Real-time monitoring interface
- **URL**: http://localhost:8888
- **Features**:
  - Library statistics
  - Search interface with Enter key support
  - Document browsing
  - Failed document management
  - Lock status monitoring

## Data Flow

### Indexing Flow
```
Books Directory → File Watcher → Document Loader → Text Extraction
→ Chunking → Categorization → Embedding → Vector Storage → Index Update
```

### Search Flow
```
Query → Embedding Generation → Vector Similarity Search → Chunk Retrieval
→ Book Metadata Loading → Result Ranking → Response Formatting
```

### Tool Execution Flow
```
Claude Desktop → MCP Protocol → Tool Handler → RAG System
→ Data Processing → Response Generation → MCP Response → Claude Desktop
```

## Security Architecture

### Isolation Layers
1. **Process Isolation**: MCP server runs in separate process
2. **File System Boundaries**: Restricted to configured directories
3. **No Network Access**: All processing is local
4. **User Permissions**: Services run with user permissions only

### Data Protection
- No data leaves the local machine
- Vector database stored locally
- Logs stored locally with rotation
- No telemetry or analytics

## Performance Optimizations

### Lazy Loading
- RAG system initialized only when first tool is called
- Prevents MCP timeout during startup
- Sub-1 second initialization time

### Caching Strategy
- MD5 hash-based document tracking
- Book index for quick lookups
- Failed document cache to skip problematic files
- Search result caching

### Resource Management
- 15-minute timeout protection for long operations
- File lock management with 30-minute cleanup
- Batch processing for multiple documents
- Memory monitoring during indexing

## Error Handling

### Resilience Features
- Automatic PDF cleaning for corrupted files
- OCR fallback for scanned PDFs
- Timeout protection with graceful recovery
- Failed document tracking and retry logic
- Stale lock detection and cleanup

### Monitoring Points
- Service health checks
- Indexing progress tracking
- Error logging with categories
- Web dashboard for real-time status

## Scalability

### Current Limits
- Tested with libraries up to 10,000 documents
- ChromaDB handles millions of vectors
- 768-dimensional embeddings for accuracy
- Parallel processing for document indexing

### Growth Path
- Modular architecture allows component upgrades
- Database can be migrated to other vector stores
- Processing pipeline supports custom transformers
- MCP protocol allows tool additions without breaking changes