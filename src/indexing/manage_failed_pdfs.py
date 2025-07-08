#!/usr/bin/env python3
"""
Utility script for managing failed PDFs in the Spiritual Library
"""

import json
import os
import sys
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.shared_rag import SharedRAG
from src.core.config import config

def show_failed_pdfs():
    """Show detailed report of failed PDFs"""
    rag = SharedRAG()
    report = rag.get_failed_pdfs_report()
    
    print("=== Failed PDFs Report ===")
    print(f"Total failed: {report['total_failed']}")
    
    if report['total_failed'] == 0:
        print("✅ No failed PDFs!")
        return
    
    print("\n📊 By Error Type:")
    for error_type, pdfs in report['by_error_type'].items():
        print(f"  {error_type}: {len(pdfs)} files")
        for pdf in pdfs[:5]:  # Show first 5
            print(f"    - {pdf}")
        if len(pdfs) > 5:
            print(f"    ... and {len(pdfs) - 5} more")
    
    print("\n📋 Detailed Failed PDFs:")
    for pdf_name, info in report['failed_pdfs'].items():
        print(f"\n📄 {pdf_name}")
        print(f"   Error: {info.get('error', 'Unknown')}")
        print(f"   Failed at: {info.get('failed_at', 'Unknown')}")
        print(f"   Retry count: {info.get('retry_count', 0)}")
        print(f"   Size: {info.get('file_size', 0):,} bytes")
        print(f"   Path: {info.get('relative_path', 'Unknown')}")

def clear_failed_pdf(pdf_name):
    """Clear a specific PDF from the failed list"""
    rag = SharedRAG()
    if rag.clear_failed_pdf(pdf_name):
        print(f"✅ Cleared {pdf_name} from failed list")
    else:
        print(f"❌ Could not clear {pdf_name}")

def retry_failed_pdfs(max_retries=3, timeout_minutes=10):
    """Retry processing failed PDFs"""
    rag = SharedRAG()
    print(f"🔄 Retrying failed PDFs (max retries: {max_retries}, timeout: {timeout_minutes}min)")
    
    retried = rag.retry_failed_pdfs(max_retries=max_retries, timeout_minutes=timeout_minutes)
    
    if retried:
        print(f"✅ Successfully processed {len(retried)} PDFs:")
        for pdf in retried:
            print(f"  - {pdf}")
    else:
        print("❌ No PDFs were successfully processed")

def clear_all_failed():
    """Clear all failed PDFs from the list"""
    failed_pdfs_file = os.path.join(str(config.db_directory), "failed_pdfs.json")
    
    if os.path.exists(failed_pdfs_file):
        os.remove(failed_pdfs_file)
        print("✅ Cleared all failed PDFs from the list")
    else:
        print("ℹ️  No failed PDFs file found")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_failed_pdfs.py show              # Show failed PDFs report")
        print("  python manage_failed_pdfs.py clear <pdf_name>  # Clear specific PDF")
        print("  python manage_failed_pdfs.py retry             # Retry failed PDFs")
        print("  python manage_failed_pdfs.py clear_all         # Clear all failed PDFs")
        return
    
    command = sys.argv[1]
    
    if command == "show":
        show_failed_pdfs()
    elif command == "clear" and len(sys.argv) > 2:
        clear_failed_pdf(sys.argv[2])
    elif command == "retry":
        timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        retry_failed_pdfs(timeout_minutes=timeout)
    elif command == "clear_all":
        clear_all_failed()
    else:
        print("❌ Invalid command")

if __name__ == "__main__":
    main()