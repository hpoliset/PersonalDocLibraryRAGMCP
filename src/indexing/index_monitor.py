#!/usr/bin/env python3
"""
Background Index Monitor for Spiritual Library
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
        if not event.is_directory and event.src_path.lower().endswith(('.pdf', '.docx', '.doc', '.epub')):
            logger.info(f"New document detected: {event.src_path}")
            with self.update_lock:
                self.pending_updates.add(event.src_path)
            self.monitor.schedule_update()
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.pdf', '.docx', '.doc', '.epub')):
            logger.info(f"Document modified: {event.src_path}")
            with self.update_lock:
                self.pending_updates.add(event.src_path)
            self.monitor.schedule_update()
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.pdf', '.docx', '.doc', '.epub')):
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
        logger.info(f"Environment - SPIRITUAL_LIBRARY_BOOKS_PATH: {os.getenv('SPIRITUAL_LIBRARY_BOOKS_PATH', 'NOT SET')}")
        logger.info(f"Environment - SPIRITUAL_LIBRARY_DB_PATH: {os.getenv('SPIRITUAL_LIBRARY_DB_PATH', 'NOT SET')}")
        
        # Use config system if no explicit paths provided
        if books_directory is not None:
            logger.info(f"Using explicit books_directory: {books_directory}")
            self.books_directory = books_directory
        else:
            # Read environment variable directly if available
            env_books_path = os.getenv('SPIRITUAL_LIBRARY_BOOKS_PATH')
            logger.info(f"Environment variable SPIRITUAL_LIBRARY_BOOKS_PATH: {env_books_path}")
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
            env_db_path = os.getenv('SPIRITUAL_LIBRARY_DB_PATH')
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
        logger.info("Starting Spiritual Library Index Monitor")
        logger.info(f"Watching directory: {self.books_directory}")
        
        # Set running flag before initial sync
        self.running = True
        
        # Initial sync
        self.initial_sync()
        
        # Set up file monitoring
        self.setup_file_monitor()
        
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
        
        documents_to_index = []
        for filepath in updates:
            if os.path.exists(filepath):
                rel_path = os.path.relpath(filepath, self.books_directory)
                documents_to_index.append((filepath, rel_path))
        
        if documents_to_index:
            self.process_documents(documents_to_index)
    
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
                
                logger.info(f"About to process {len(documents_to_index)} documents")
                for i, (filepath, rel_path) in enumerate(documents_to_index, 1):
                    # Check if paused before processing each document
                    self.wait_if_paused()
                    
                    # Check if still running after pause
                    if not self.running:
                        break
                    
                    # Update current index for progress tracking
                    self.current_document_index = i
                    
                    logger.info(f"Processing document {i}/{len(documents_to_index)}: {rel_path}")
                    
                    # Process document with timeout
                    result = self.rag.process_document_with_timeout(filepath, rel_path)
                    
                    # Update status with progress AFTER processing starts
                    self.rag.update_status("indexing", {
                        "current_file": rel_path,
                        "progress": f"{i}/{len(documents_to_index)}",
                        "success": success_count,
                        "failed": failed_count,
                        "percentage": round((i-1) / len(documents_to_index) * 100, 1)
                    })
                    
                    if result:
                        success_count += 1
                        logger.info(f"Successfully processed: {rel_path}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to process: {rel_path}")
                
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

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Spiritual Library Index Monitor')
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