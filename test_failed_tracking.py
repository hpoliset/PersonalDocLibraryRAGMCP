#!/usr/bin/env python3
"""
Test script to verify failed document tracking fixes
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, '/Users/hpoliset/DocumentIndexerMCP/src')

from core.shared_rag import SharedRAG

def test_failed_tracking():
    """Test that failed documents are properly tracked with relative paths"""
    print("Testing Failed Document Tracking...")
    
    # Create a test RAG system
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db"
        books_dir = Path(tmpdir) / "books"
        db_dir.mkdir()
        books_dir.mkdir()
        
        # Create some test subdirectories
        (books_dir / "subfolder1").mkdir()
        (books_dir / "subfolder1" / "deep").mkdir()
        (books_dir / "subfolder2").mkdir()
        
        # Create test files with same names in different folders
        test_files = [
            books_dir / "test.pdf",
            books_dir / "subfolder1" / "test.pdf",
            books_dir / "subfolder1" / "deep" / "test.pdf",
            books_dir / "subfolder2" / "test.pdf",
        ]
        
        for file in test_files:
            file.write_text("dummy content")
        
        # Initialize RAG system
        rag = SharedRAG(
            db_directory=str(db_dir),
            books_directory=str(books_dir)
        )
        
        # Simulate failures for each file
        for file in test_files:
            rag.handle_failed_document(str(file), f"Test error for {file}")
        
        # Check the failed list
        failed_file = db_dir / "failed_pdfs.json"
        if failed_file.exists():
            with open(failed_file) as f:
                failed_docs = json.load(f)
            
            print(f"✓ Failed documents tracked: {len(failed_docs)}")
            
            # Verify all 4 files are tracked (not just 1 due to name collision)
            if len(failed_docs) == 4:
                print("✓ All documents with same name tracked separately")
            else:
                print(f"✗ Expected 4 failed docs, got {len(failed_docs)}")
                return False
            
            # Check that relative paths are used
            for key in failed_docs.keys():
                if not key.startswith("/"):  # Should be relative, not absolute
                    print(f"✓ Using relative path: {key}")
                else:
                    print(f"✗ Using absolute path: {key}")
                    return False
            
            # Verify full_path is stored
            for key, value in failed_docs.items():
                if "full_path" in value:
                    print(f"✓ Full path stored for: {key}")
                else:
                    print(f"✗ Missing full_path for: {key}")
                    return False
            
            return True
        else:
            print("✗ Failed documents file not created")
            return False

def test_remove_from_failed():
    """Test removing documents from failed list"""
    print("\nTesting Remove from Failed List...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_dir = Path(tmpdir) / "db"
        books_dir = Path(tmpdir) / "books"
        db_dir.mkdir()
        books_dir.mkdir()
        
        # Create test file
        test_file = books_dir / "subfolder" / "test.pdf"
        test_file.parent.mkdir()
        test_file.write_text("dummy")
        
        # Initialize RAG system
        rag = SharedRAG(
            db_directory=str(db_dir),
            books_directory=str(books_dir)
        )
        
        # Add to failed list
        rag.handle_failed_document(str(test_file), "Test error")
        
        # Try to remove it
        rel_path = "subfolder/test.pdf"
        rag.remove_from_failed_list(rel_path)
        
        # Check if removed
        failed_file = db_dir / "failed_pdfs.json"
        if failed_file.exists():
            with open(failed_file) as f:
                failed_docs = json.load(f)
            
            if rel_path not in failed_docs:
                print("✓ Document successfully removed from failed list")
                return True
            else:
                print("✗ Document still in failed list")
                return False
        else:
            print("✓ Failed list empty after removal")
            return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Failed Document Tracking Fixes")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Failed Document Tracking", test_failed_tracking()))
    results.append(("Remove from Failed List", test_remove_from_failed()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + ("All tests passed! ✓" if all_passed else "Some tests failed. ✗"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())