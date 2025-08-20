#!/usr/bin/env python3
"""
Background Index Monitor for Personal Document Library
Watches for changes and automatically indexes new/modified PDFs
"""

import os
import sys
import signal
import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import resource
import psutil
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.shared_rag import SharedRAG, IndexLock
from src.core.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BookLibraryHandler(FileSystemEventHandler):
    """Handles file system events for the books directory"""
    def __init__(self, monitor):
        self.monitor = monitor
        self.pending_updates = set()
        self.update_lock = threading.Lock()
    
    def on_created(self, event):
        if event.is_directory:
            # New directory created - scan for all documents inside
            logger.info(f"New directory detected: {event.src_path}")
            self.scan_directory_for_documents(event.src_path)
        elif event.src_path.lower().endswith(('.pdf', '.docx', '.doc', '.epub', '.pptx', '.ppt')):
            logger.info(f"New document detected: {event.src_path}")
            with self.update_lock:
                self.pending_updates.add(event.src_path)
            self.monitor.schedule_update()
    
    def on_modified(self, event):
        if event.is_directory:
            # Directory modified - might contain new files, scan contents
            logger.info(f"Directory modified: {event.src_path}")
            self.scan_directory_for_documents(event.src_path)
        elif event.src_path.lower().endswith(('.pdf', '.docx', '.doc', '.epub', '.pptx', '.ppt')):
            logger.info(f"Document modified: {event.src_path}")
            with self.update_lock:
                self.pending_updates.add(event.src_path)
            self.monitor.schedule_update()
    
    def scan_directory_for_documents(self, directory_path):
        """Scan a directory for all supported documents and add them to pending updates"""
        try:
            supported_extensions = ('.pdf', '.docx', '.doc', '.epub', '.pptx', '.ppt')
            found_files = []
            
            # Walk through the directory and find all supported files
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.lower().endswith(supported_extensions):
                        filepath = os.path.join(root, file)
                        found_files.append(filepath)
            
            if found_files:
                logger.info(f"Found {len(found_files)} documents in directory: {directory_path}")
                with self.update_lock:
                    for filepath in found_files:
                        self.pending_updates.add(filepath)
                self.monitor.schedule_update()
                
        except Exception as e:
            logger.warning(f"Error scanning directory {directory_path}: {e}")
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.pdf', '.docx', '.doc', '.epub', '.pptx', '.ppt')):
            logger.info(f"Document removed: {event.src_path}")
            self.monitor.handle_deletion(event.src_path)
    
    def get_pending_updates(self):
        with self.update_lock:
            updates = list(self.pending_updates)
            self.pending_updates.clear()
            return updates
    
    def get_pending_count(self):
        """Get count of pending updates without clearing"""
        with self.update_lock:
            return len(self.pending_updates)

