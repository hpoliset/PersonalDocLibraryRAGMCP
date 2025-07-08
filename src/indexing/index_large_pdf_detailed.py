#!/usr/bin/env python3
"""
Detailed Large PDF Indexing - Enhanced logging for monitoring single large documents
"""

import os
import sys
import time
import psutil
import logging
from datetime import datetime
from pathlib import Path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.shared_rag import SharedRAG

# Setup detailed logging
def setup_detailed_logging():
    log_format = '%(asctime)s | %(levelname)-8s | %(message)s'
    
    # Console handler with detailed format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    # File handler for persistent logs
    log_file = Path("large_pdf_indexing.log")
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def monitor_system_resources():
    """Monitor and log system resources"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    cpu_percent = process.cpu_percent()
    
    # System memory
    sys_memory = psutil.virtual_memory()
    sys_memory_gb = sys_memory.total / (1024**3)
    sys_memory_used_gb = sys_memory.used / (1024**3)
    sys_memory_percent = sys_memory.percent
    
    logging.info(f"🖥️  SYSTEM RESOURCES:")
    logging.info(f"   💾 Process Memory: {memory_mb:.1f}MB")
    logging.info(f"   🖥️  System Memory: {sys_memory_used_gb:.1f}GB / {sys_memory_gb:.1f}GB ({sys_memory_percent:.1f}%)")
    logging.info(f"   ⚡ CPU Usage: {cpu_percent:.1f}%")
    
    return memory_mb

def monitor_progress_file():
    """Monitor the progress file for detailed stage tracking"""
    progress_file = Path("chroma_db/indexing_progress.json")
    if progress_file.exists():
        try:
            import json
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            stage = progress.get('stage', 'unknown')
            current_page = progress.get('current_page')
            total_pages = progress.get('total_pages')
            chunks_generated = progress.get('chunks_generated')
            memory_mb = progress.get('memory_mb', 0)
            current_file = progress.get('current_file', 'unknown')
            
            logging.info(f"📊 PROGRESS DETAILS:")
            logging.info(f"   📄 File: {current_file}")
            logging.info(f"   🔄 Stage: {stage.upper()}")
            if current_page and total_pages:
                logging.info(f"   📖 Pages: {current_page}/{total_pages} ({(current_page/total_pages*100):.1f}%)")
            if chunks_generated:
                logging.info(f"   🧩 Chunks Generated: {chunks_generated}")
            logging.info(f"   💾 Process Memory: {memory_mb:.1f}MB")
            
        except Exception as e:
            logging.warning(f"Could not read progress file: {e}")

def main():
    # Setup logging
    logger = setup_detailed_logging()
    
    logging.info("🚀 STARTING DETAILED LARGE PDF INDEXING")
    logging.info("="*60)
    
    # Target the specific large PDF
    pdf_pattern = "whispers vol 6"
    timeout_minutes = 60  # 1 hour
    
    logging.info(f"🎯 TARGET: {pdf_pattern}")
    logging.info(f"⏱️  TIMEOUT: {timeout_minutes} minutes")
    logging.info(f"📝 LOG FILE: large_pdf_indexing.log")
    logging.info("")
    
    try:
        # Initialize SharedRAG with detailed logging
        logging.info("🔧 INITIALIZING SHARED RAG SYSTEM...")
        start_time = time.time()
        
        rag = SharedRAG()
        
        init_time = time.time() - start_time
        logging.info(f"✅ SharedRAG initialized in {init_time:.2f} seconds")
        
        # Find the target PDF
        logging.info(f"🔍 SEARCHING FOR PDF: '{pdf_pattern}'")
        matching_files = []
        
        for root, dirs, files in os.walk(rag.books_directory):
            if "originals" in root:
                continue
                
            for file in files:
                if file.lower().endswith('.pdf'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, rag.books_directory)
                    
                    if pdf_pattern.lower() in file.lower() or pdf_pattern.lower() in rel_path.lower():
                        matching_files.append((filepath, rel_path))
        
        if not matching_files:
            logging.error(f"❌ NO MATCHING PDFs FOUND for pattern: '{pdf_pattern}'")
            return 1
        
        # Process each matching file
        for filepath, rel_path in matching_files:
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            logging.info("")
            logging.info("📄 TARGET PDF DETAILS:")
            logging.info(f"   📁 Path: {rel_path}")
            logging.info(f"   📏 Size: {file_size_mb:.1f}MB")
            logging.info(f"   🔧 Timeout: {timeout_minutes} minutes")
            logging.info("")
            
            # Monitor initial resources
            logging.info("🔍 PRE-PROCESSING SYSTEM STATE:")
            monitor_system_resources()
            logging.info("")
            
            # Start processing
            logging.info("🚀 STARTING PDF PROCESSING...")
            processing_start = time.time()
            
            # Create a monitoring thread to track progress
            import threading
            import signal
            
            stop_monitoring = threading.Event()
            
            def progress_monitor():
                """Background thread to monitor progress"""
                while not stop_monitoring.is_set():
                    try:
                        logging.info("")
                        logging.info("⏱️  PROGRESS CHECK:")
                        monitor_progress_file()
                        monitor_system_resources()
                        logging.info("")
                    except Exception as e:
                        logging.error(f"Error in progress monitor: {e}")
                    
                    # Wait 30 seconds before next check
                    stop_monitoring.wait(30)
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=progress_monitor)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            try:
                # Process the PDF with timeout
                success = rag.process_pdf_with_timeout(filepath, rel_path, timeout_minutes=timeout_minutes)
                
                # Stop monitoring
                stop_monitoring.set()
                monitor_thread.join(timeout=1)
                
                processing_time = time.time() - processing_start
                
                logging.info("")
                logging.info("📊 PROCESSING RESULTS:")
                logging.info(f"   ⏱️  Total Time: {processing_time:.2f} seconds ({processing_time/60:.1f} minutes)")
                
                if success:
                    logging.info(f"   ✅ STATUS: SUCCESS")
                    
                    # Check final stats
                    if rel_path in rag.book_index:
                        book_info = rag.book_index[rel_path]
                        chunks = book_info.get('chunks', 0)
                        pages = book_info.get('pages', 0)
                        logging.info(f"   📄 Pages Indexed: {pages}")
                        logging.info(f"   🧩 Chunks Created: {chunks}")
                        logging.info(f"   📈 Chunks per Page: {chunks/pages:.1f}" if pages > 0 else "   📈 Chunks per Page: N/A")
                else:
                    logging.error(f"   ❌ STATUS: FAILED")
                
                # Final resource check
                logging.info("")
                logging.info("🔍 POST-PROCESSING SYSTEM STATE:")
                final_memory = monitor_system_resources()
                
                logging.info("")
                logging.info("="*60)
                logging.info("✅ DETAILED INDEXING COMPLETE")
                
                return 0 if success else 1
                
            except KeyboardInterrupt:
                logging.warning("⚠️  INTERRUPTED BY USER")
                stop_monitoring.set()
                return 130
            except Exception as e:
                logging.error(f"❌ PROCESSING ERROR: {e}")
                stop_monitoring.set()
                return 1
                
    except Exception as e:
        logging.error(f"❌ INITIALIZATION ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())