#!/usr/bin/env python3
"""
Standalone PDF cleaning utility for problematic PDFs
Can be used manually or called by the enhanced MCP server
"""

import os
import subprocess
import shutil
import logging
import time
import sys
import json
from pathlib import Path
from personal_doc_library.core.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_pdf_with_ghostscript(input_path, output_path, timeout_minutes=30):
    """
    Clean a PDF using Ghostscript
    
    Args:
        input_path: Path to input PDF
        output_path: Path to save cleaned PDF
        timeout_minutes: Timeout in minutes (default 30)
    """
    try:
        logger.info(f"Cleaning {os.path.basename(input_path)}...")
        start_time = time.time()
        
        # Ghostscript command with balanced optimization
        cmd = [
            'gs',
            '-dBATCH',
            '-dNOPAUSE',
            '-q',
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/ebook',  # Balance between quality and size
            '-dCompressFonts=true',
            '-dSubsetFonts=true',
            '-dColorImageDownsampleType=/Bicubic',
            '-dColorImageResolution=150',
            '-dGrayImageDownsampleType=/Bicubic',
            '-dGrayImageResolution=150',
            '-dMonoImageDownsampleType=/Bicubic',
            '-dMonoImageResolution=150',
            '-dOptimize=true',
            f'-sOutputFile={output_path}',
            input_path
        ]
        
        # Run with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_minutes * 60
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            # Check output
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                input_size = os.path.getsize(input_path) / (1024*1024)
                output_size = os.path.getsize(output_path) / (1024*1024)
                reduction = ((input_size - output_size) / input_size) * 100 if input_size > 0 else 0
                
                logger.info(f"✓ Success! Cleaned in {elapsed/60:.1f} minutes")
                logger.info(f"  Size: {input_size:.1f}MB → {output_size:.1f}MB ({reduction:.1f}% reduction)")
                return True
            else:
                logger.error("Ghostscript completed but output file is missing or empty")
                return False
        else:
            logger.error(f"Ghostscript failed with code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr[:500]}...")  # Truncate long errors
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout after {timeout_minutes} minutes")
        # Clean up partial file
        if os.path.exists(output_path):
            os.remove(output_path)
        return False
    except FileNotFoundError:
        logger.error("Ghostscript not found. Install with: brew install ghostscript")
        return False
    except Exception as e:
        logger.error(f"Error cleaning PDF: {e}")
        return False

def process_pdf(filepath, books_dir=None, timeout_minutes=30):
    """
    Process a single PDF file
    
    Args:
        filepath: Path to PDF file
        books_dir: Base books directory
        timeout_minutes: Timeout for cleaning
    """
    if books_dir is None:
        books_dir = str(config.books_directory)
    
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return False
    
    filename = os.path.basename(filepath)
    logger.info(f"\nProcessing: {filename}")
    logger.info(f"Size: {os.path.getsize(filepath) / (1024*1024):.1f} MB")
    
    # Create directories
    originals_dir = os.path.join(books_dir, "originals")
    os.makedirs(originals_dir, exist_ok=True)
    
    # Paths
    temp_cleaned = filepath + ".cleaned.tmp"
    backup_path = os.path.join(originals_dir, filename)
    
    # Clean the PDF
    if clean_pdf_with_ghostscript(filepath, temp_cleaned, timeout_minutes):
        try:
            # Backup original
            logger.info(f"Backing up original to {backup_path}")
            shutil.copy2(filepath, backup_path)
            
            # Replace with cleaned version
            logger.info("Replacing with cleaned version...")
            shutil.move(temp_cleaned, filepath)
            
            logger.info(f"✓ Successfully cleaned {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error replacing file: {e}")
            # Try to restore
            if os.path.exists(backup_path) and not os.path.exists(filepath):
                shutil.copy2(backup_path, filepath)
            # Clean up temp file
            if os.path.exists(temp_cleaned):
                os.remove(temp_cleaned)
            return False
    else:
        # Clean up any temp file
        if os.path.exists(temp_cleaned):
            os.remove(temp_cleaned)
        return False

def find_large_pdfs(books_dir=None, min_size_mb=50):
    """Find PDFs larger than specified size"""
    if books_dir is None:
        books_dir = str(config.books_directory)
    
    large_pdfs = []
    
    for root, dirs, files in os.walk(books_dir):
        # Skip originals directory
        if "originals" in root:
            continue
            
        for file in files:
            if file.lower().endswith('.pdf'):
                filepath = os.path.join(root, file)
                size_mb = os.path.getsize(filepath) / (1024*1024)
                if size_mb >= min_size_mb:
                    large_pdfs.append((filepath, size_mb))
    
    return sorted(large_pdfs, key=lambda x: x[1], reverse=True)

def main():
    """Main function for standalone usage"""
    
    if len(sys.argv) > 1:
        # Process specific file
        filepath = sys.argv[1]
        timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        
        success = process_pdf(filepath, timeout_minutes=timeout)
        sys.exit(0 if success else 1)
    
    else:
        # Interactive mode - find and process large PDFs
        print("\n🔍 PDF Cleaning Utility")
        print("=" * 50)
        
        books_dir = str(config.books_directory)
        if not os.path.exists(books_dir):
            logger.error(f"Books directory not found: {books_dir}")
            sys.exit(1)
        
        # Find large PDFs
        min_size = 50  # MB
        large_pdfs = find_large_pdfs(books_dir, min_size)
        
        if not large_pdfs:
            print(f"No PDFs larger than {min_size}MB found.")
            sys.exit(0)
        
        print(f"\nFound {len(large_pdfs)} PDFs larger than {min_size}MB:")
        for i, (path, size) in enumerate(large_pdfs, 1):
            rel_path = os.path.relpath(path, books_dir)
            print(f"{i}. {rel_path} ({size:.1f}MB)")
        
        print("\nOptions:")
        print("- Enter number to clean specific PDF")
        print("- Enter 'all' to clean all large PDFs")
        print("- Enter 'q' to quit")
        
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'q':
            sys.exit(0)
        elif choice == 'all':
            # Process all
            success_count = 0
            for path, size in large_pdfs:
                # Larger files get more time
                timeout = max(30, int(size / 10))  # ~10MB per minute
                if process_pdf(path, books_dir, timeout):
                    success_count += 1
            
            print(f"\n✅ Cleaned {success_count}/{len(large_pdfs)} PDFs")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(large_pdfs):
                    path, size = large_pdfs[idx]
                    timeout = max(30, int(size / 10))
                    process_pdf(path, books_dir, timeout)
                else:
                    print("Invalid selection")
            except ValueError:
                print("Invalid input")

if __name__ == "__main__":
    main()