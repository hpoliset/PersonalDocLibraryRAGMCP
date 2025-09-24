#!/usr/bin/env python3
"""
Selective PDF indexing - index specific files or patterns
"""

import os
import sys
import argparse
from pathlib import Path

from personal_doc_library.core.shared_rag import SharedRAG

def find_matching_pdfs(pattern, books_dir):
    """Find PDFs matching a pattern"""
    matching_files = []
    
    for root, dirs, files in os.walk(books_dir):
        # Skip originals directory
        if "originals" in root:
            continue
            
        for file in files:
            if file.lower().endswith('.pdf'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, books_dir)
                
                # Check if pattern matches filename or relative path
                if pattern.lower() in file.lower() or pattern.lower() in rel_path.lower():
                    matching_files.append((filepath, rel_path))
    
    return matching_files

def main():
    parser = argparse.ArgumentParser(description='Index specific PDFs by name or pattern')
    parser.add_argument('pattern', help='Pattern to match (filename or path fragment)')
    parser.add_argument('--force', action='store_true', help='Force re-index even if already indexed')
    parser.add_argument('--list-only', action='store_true', help='List matching files without indexing')
    parser.add_argument('--timeout', type=int, default=15, help='Timeout per file in minutes (default: 15)')
    
    args = parser.parse_args()
    
    # Initialize SharedRAG
    rag = SharedRAG()
    
    # Find matching PDFs
    matching_files = find_matching_pdfs(args.pattern, rag.books_directory)
    
    if not matching_files:
        print(f"❌ No PDFs found matching pattern: '{args.pattern}'")
        return 1
    
    print(f"📁 Found {len(matching_files)} PDF(s) matching '{args.pattern}':")
    for i, (filepath, rel_path) in enumerate(matching_files, 1):
        status = "📄"
        if rel_path in rag.book_index:
            status = "✅" if not args.force else "🔄"
        print(f"  {i}. {status} {rel_path}")
    
    if args.list_only:
        print("\n💡 Use --force to re-index already indexed files")
        return 0
    
    # Filter files that need indexing
    files_to_index = []
    for filepath, rel_path in matching_files:
        if args.force or rel_path not in rag.book_index:
            files_to_index.append((filepath, rel_path))
        elif rel_path in rag.book_index:
            print(f"⏭️  Skipping {rel_path} (already indexed, use --force to re-index)")
    
    if not files_to_index:
        print("✅ All matching files are already indexed!")
        return 0
    
    print(f"\n🚀 Starting indexing of {len(files_to_index)} file(s)...")
    
    # Index the files
    success_count = 0
    for i, (filepath, rel_path) in enumerate(files_to_index, 1):
        print(f"\n[{i}/{len(files_to_index)}] Processing: {rel_path}")
        
        try:
            success = rag.process_pdf_with_timeout(filepath, rel_path, timeout_minutes=args.timeout)
            if success:
                success_count += 1
                print(f"✅ Successfully indexed: {rel_path}")
            else:
                print(f"❌ Failed to index: {rel_path}")
        except Exception as e:
            print(f"❌ Error indexing {rel_path}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Successfully indexed: {success_count}/{len(files_to_index)} files")
    print(f"   Failed: {len(files_to_index) - success_count} files")
    
    return 0 if success_count == len(files_to_index) else 1

if __name__ == "__main__":
    sys.exit(main())