class IndexMonitor:
    """Background monitor that watches and indexes books"""
    
    SERVICE_MODE = False  # Class variable for service mode
    
    def __init__(self, books_directory=None, db_directory=None):
        # Debug: Log environment variables
        logger.info(f"Environment - PERSONAL_LIBRARY_DOC_PATH: {os.getenv('PERSONAL_LIBRARY_DOC_PATH', 'NOT SET')}")
        logger.info(f"Environment - PERSONAL_LIBRARY_DB_PATH: {os.getenv('PERSONAL_LIBRARY_DB_PATH', 'NOT SET')}")
        
        # Use config system if no explicit paths provided
        if books_directory is not None:
            logger.info(f"Using explicit books_directory: {books_directory}")
            self.books_directory = books_directory
        else:
            # Read environment variable directly if available
            env_books_path = os.getenv('PERSONAL_LIBRARY_DOC_PATH')
            logger.info(f"Environment variable PERSONAL_LIBRARY_DOC_PATH: {env_books_path}")
            if env_books_path:
                logger.info(f"Using environment variable for books_directory: {env_books_path}")
                self.books_directory = env_books_path
            else:
                logger.info(f"Falling back to config.books_directory: {config.books_directory}")
                self.books_directory = str(config.books_directory)
            
        if db_directory is not None:
            self.db_directory = db_directory
        else:
            # Read environment variable directly if available
            env_db_path = os.getenv('PERSONAL_LIBRARY_DB_PATH')
            if env_db_path:
                self.db_directory = env_db_path
            else:
                self.db_directory = str(config.db_directory)
        
        # Debug: Log what config system resolved
        logger.info(f"Config resolved - Books: {self.books_directory}")
        logger.info(f"Config resolved - DB: {self.db_directory}")
        
        # Pass the resolved paths to SharedRAG
        self.rag = SharedRAG(self.books_directory, self.db_directory)
        self.update_timer = None
        self.update_lock = threading.Lock()
        self.observer = None
        self.running = False
        self.pause_file = "/tmp/spiritual_library_index.pause"
        self.total_documents_to_process = 0
        self.current_document_index = 0
        
        # File descriptor management
        self.max_file_descriptors = self._get_safe_fd_limit()
        self.fd_reserve = 100  # Reserve 100 FDs for system operations
        logger.info(f"File descriptor limit: {self.max_file_descriptors}, reserving {self.fd_reserve} for system")
        
        # Adjust delays for service mode
        self.retry_delay = 5.0 if self.SERVICE_MODE else 2.0
        self.batch_delay = 5.0 if self.SERVICE_MODE else 2.0
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal, stopping monitor...")
        self.stop()
        sys.exit(0)
    
    def _get_safe_fd_limit(self):
        """Get a safe file descriptor limit for the system"""
        try:
            # Get current soft and hard limits
            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            
            # Try to increase soft limit to a reasonable value
            target_limit = min(4096, hard_limit)
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, (target_limit, hard_limit))
                logger.info(f"Set file descriptor limit to {target_limit}")
                return target_limit
            except:
                logger.info(f"Using current file descriptor limit: {soft_limit}")
                return soft_limit
        except Exception as e:
            logger.warning(f"Could not determine file descriptor limit: {e}, using default 256")
            return 256
    
    def _get_current_fd_usage(self):
        """Get current file descriptor usage for this process"""
        try:
            process = psutil.Process()
            return len(process.open_files())
        except:
            # Fallback: count open file descriptors in /proc/self/fd (Linux/Mac)
            try:
                if os.path.exists('/proc/self/fd'):
                    return len(os.listdir('/proc/self/fd'))
                else:
                    # macOS fallback
                    import subprocess
                    result = subprocess.run(['lsof', '-p', str(os.getpid())], 
                                         capture_output=True, text=True)
                    return len(result.stdout.splitlines()) - 1  # Subtract header
            except:
                return 50  # Conservative estimate if we can't determine
    
    def _calculate_safe_workers(self, base_workers=5):
        """Calculate safe number of workers based on available file descriptors"""
        current_fds = self._get_current_fd_usage()
        available_fds = self.max_file_descriptors - current_fds - self.fd_reserve
        
        # Each worker might use ~20-50 file descriptors (PDF processing, temp files, etc)
        fds_per_worker = 50
        max_workers_by_fds = max(1, available_fds // fds_per_worker)
        
        # Also consider memory
        try:
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            max_workers_by_memory = max(1, int(available_memory_gb // 2))  # 2GB per worker
        except:
            max_workers_by_memory = base_workers
        
        # Take the minimum of all constraints
        safe_workers = min(base_workers, max_workers_by_fds, max_workers_by_memory)
        
        logger.info(f"FD usage: {current_fds}/{self.max_file_descriptors}, "
                   f"Available FDs: {available_fds}, "
                   f"Safe workers: {safe_workers} (FD limit: {max_workers_by_fds}, "
                   f"Memory limit: {max_workers_by_memory})")
        
        return safe_workers
    
    def is_paused(self):
        """Check if indexing is paused"""
        return os.path.exists(self.pause_file)
    
    def wait_if_paused(self):
        """Wait while paused, checking periodically"""
        if self.is_paused():
            logger.info("Indexing is paused. Waiting for resume...")
            self.rag.update_status("paused", {
                "message": "Indexing paused by user",
                "queued_files": self.event_handler.get_pending_count() if self.event_handler else 0
            })
            
            while self.is_paused() and self.running:
                time.sleep(5)  # Check every 5 seconds
                
            if self.running:
                logger.info("Indexing resumed")
                self.rag.update_status("resuming", {
                    "message": "Indexing resumed"
                })
    
    def start(self):
        """Start the monitoring service"""
        logger.info("Starting Personal Document Library Index Monitor")
        logger.info(f"Watching directory: {self.books_directory}")
        
        # Set running flag before initial sync
        self.running = True
        
        # Initial sync
        self.initial_sync()
        
        # Set up file monitoring
        self.setup_file_monitor()
        
        # Start progress monitoring thread for PDF extraction
        logger.info("About to start progress monitor thread...")
        try:
            if hasattr(self, 'start_progress_monitor'):
                self.start_progress_monitor()
            else:
                logger.error("start_progress_monitor method not found!")
        except Exception as e:
            logger.error(f"Failed to start progress monitor: {e}", exc_info=True)
        
        logger.info("Monitor is running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the monitoring service"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Stop progress monitor thread
        if hasattr(self, 'progress_monitor_thread'):
            self.progress_monitor_running = False
            self.progress_monitor_thread.join(timeout=2)
        
        # Cancel any pending updates
        with self.update_lock:
            if self.update_timer:
                self.update_timer.cancel()
        
        # Update status
        self.rag.update_status("stopped", {"message": "Monitor stopped"})
        logger.info("Monitor stopped")
    
    def setup_file_monitor(self):
        """Set up the file system monitor"""
        self.event_handler = BookLibraryHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.books_directory, recursive=True)
        self.observer.start()
        logger.info("File monitoring activated")
    
    def initial_sync(self):
        """Perform initial synchronization"""
        logger.info("Performing initial synchronization...")
        
        # Debug: Check book index state
        logger.info(f"Current book index has {len(self.rag.book_index)} entries")
        logger.info(f"Books directory: {self.books_directory}")
        logger.info(f"Books directory exists: {os.path.exists(self.books_directory)}")
        
        # Find new or modified documents
        documents_to_index = self.rag.find_new_or_modified_documents()
        logger.info(f"find_new_or_modified_documents returned {len(documents_to_index)} documents")
        
        if documents_to_index:
            logger.info(f"Found {len(documents_to_index)} documents to index")
            self.process_documents(documents_to_index)
        else:
            logger.info("All documents are up to date")
        
        # Clean up removed documents
        self.cleanup_removed_documents()
    
    def cleanup_removed_documents(self):
        """Remove index entries for documents that no longer exist"""
        removed_count = 0
        for rel_path in list(self.rag.book_index.keys()):
            full_path = os.path.join(self.books_directory, rel_path)
            if not os.path.exists(full_path):
                logger.info(f"Removing deleted book from index: {rel_path}")
                self.rag.remove_book_by_path(rel_path)
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} deleted books from index")
    
    def schedule_update(self):
        """Schedule a batch update after a short delay"""
        with self.update_lock:
            if self.update_timer:
                self.update_timer.cancel()
            self.update_timer = threading.Timer(self.batch_delay, self.process_pending_updates)
            self.update_timer.start()
    
    def process_pending_updates(self):
        """Process all pending book updates"""
        updates = self.event_handler.get_pending_updates()
        if not updates:
            return
        
        logger.info(f"Processing {len(updates)} pending file updates")
        
        # Use the full document discovery mechanism to ensure we don't miss any files
        # This is especially important when directories are copied with old timestamps
        all_documents_to_index = self.rag.find_new_or_modified_documents()
        
        if all_documents_to_index:
            logger.info(f"Full scan found {len(all_documents_to_index)} documents to index")
            self.process_documents(all_documents_to_index)
        else:
            logger.info("No new documents found to index")
    
    def process_documents(self, documents_to_index):
        """Process a list of documents with proper locking"""
        try:
            with self.rag.lock.acquire(blocking=False):
                logger.info(f"Starting to index {len(documents_to_index)} documents")
                logger.info(f"self.running = {self.running}")
                
                # Store total for progress tracking
                self.total_documents_to_process = len(documents_to_index)
                success_count = 0
                failed_count = 0
                
                # Set initial progress status
                self.rag.update_status("indexing", {
                    "progress": f"0/{len(documents_to_index)}",
                    "success": 0,
                    "failed": 0,
                    "percentage": 0,
                    "message": "Starting indexing..."
                })
                
                logger.info(f"About to process {len(documents_to_index)} documents")
                
                # Import required modules for parallel processing
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import multiprocessing
                import threading
                import psutil
                
                # Thread-safe counters
                success_lock = threading.Lock()
                failed_lock = threading.Lock()
                progress_lock = threading.Lock()
                
                # Separate large files from regular files
                large_files = []
                regular_files = []
                
                for filepath, rel_path in documents_to_index:
                    try:
                        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
                        if file_size_mb > 100:  # Files over 100MB
                            large_files.append((filepath, rel_path))
                        else:
                            regular_files.append((filepath, rel_path))
                    except:
                        regular_files.append((filepath, rel_path))  # If we can't check size, treat as regular
                
                logger.info(f"Found {len(large_files)} large files (>100MB) and {len(regular_files)} regular files")
                
                # Process large files first, sequentially
                if large_files:
                    logger.info("Processing large files sequentially to prevent memory issues...")
                    for i, (filepath, rel_path) in enumerate(large_files, 1):
                        if not self.running:
                            break
                        
                        self.wait_if_paused()
                        
                        logger.info(f"Processing large file {i}/{len(large_files)}: {rel_path}")
                        
                        # Check if file is in failed list
                        if self.rag.is_document_failed(rel_path):
                            logger.info(f"Skipping previously failed file: {rel_path}")
                            failed_count += 1
                            self.current_document_index += 1
                            continue
                        
                        # Process large file with timeout
                        result = self.rag.process_document_with_timeout(filepath, rel_path)
                        
                        if result:
                            success_count += 1
                            logger.info(f"Successfully processed large file: {rel_path}")
                        else:
                            failed_count += 1
                            logger.warning(f"Failed to process large file: {rel_path}")
                        
                        self.current_document_index += 1
                        
                        # Update status
                        self.rag.update_status("indexing", {
                            "current_file": rel_path,
                            "progress": f"{self.current_document_index}/{len(documents_to_index)}",
                            "success": success_count,
                            "failed": failed_count,
                            "percentage": round(self.current_document_index / len(documents_to_index) * 100, 1),
                            "processing_mode": "sequential_large_file"
                        })
                
                # Now process regular files in parallel
                if regular_files and self.running:
                    # Determine optimal worker count based on system resources
                    cpu_count = multiprocessing.cpu_count()
                    # Get available memory in GB
                    available_memory_gb = psutil.virtual_memory().available / (1024**3)
                    
                    # Use dynamic worker calculation based on file descriptors and memory
                    base_workers = min(
                        max(1, cpu_count // 2),  # Half the CPU cores
                        5  # Max 5 workers as base
                    )
                    max_workers = self._calculate_safe_workers(base_workers)
                    
                    logger.info(f"Processing regular files with {max_workers} parallel workers (CPUs: {cpu_count}, Available RAM: {available_memory_gb:.1f}GB)")
                
                def process_single_document(doc_info):
                    """Process a single document with thread-safe progress tracking"""
                    nonlocal success_count, failed_count
                    
                    filepath, rel_path, index = doc_info
                    
                    # Check if paused before processing
                    self.wait_if_paused()
                    
                    # Check if still running after pause
                    if not self.running:
                        return None
                    
                    logger.info(f"Processing document {index}/{len(documents_to_index)}: {rel_path}")
                    
                    # Check if file is in failed list before processing
                    if self.rag.is_document_failed(rel_path):
                        logger.info(f"Skipping previously failed file: {rel_path}")
                        
                        with failed_lock:
                            failed_count += 1
                        
                        with progress_lock:
                            self.current_document_index = max(self.current_document_index, index)
                            # Update status to show we're skipping this file
                            self.rag.update_status("indexing", {
                                "current_file": f"Skipping failed: {rel_path}",
                                "progress": f"{self.current_document_index}/{len(documents_to_index)}",
                                "success": success_count,
                                "failed": failed_count,
                                "percentage": round(self.current_document_index / len(documents_to_index) * 100, 1)
                            })
                        return False
                    
                    # Process document with timeout
                    result = self.rag.process_document_with_timeout(filepath, rel_path)
                    
                    # Update counters thread-safely
                    if result:
                        with success_lock:
                            success_count += 1
                        logger.info(f"Successfully processed: {rel_path}")
                    else:
                        with failed_lock:
                            failed_count += 1
                        logger.warning(f"Failed to process: {rel_path}")
                    
                    # Update progress
                    with progress_lock:
                        self.current_document_index = max(self.current_document_index, index)
                        self.rag.update_status("indexing", {
                            "current_file": rel_path,
                            "progress": f"{self.current_document_index}/{len(documents_to_index)}",
                            "success": success_count,
                            "failed": failed_count,
                            "percentage": round(self.current_document_index / len(documents_to_index) * 100, 1),
                            "parallel_workers": max_workers
                        })
                    
                    return result
                
                # Process regular documents in parallel with dynamic worker adjustment
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Prepare document info with indices, adjusting for already processed large files
                        doc_infos = [(filepath, rel_path, self.current_document_index + i) 
                                   for i, (filepath, rel_path) in enumerate(regular_files, 1)]
                        
                        # Submit tasks in batches to control file descriptor usage
                        batch_size = max_workers * 2  # Process 2x workers at a time
                        processed_docs = 0
                        
                        for batch_start in range(0, len(doc_infos), batch_size):
                            batch_end = min(batch_start + batch_size, len(doc_infos))
                            batch = doc_infos[batch_start:batch_end]
                            
                            # Check file descriptors before each batch
                            current_fds = self._get_current_fd_usage()
                            if current_fds > self.max_file_descriptors - self.fd_reserve:
                                logger.warning(f"High FD usage ({current_fds}/{self.max_file_descriptors}), waiting for cleanup...")
                                time.sleep(5)  # Wait for cleanup
                                
                                # Recalculate workers if needed
                                new_max_workers = self._calculate_safe_workers(base_workers)
                                if new_max_workers < max_workers:
                                    logger.info(f"Reducing workers from {max_workers} to {new_max_workers} due to FD pressure")
                                    executor._max_workers = new_max_workers
                                    max_workers = new_max_workers
                            
                            # Submit batch
                            futures = {executor.submit(process_single_document, doc_info): doc_info 
                                     for doc_info in batch}
                            
                            # Process completed futures for this batch
                            for future in as_completed(futures):
                                if not self.running:
                                    # Cancel remaining futures if stopped
                                    for f in futures:
                                        f.cancel()
                                    break
                                
                                try:
                                    result = future.result()
                                    processed_docs += 1
                                    
                                    # Periodic FD check every 10 documents
                                    if processed_docs % 10 == 0:
                                        current_fds = self._get_current_fd_usage()
                                        if current_fds > self.max_file_descriptors * 0.8:
                                            logger.warning(f"FD usage at {current_fds}/{self.max_file_descriptors} (80%), forcing garbage collection")
                                            import gc
                                            gc.collect()
                                            time.sleep(1)  # Brief pause for cleanup
                                            
                                except Exception as e:
                                    logger.error(f"Error processing document: {e}")
                                    with failed_lock:
                                        failed_count += 1
                            
                            if not self.running:
                                break
                
                # Final status update
                self.rag.update_status("idle", {
                    "last_run": datetime.now().isoformat(),
                    "indexed": success_count,
                    "failed": failed_count,
                    "total_processed": self.current_document_index
                })
                
                logger.info(f"Indexing complete: {success_count} succeeded, {failed_count} failed")
                
                # Reset progress tracking
                self.total_documents_to_process = 0
                self.current_document_index = 0
                
        except IOError:
            logger.warning("Could not acquire lock - another process may be indexing")
            # Schedule retry
            self.schedule_update()
    
    def handle_deletion(self, filepath):
        """Handle deletion of a document"""
        rel_path = os.path.relpath(filepath, self.books_directory)
        
        try:
            with self.rag.lock.acquire(blocking=False):
                self.rag.remove_book_by_path(rel_path)
                self.rag.update_status("idle", {
                    "last_action": "removed",
                    "removed_file": rel_path,
                    "timestamp": datetime.now().isoformat()
                })
        except IOError:
            logger.warning("Could not acquire lock for deletion")
    
    def start_progress_monitor(self):
        """Start a background thread to monitor PDF extraction progress from logs"""
        self.progress_monitor_running = True
        self.progress_monitor_thread = threading.Thread(target=self.monitor_pdf_progress, daemon=True)
        self.progress_monitor_thread.start()
        logger.info("Started PDF progress monitoring thread")
    
    def monitor_pdf_progress(self):
        """Monitor stderr logs for PDF page extraction progress and update progress file"""
        import re
        import json
        import subprocess
        
        logger.info("Progress monitor thread started")
        log_file = os.path.join(config.logs_directory, 'index_monitor_stderr.log')
        progress_file = os.path.join(self.db_directory, 'indexing_progress.json')
        logger.info(f"Monitoring log file: {log_file}")
        logger.info(f"Updating progress file: {progress_file}")
        
        while self.progress_monitor_running:
            try:
                # Check if we're currently indexing
                if not os.path.exists(progress_file):
                    time.sleep(5)
                    continue
                
                # Read current progress file to see if we're in loading/extracting stage
                with open(progress_file, 'r') as f:
                    progress_data = json.load(f)
                
                current_stage = progress_data.get('stage', '')
                if current_stage not in ['loading', 'extracting']:
                    time.sleep(5)
                    continue
                
                # Get the latest page number from stderr logs
                if os.path.exists(log_file):
                    try:
                        result = subprocess.run(
                            ['tail', '-100', log_file],
                            capture_output=True, text=True, timeout=2
                        )
                        
                        # Find all page numbers in recent logs
                        matches = re.findall(r'page (\d+)', result.stdout)
                        if matches:
                            latest_page = max(int(m) for m in matches)
                            
                            # Check if this is a PDF file
                            current_file = progress_data.get('current_file', '')
                            if current_file.lower().endswith('.pdf'):
                                # Get total pages from log if available
                                total_matches = re.findall(r'PDF has (\d+) pages', result.stdout)
                                total_pages = int(total_matches[-1]) if total_matches else progress_data.get('total_pages')
                                
                                # Update progress file with actual page number
                                progress_data['current_page'] = latest_page
                                if total_pages:
                                    progress_data['total_pages'] = total_pages
                                progress_data['stage'] = 'extracting'
                                progress_data['timestamp'] = datetime.now().isoformat()
                                
                                with open(progress_file, 'w') as f:
                                    json.dump(progress_data, f, indent=2)
                    except subprocess.TimeoutExpired:
                        pass
                    except Exception as e:
                        logger.debug(f"Error parsing logs: {e}")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.debug(f"Progress monitor error: {e}")
                time.sleep(10)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Personal Document Library Index Monitor')
    parser.add_argument('--books-dir', default=None, 
                      help='Directory containing document library (PDFs, Word docs, EPUBs)')
    parser.add_argument('--db-dir', default=None,
                      help='Directory for database storage')
    parser.add_argument('--daemon', action='store_true',
                      help='Run as daemon (background process)')
    parser.add_argument('--service', action='store_true',
                      help='Run in service mode (longer delays, lower priority)')
    
    args = parser.parse_args()
    
    # Create directories if needed (use config defaults if not specified)
    books_dir = args.books_dir if args.books_dir is not None else str(config.books_directory)
    db_dir = args.db_dir if args.db_dir is not None else str(config.db_directory)
    os.makedirs(books_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)
    
    # Configure for service mode
    if args.service:
        logger.info("Running in service mode (LaunchAgent)")
        # In service mode, use longer delays and lower priority
        IndexMonitor.SERVICE_MODE = True
    
    if args.daemon:
        # Fork to background
        import daemon
        with daemon.DaemonContext():
            monitor = IndexMonitor(args.books_dir, args.db_dir)
            monitor.start()
    else:
        # Run in foreground
        monitor = IndexMonitor(args.books_dir, args.db_dir)
        monitor.start()

if __name__ == "__main__":
    main()