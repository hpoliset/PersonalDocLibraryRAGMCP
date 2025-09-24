#!/usr/bin/env python3
"""
Robust indexing script that handles both fresh and incremental indexing
"""

import sys
import os
import argparse
import logging
from datetime import datetime

from personal_doc_library.core.shared_rag import SharedRAG
from personal_doc_library.core.config import config

# Configure logging
log_directory = config.logs_directory
os.makedirs(log_directory, exist_ok=True)
log_filename = log_directory / f'indexing_{datetime.now():%Y%m%d_%H%M%S}.log'

# Set up both console and file logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler(log_filename)  # File output
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to {log_filename}")

def main():
    parser = argparse.ArgumentParser(description='Index spiritual library books')
    parser.add_argument('--fresh', action='store_true', help='Clear all data and start fresh')
    parser.add_argument('--retry-failed', action='store_true', help='Retry failed books')
    parser.add_argument('--max-workers', type=int, default=1, help='Number of parallel workers')
    args = parser.parse_args()
    
    print(f"\n🚀 Starting {'fresh' if args.fresh else 'incremental'} indexing...")
    
    # Initialize RAG system
    rag = SharedRAG()
    
    # Fresh indexing if requested
    if args.fresh:
        print("📄 Clearing all existing data for fresh start...")
        # TODO: Implement clear_all_data method
        # rag.clear_all_data()
        print("Note: clear_all_data not implemented yet")
    
    # Get current stats before indexing
    stats_before = rag.get_stats()
    print(f"\n📊 Current Library Status:")
    print(f"   Total books: {stats_before['total_books']}")
    # print(f"   Unique books: {stats_before['unique_books']}")
    print(f"   Failed books: {stats_before['failed_books']}")
    
    # Retry failed books if requested
    if args.retry_failed and not args.fresh:
        print(f"\n🔄 Clearing failed book records for retry...")
        # TODO: Implement failed_pdfs clearing
        print("Note: Retry failed not implemented yet")
    
    # Find PDFs to index
    pdfs_to_index = rag.find_new_or_modified_pdfs()
    
    if not pdfs_to_index:
        print("\n✅ All books are already indexed and up to date!")
        return
    
    print(f"\n📚 Found {len(pdfs_to_index)} books to index")
    
    # Acquire lock for indexing
    try:
        with rag.lock.acquire(blocking=False):
            print("🔒 Acquired indexing lock")
            
            # Process all PDFs
            success_count = 0
            failed_count = 0
            start_time = datetime.now()
            
            for i, (filepath, rel_path) in enumerate(pdfs_to_index, 1):
                # Get file size
                file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"\n[{i}/{len(pdfs_to_index)}] Processing: {rel_path} ({file_size_mb:.1f} MB)")
                
                # Log memory usage
                try:
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                    print(f"   Memory usage: {memory_mb:.0f} MB")
                except:
                    pass
                
                # Update status
                rag.update_status("indexing", {
                    "current_file": rel_path,
                    "progress": f"{i}/{len(pdfs_to_index)}",
                    "success": success_count,
                    "failed": failed_count,
                    "remaining": len(pdfs_to_index) - i
                })
                
                # Process PDF with timeout
                pdf_start_time = datetime.now()
                if rag.process_pdf_with_timeout(filepath, rel_path):
                    success_count += 1
                    pdf_time = (datetime.now() - pdf_start_time).total_seconds()
                    print(f"   ✅ Success: {rel_path} ({pdf_time:.1f}s)")
                else:
                    failed_count += 1
                    pdf_time = (datetime.now() - pdf_start_time).total_seconds()
                    print(f"   ❌ Failed: {rel_path} ({pdf_time:.1f}s)")
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Final status update
            rag.update_status("idle", {
                "last_run": datetime.now().isoformat(),
                "indexed": success_count,
                "failed": failed_count,
                "duration_seconds": duration
            })
            
            # Get final stats
            stats_after = rag.get_stats()
            
            print("\n" + "="*60)
            print("✅ Indexing Complete!")
            print("="*60)
            print(f"Duration: {duration:.1f} seconds")
            print(f"Books processed: {len(pdfs_to_index)}")
            print(f"Successful: {success_count}")
            print(f"Failed: {failed_count}")
            print(f"\nLibrary Statistics:")
            print(f"   Total books: {stats_after['total_books']} (+{stats_after['total_books'] - stats_before['total_books']})")
            # print(f"   Unique books: {stats_after['unique_books']}")
            # print(f"   Duplicate books: {stats_after['duplicate_books']}")
            print(f"   Total chunks: {stats_after['total_chunks']:,}")
            # print(f"   Total size: {stats_after['total_size_gb']} GB")
            
            if stats_after['failed_books'] > 0:
                print(f"\n⚠️  Failed books: {stats_after['failed_books']}")
                # print(f"   Books exceeding retry limit: {stats_after['retry_exceeded']}")
                print("   Run with --retry-failed to attempt again")
            
            print("\n📊 Categories:")
            for cat, count in stats_after['categories'].items():
                print(f"   {cat}: {count:,} chunks")
            
    except IOError as e:
        print(f"\n⚠️  Could not acquire lock: {e}")
        print("Another indexing process may be running.")
        print("Check with: ./service_status.sh")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Indexing interrupted by user")
        rag.update_status("idle", {"message": "Interrupted by user"})
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        rag.update_status("error", {"error": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()
