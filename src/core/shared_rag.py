#!/usr/bin/env python3
"""
Shared RAG System for Spiritual Library
Common functionality used by both MCP server and background indexer
"""

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredEPubLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
# from langchain_community.llms import Ollama  # Removed for direct RAG results
import os
import logging
import torch
import hashlib
import json
import time
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import fcntl
from contextlib import contextmanager
from .config import config
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import psutil
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndexLock:
    """File-based locking to prevent simultaneous indexing with stale lock detection"""
    def __init__(self, lock_file="/tmp/spiritual_library_index.lock", stale_timeout_minutes=30):
        self.lock_file = lock_file
        self.lock_fd = None
        self.stale_timeout_minutes = stale_timeout_minutes
        self.update_thread = None
        self.stop_update = threading.Event()
        # Clean stale locks on initialization
        self.clean_stale_lock()
    
    def is_lock_stale(self):
        """Check if existing lock file is from a dead process or too old"""
        if not os.path.exists(self.lock_file):
            return False
        
        try:
            # Check file age
            mtime = os.path.getmtime(self.lock_file)
            age_minutes = (time.time() - mtime) / 60
            
            if age_minutes > self.stale_timeout_minutes:
                logger.info(f"Lock file is {age_minutes:.1f} minutes old, considering stale")
                return True
            
            # Check if process is alive
            with open(self.lock_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    pid = int(lines[0].strip())
                    try:
                        # Signal 0 checks if process exists without sending signal
                        os.kill(pid, 0)
                        return False  # Process is alive
                    except ProcessLookupError:
                        logger.info(f"Lock held by dead process {pid}")
                        return True  # Process is dead
                    except PermissionError:
                        # Process exists but we can't signal it
                        return False
        except Exception as e:
            logger.warning(f"Error checking lock status: {e}")
            return True  # Consider stale if we can't check properly
    
    def clean_stale_lock(self):
        """Remove stale lock files from dead processes"""
        if self.is_lock_stale():
            try:
                os.remove(self.lock_file)
                logger.info("Cleaned up stale lock file")
            except Exception as e:
                logger.warning(f"Could not remove stale lock: {e}")
    
    def get_lock_info(self):
        """Get information about current lock holder"""
        if not os.path.exists(self.lock_file):
            return None
        
        try:
            with open(self.lock_file, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    pid = int(lines[0].strip())
                    timestamp = lines[1].strip()
                    
                    # Check if process is alive
                    try:
                        os.kill(pid, 0)
                        alive = True
                    except:
                        alive = False
                    
                    return {
                        "pid": pid,
                        "timestamp": timestamp,
                        "alive": alive,
                        "age_minutes": (time.time() - os.path.getmtime(self.lock_file)) / 60
                    }
        except:
            pass
        return None
    
    def start_periodic_update(self):
        """Start background thread to update lock timestamp"""
        def update_loop():
            while not self.stop_update.is_set():
                try:
                    # Touch the lock file to update mtime
                    os.utime(self.lock_file, None)
                    # Also rewrite content with current timestamp
                    with open(self.lock_file, 'w') as f:
                        f.write(f"{os.getpid()}\n{datetime.now().isoformat()}")
                except Exception as e:
                    logger.warning(f"Failed to update lock timestamp: {e}")
                # Wait 30 seconds or until stop signal
                self.stop_update.wait(30)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        logger.info("Started lock periodic update thread")
    
    def stop_periodic_update(self):
        """Stop the periodic update thread"""
        if self.update_thread and self.update_thread.is_alive():
            self.stop_update.set()
            self.update_thread.join(timeout=1)
            logger.info("Stopped lock periodic update thread")
    
    @contextmanager
    def acquire(self, blocking=False):
        """Acquire index lock with context manager"""
        # Clean stale locks before attempting
        self.clean_stale_lock()
        
        self.lock_fd = open(self.lock_file, 'w')
        try:
            if blocking:
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX)
            else:
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(f"{os.getpid()}\n{datetime.now().isoformat()}")
            self.lock_fd.flush()
            # Start periodic update thread
            self.start_periodic_update()
            yield
        except IOError:
            if self.lock_fd:
                self.lock_fd.close()
            logger.warning("Could not acquire index lock - another process may be indexing")
            raise
        finally:
            # Stop periodic update thread
            self.stop_periodic_update()
            if self.lock_fd:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                try:
                    os.remove(self.lock_file)
                except:
                    pass

class PDFCleaner:
    """Handles PDF cleaning for problematic files"""
    
    @staticmethod
    def clean_pdf(input_path, output_path, timeout_minutes=10):
        """Clean a PDF using Ghostscript"""
        try:
            logger.info(f"Cleaning {os.path.basename(input_path)}...")
            
            cmd = [
                'gs', '-dBATCH', '-dNOPAUSE', '-q',
                '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/ebook', '-dCompressFonts=true',
                '-dSubsetFonts=true', '-dOptimize=true',
                '-dColorImageResolution=150',
                f'-sOutputFile={output_path}', input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=timeout_minutes * 60)
            
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully cleaned {os.path.basename(input_path)}")
                return True
            return False
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout cleaning PDF after {timeout_minutes} minutes")
            return False
        except Exception as e:
            logger.error(f"Error cleaning PDF: {e}")
            return False

class SharedRAG:
    """Core RAG functionality shared between server and monitor"""
    
    def __init__(self, books_directory=None, db_directory=None):
        # Use config system if no explicit paths provided
        self.books_directory = books_directory if books_directory is not None else str(config.books_directory)
        self.db_directory = db_directory if db_directory is not None else str(config.db_directory)
        
        # Ensure directories exist
        config.ensure_directories()
        
        logger.info(f"SharedRAG initialized with books_directory: {self.books_directory}")
        logger.info(f"SharedRAG initialized with db_directory: {self.db_directory}")
        
        self.index_file = os.path.join(self.db_directory, "book_index.json")
        self.status_file = os.path.join(self.db_directory, "index_status.json")
        self.failed_pdfs_file = os.path.join(self.db_directory, "failed_pdfs.json")
        self.book_index = self.load_book_index()
        self.lock = IndexLock()
        
        # Simple search cache for performance
        self._search_cache = {}
        self._cache_ttl = 300  # 5 minutes TTL
        
        # Initialize embeddings
        logger.info("Initializing embeddings...")
        device = 'mps' if hasattr(torch, 'backends') and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'cpu'
        
        # BACKUP: Original 384-dim model was "sentence-transformers/all-MiniLM-L6-v2"
        # Switching to original 768-dim model to match existing database
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # LLM initialization removed - using direct RAG results
        # logger.info("Initializing Ollama LLM...")
        # self.llm = Ollama(model="llama3.3:70b")
        
        # Initialize or load vector store
        self.vectorstore = self.initialize_vectorstore()
    
    def load_book_index(self):
        """Load the book index from disk"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_book_index(self):
        """Save the book index to disk"""
        os.makedirs(self.db_directory, exist_ok=True)
        with open(self.index_file, 'w') as f:
            json.dump(self.book_index, f, indent=2)
    
    def update_status(self, status, details=None):
        """Update indexing status file"""
        status_data = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def get_indexing_status(self):
        """Get current indexing status"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"status": "idle", "timestamp": datetime.now().isoformat()}
    
    def get_status(self):
        """Legacy method name for backward compatibility"""
        return self.get_indexing_status()
    
    def get_lock_status(self):
        """Get detailed lock status"""
        return self.lock.get_lock_info()
    
    def update_progress(self, stage, current_page=None, total_pages=None, chunks_generated=None, current_file=None):
        """Update detailed progress tracking"""
        progress_file = os.path.join(self.db_directory, "indexing_progress.json")
        
        # Get memory usage
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
        except:
            memory_mb = 0
        
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,  # loading, extracting, chunking, embedding
            "current_page": current_page,
            "total_pages": total_pages,
            "chunks_generated": chunks_generated,
            "memory_mb": round(memory_mb, 1),
            "current_file": current_file or self.get_status().get('details', {}).get('current_file')
        }
        
        try:
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not update progress: {e}")
    
    def is_process_healthy(self):
        """Check if the indexing process is healthy"""
        progress_file = os.path.join(self.db_directory, "indexing_progress.json")
        
        # Check if progress file exists
        if not os.path.exists(progress_file):
            return True  # No active indexing
        
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            # Check timestamp age
            timestamp = datetime.fromisoformat(progress['timestamp'])
            age_seconds = (datetime.now() - timestamp).total_seconds()
            
            # If no update for more than 2 minutes, might be stuck
            if age_seconds > 120:
                logger.warning(f"Progress hasn't been updated for {age_seconds:.0f} seconds")
                return False
            
            # Check memory usage trends
            memory_mb = progress.get('memory_mb', 0)
            if memory_mb > 8000:  # More than 8GB
                logger.warning(f"High memory usage: {memory_mb:.0f} MB")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking process health: {e}")
            return True  # Assume healthy on error
    
    def get_file_hash(self, filepath):
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def initialize_vectorstore(self):
        """Initialize or load the vector store"""
        if os.path.exists(self.db_directory) and os.path.exists(os.path.join(self.db_directory, "chroma.sqlite3")):
            logger.info("Loading existing vector store...")
            return Chroma(
                persist_directory=self.db_directory,
                embedding_function=self.embeddings
            )
        else:
            logger.info("Creating new vector store...")
            os.makedirs(self.db_directory, exist_ok=True)
            return Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.db_directory
            )
    
    def find_new_or_modified_documents(self):
        """Find documents that need indexing (PDFs, Word docs, EPUBs)"""
        if not os.path.exists(self.books_directory):
            return []
        
        # Supported file extensions
        supported_extensions = ('.pdf', '.docx', '.doc', '.epub')
        documents_to_index = []
        
        for root, dirs, files in os.walk(self.books_directory):
            # Skip originals directory
            if "originals" in root:
                continue
                
            for file in files:
                if file.lower().endswith(supported_extensions):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.books_directory)
                    file_hash = self.get_file_hash(filepath)
                    
                    if rel_path not in self.book_index or self.book_index[rel_path].get('hash') != file_hash:
                        documents_to_index.append((filepath, rel_path))
        
        return documents_to_index
    
    def find_new_or_modified_pdfs(self):
        """Legacy method - now calls find_new_or_modified_documents for backward compatibility"""
        return self.find_new_or_modified_documents()
    
    def get_document_loader(self, filepath):
        """Get the appropriate document loader based on file extension"""
        file_ext = os.path.splitext(filepath)[1].lower()
        
        if file_ext == '.pdf':
            return PyPDFLoader(filepath)
        elif file_ext in ['.docx', '.doc']:
            return UnstructuredWordDocumentLoader(filepath)
        elif file_ext == '.epub':
            return UnstructuredEPubLoader(filepath)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def get_document_type(self, filepath):
        """Get a human-readable document type from file extension"""
        file_ext = os.path.splitext(filepath)[1].lower()
        
        type_mapping = {
            '.pdf': 'PDF',
            '.docx': 'Word Document',
            '.doc': 'Word Document',
            '.epub': 'EPUB Book'
        }
        
        return type_mapping.get(file_ext, 'Document')
    
    def process_document_with_timeout(self, filepath, rel_path=None, timeout_minutes=10):
        """Process any supported document with timeout protection"""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.process_document, filepath, rel_path)
            try:
                return future.result(timeout=timeout_minutes * 60)
            except FutureTimeoutError:
                logger.error(f"Processing timeout after {timeout_minutes} minutes for {filepath}")
                self.handle_failed_document(filepath, f"Processing timeout after {timeout_minutes} minutes - file too large or complex")
                return False
            except Exception as e:
                logger.error(f"Error in thread: {e}")
                return False
    
    def process_pdf_with_timeout(self, filepath, rel_path=None, timeout_minutes=10):
        """Legacy method - now calls process_document_with_timeout for backward compatibility"""
        return self.process_document_with_timeout(filepath, rel_path, timeout_minutes)
    
    def prepare_file_for_processing(self, filepath, rel_path):
        """Prepare file for processing, handling CloudDocs permission issues"""
        # Check if this is a CloudDocs file
        if "Mobile Documents/com~apple~CloudDocs" in filepath:
            logger.info(f"CloudDocs file detected, creating accessible copy: {rel_path}")
            
            # Create temp directory for CloudDocs files
            temp_dir = os.path.join(self.db_directory, "temp_cloudocs")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create safe filename from rel_path
            safe_filename = rel_path.replace("/", "_").replace(" ", "_")
            temp_filepath = os.path.join(temp_dir, safe_filename)
            
            try:
                # Copy file to accessible location
                shutil.copy2(filepath, temp_filepath)
                logger.info(f"Created temporary copy at: {temp_filepath}")
                return temp_filepath
            except Exception as e:
                logger.error(f"Failed to copy CloudDocs file: {e}")
                # Fall back to original path and let the error happen
                return filepath
        else:
            # Regular file, use as-is
            return filepath
    
    def cleanup_temp_file(self, working_filepath, original_filepath):
        """Clean up temporary file if it was created"""
        if working_filepath != original_filepath:
            try:
                os.remove(working_filepath)
                logger.debug(f"Cleaned up temporary file: {working_filepath}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file {working_filepath}: {e}")
    
    def process_document(self, filepath, rel_path=None):
        """Process any supported document and add it to the index"""
        if not rel_path:
            rel_path = os.path.relpath(filepath, self.books_directory)
        
        working_filepath = filepath  # Initialize to original path
        
        try:
            doc_type = self.get_document_type(filepath)
            logger.info(f"Processing {doc_type}: {rel_path}")
            
            # Update status but preserve any existing details like progress
            try:
                with open(self.status_file, 'r') as f:
                    current_status = json.load(f)
                    existing_details = current_status.get('details', {})
            except:
                existing_details = {}
            
            # Merge with existing details to preserve progress info
            existing_details['current_file'] = rel_path
            self.update_status("indexing", existing_details)
            self.update_progress("starting", current_file=rel_path)
            
            # Check file size before processing
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            if file_size_mb > 500:  # Skip files larger than 500MB
                logger.warning(f"Skipping {rel_path}: File too large ({file_size_mb:.1f}MB)")
                self.handle_failed_document(filepath, f"File too large: {file_size_mb:.1f}MB")
                return False
            
            # Handle CloudDocs permission issue by copying to temp location if needed
            working_filepath = self.prepare_file_for_processing(filepath, rel_path)
            
            # Load the document using appropriate loader
            self.update_progress("loading", current_file=rel_path)
            logger.info(f"Loading {doc_type}: {rel_path} ({file_size_mb:.1f}MB)")
            
            loader = self.get_document_loader(working_filepath)
            documents = loader.load()
            
            if not documents:
                raise Exception(f"No content extracted from {doc_type}")
            
            # For non-PDF documents, we don't have page count, so use document count
            total_sections = len(documents)
            logger.info(f"Loaded {total_sections} sections from {rel_path}")
            self.update_progress("extracting", total_pages=total_sections, current_file=rel_path)
            
            # Split into chunks with optimized parameters
            logger.info(f"Splitting {rel_path} into chunks...")
            self.update_progress("chunking", total_pages=total_sections, current_file=rel_path)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200,  # Slightly larger chunks for better context
                chunk_overlap=150,  # Less overlap for efficiency
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len
            )
            
            chunks = text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} chunks from {rel_path}")
            self.update_progress("chunking", total_pages=total_sections, chunks_generated=len(chunks), current_file=rel_path)
            
            # Add metadata
            for chunk in chunks:
                chunk.metadata['book'] = os.path.basename(filepath)
                chunk.metadata['document_type'] = doc_type
                chunk.metadata['indexed_at'] = datetime.now().isoformat()
                
                # Categorize content
                content = chunk.page_content.lower()
                if any(word in content for word in ['meditation', 'mindfulness', 'breath', 'breathing']):
                    chunk.metadata['type'] = 'practice'
                elif any(word in content for word in ['energy', 'chakra', 'healing', 'aura']):
                    chunk.metadata['type'] = 'energy_work'
                elif any(word in content for word in ['conscious', 'awareness', 'enlighten', 'spiritual']):
                    chunk.metadata['type'] = 'philosophy'
                else:
                    chunk.metadata['type'] = 'general'
            
            # Remove old chunks if re-indexing
            if rel_path in self.book_index:
                self.remove_book_by_path(rel_path, skip_save=True)
            
            # Add to vector store with batch optimization
            logger.info(f"Adding {len(chunks)} chunks to vector store...")
            self.update_progress("embedding", total_pages=total_sections, chunks_generated=len(chunks), current_file=rel_path)
            
            # Add in batches for better performance
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                self.vectorstore.add_documents(batch)
                if i + batch_size < len(chunks):
                    self.update_progress("embedding", total_pages=total_sections, 
                                       chunks_generated=len(chunks), 
                                       current_file=rel_path,
                                       current_page=f"Batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            
            self.vectorstore.persist()
            self.update_progress("completed", total_pages=total_sections, chunks_generated=len(chunks), current_file=rel_path)
            
            # Update index
            self.book_index[rel_path] = {
                'hash': self.get_file_hash(filepath),
                'chunks': len(chunks),
                'pages': total_sections,  # For non-PDFs, this represents sections/documents
                'document_type': doc_type,
                'indexed_at': datetime.now().isoformat()
            }
            self.save_book_index()
            
            logger.info(f"Successfully indexed {rel_path}: {len(chunks)} chunks from {total_sections} sections")
            
            # Clean up temporary file if it was created
            self.cleanup_temp_file(working_filepath, filepath)
            
            # Force garbage collection to free memory
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {filepath}: {str(e)}")
            self.handle_failed_document(filepath, str(e))
            
            # Clean up temporary file if it was created
            self.cleanup_temp_file(working_filepath, filepath)
            
            # Force garbage collection even on error
            import gc
            gc.collect()
            
            return False
    
    def process_pdf(self, filepath, rel_path=None):
        """Legacy method - now calls process_document for backward compatibility"""
        return self.process_document(filepath, rel_path)
    
    def handle_failed_document(self, filepath, error_msg):
        """Handle a document that failed to index by attempting to clean it (PDFs only)"""
        # Only attempt cleaning for PDFs
        if not filepath.lower().endswith('.pdf'):
            # For non-PDF documents, just log the failure
            failed_docs = {}
            if os.path.exists(self.failed_pdfs_file):
                try:
                    with open(self.failed_pdfs_file, 'r') as f:
                        failed_docs = json.load(f)
                except:
                    pass
            
            doc_name = os.path.basename(filepath)
            failed_docs[doc_name] = {
                "error": error_msg,
                "cleaned": False,
                "failed_at": datetime.now().isoformat()
            }
            
            with open(self.failed_pdfs_file, 'w') as f:
                json.dump(failed_docs, f, indent=2)
            
            return False
        
        # For PDFs, attempt cleaning
        return self.handle_failed_pdf(filepath, error_msg)
    
    def handle_failed_pdf(self, filepath, error_msg):
        """Handle a PDF that failed to index by attempting to clean it"""
        # Load failed PDFs log
        failed_pdfs = {}
        if os.path.exists(self.failed_pdfs_file):
            try:
                with open(self.failed_pdfs_file, 'r') as f:
                    failed_pdfs = json.load(f)
            except:
                pass
        
        pdf_name = os.path.basename(filepath)
        
        # Don't retry if already cleaned
        if pdf_name in failed_pdfs and failed_pdfs[pdf_name].get("cleaned", False):
            return False
        
        logger.info(f"Attempting to clean failed PDF: {pdf_name}")
        
        # Create directories
        originals_dir = os.path.join(self.books_directory, "originals")
        os.makedirs(originals_dir, exist_ok=True)
        
        # Paths
        original_backup = os.path.join(originals_dir, pdf_name)
        temp_cleaned = filepath + ".cleaned.tmp"
        
        # Try to clean
        if PDFCleaner.clean_pdf(filepath, temp_cleaned):
            try:
                # Backup original
                shutil.copy2(filepath, original_backup)
                # Replace with cleaned
                shutil.move(temp_cleaned, filepath)
                
                # Record in log
                failed_pdfs[pdf_name] = {
                    "error": error_msg,
                    "cleaned": True,
                    "cleaned_at": datetime.now().isoformat(),
                    "original_backup": original_backup
                }
                
                with open(self.failed_pdfs_file, 'w') as f:
                    json.dump(failed_pdfs, f, indent=2)
                
                logger.info(f"Successfully cleaned {pdf_name}. Will retry indexing.")
                
                # Try indexing again
                return self.process_pdf(filepath)
                
            except Exception as e:
                logger.error(f"Error during cleaning: {e}")
                # Restore original if needed
                if os.path.exists(original_backup) and not os.path.exists(filepath):
                    shutil.copy2(original_backup, filepath)
        else:
            # Record failure
            failed_pdfs[pdf_name] = {
                "error": error_msg,
                "cleaned": False,
                "attempted_at": datetime.now().isoformat()
            }
            with open(self.failed_pdfs_file, 'w') as f:
                json.dump(failed_pdfs, f, indent=2)
        
        return False
    
    def remove_book_by_path(self, rel_path, skip_save=False):
        """Remove a book from the index by relative path"""
        if rel_path not in self.book_index:
            return
        
        try:
            # Delete from vector store
            book_name = os.path.basename(rel_path)
            collection = self.vectorstore._collection
            collection.delete(where={"book": book_name})
            
            # Remove from index
            del self.book_index[rel_path]
            if not skip_save:
                self.save_book_index()
            
            logger.info(f"Removed {rel_path} from index")
        except Exception as e:
            logger.error(f"Error removing {rel_path}: {str(e)}")
    
    def search(self, query, k=10, filter_type=None, synthesize=False):
        """Search the vector store with caching"""
        if not self.vectorstore:
            return []
        
        # Create cache key
        cache_key = f"{query}:{k}:{filter_type}"
        
        # Check cache
        if cache_key in self._search_cache:
            cached_result, timestamp = self._search_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result
        
        try:
            search_kwargs = {"k": min(k, self.vectorstore._collection.count() or 1)}
            if filter_type:
                search_kwargs["filter"] = {"type": filter_type}
            
            results = self.vectorstore.similarity_search_with_score(
                query, **search_kwargs
            )
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get('book', 'Unknown'),
                    "page": doc.metadata.get('page', 'Unknown'),
                    "type": doc.metadata.get('type', 'general'),
                    "relevance_score": float(score)
                })
            
            # Cache the results
            self._search_cache[cache_key] = (formatted_results, time.time())
            
            # Clean old cache entries if cache is getting large
            if len(self._search_cache) > 100:
                current_time = time.time()
                self._search_cache = {
                    k: v for k, v in self._search_cache.items()
                    if current_time - v[1] < self._cache_ttl
                }
            
            # Always return direct results (synthesis removed)
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def synthesize_results(self, query, context_chunks):
        """Stub method - synthesis now handled by Claude"""
        # This method is kept for backward compatibility but no longer used
        # Claude will synthesize the raw results directly
        return "Direct results provided - synthesis to be done by Claude for article writing."
    
    def get_stats(self):
        """Get library statistics"""
        stats = {
            "total_books": len(self.book_index),
            "total_chunks": 0,
            "categories": {},
            "failed_books": 0,
            "cleaned_books": 0,
            "indexing_status": self.get_indexing_status()
        }
        
        # Count chunks
        for info in self.book_index.values():
            stats["total_chunks"] += info.get("chunks", 0)
        
        # Get category breakdown from vector store
        try:
            if self.vectorstore:
                all_docs = self.vectorstore.get()
                if all_docs and 'metadatas' in all_docs:
                    for metadata in all_docs['metadatas']:
                        if 'type' in metadata:
                            cat_type = metadata['type']
                            stats['categories'][cat_type] = stats['categories'].get(cat_type, 0) + 1
        except:
            pass
        
        # Count failed/cleaned PDFs
        if os.path.exists(self.failed_pdfs_file):
            try:
                with open(self.failed_pdfs_file, 'r') as f:
                    failed_pdfs = json.load(f)
                    stats["failed_books"] = len(failed_pdfs)
                    stats["cleaned_books"] = len([f for f in failed_pdfs.values() if f.get("cleaned", False)])
            except:
                pass
        
        return stats