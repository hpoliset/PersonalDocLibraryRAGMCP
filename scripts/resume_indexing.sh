#!/bin/bash
# Resume the Spiritual Library indexing process

PAUSE_FILE="/tmp/spiritual_library_index.pause"

echo "▶️  Resuming Spiritual Library Indexing..."

if [ -f "$PAUSE_FILE" ]; then
    # Get pause timestamp
    PAUSE_TIME=$(cat "$PAUSE_FILE" 2>/dev/null || echo "Unknown")
    
    # Remove pause file
    rm -f "$PAUSE_FILE"
    
    if [ ! -f "$PAUSE_FILE" ]; then
        echo "✅ Indexing resumed successfully"
        echo "   Was paused since: $PAUSE_TIME"
        echo ""
        echo "📌 The indexer will now process any queued files."
        echo ""
        echo "To pause again: ./scripts/pause_indexing.sh"
        echo "To check status: ./scripts/indexing_status.sh"
    else
        echo "❌ Failed to remove pause file"
        exit 1
    fi
else
    echo "ℹ️  Indexing is not currently paused"
    echo ""
    echo "To check status: ./scripts/indexing_status.sh"
fi