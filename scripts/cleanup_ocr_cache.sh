#!/bin/bash

# Script to clean up recursive .ocr_cache folders and keep only the top-level ones

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LIBRARY_PATH="${1:-/Users/hpoliset/SpiritualLibrary}"

echo "🧹 Cleaning up recursive .ocr_cache folders"
echo "==========================================="
echo ""
echo "Library path: $LIBRARY_PATH"
echo ""

# Count total .ocr_cache directories
total_count=$(find "$LIBRARY_PATH" -type d -name ".ocr_cache" 2>/dev/null | wc -l | tr -d ' ')
echo "Found $total_count .ocr_cache directories"

# Find nested .ocr_cache directories (those within another .ocr_cache)
nested_count=0
removed_count=0

echo ""
echo "Removing nested .ocr_cache directories..."

# Find and remove nested .ocr_cache directories
find "$LIBRARY_PATH" -type d -name ".ocr_cache" | while read cache_dir; do
    # Check if this .ocr_cache is inside another .ocr_cache
    parent_path=$(dirname "$cache_dir")
    if [[ "$parent_path" == *"/.ocr_cache"* ]]; then
        echo "  Removing nested: ${cache_dir#$LIBRARY_PATH/}"
        rm -rf "$cache_dir"
        ((removed_count++))
    fi
done

# Clean up empty .ocr_cache directories
echo ""
echo "Cleaning up empty .ocr_cache directories..."
find "$LIBRARY_PATH" -type d -name ".ocr_cache" -empty -delete 2>/dev/null

# Remove problematic OCR'd files that keep failing
echo ""
echo "Removing problematic recursive OCR files..."
find "$LIBRARY_PATH" -name "*.ocr.pdf.ocr.pdf*" -type f -delete 2>/dev/null

# Final count
remaining_count=$(find "$LIBRARY_PATH" -type d -name ".ocr_cache" 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "✅ Cleanup complete!"
echo "  - Started with: $total_count .ocr_cache directories"
echo "  - Remaining: $remaining_count .ocr_cache directories"
echo "  - Removed: $((total_count - remaining_count)) nested/empty directories"
echo ""
echo "The remaining .ocr_cache directories are legitimate and contain OCR'd PDFs."