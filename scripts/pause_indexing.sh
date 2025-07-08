#!/bin/bash
# Pause the Spiritual Library indexing process

PAUSE_FILE="/tmp/spiritual_library_index.pause"

echo "⏸️  Pausing Spiritual Library Indexing..."

# Create pause file with timestamp
echo "$(date +%Y-%m-%dT%H:%M:%S)" > "$PAUSE_FILE"

if [ -f "$PAUSE_FILE" ]; then
    echo "✅ Indexing paused successfully"
    echo "   Pause file created at: $PAUSE_FILE"
    echo ""
    echo "📌 The indexer will complete the current PDF and then pause."
    echo "📌 New files will be queued but not processed until resumed."
    echo ""
    echo "To resume: ./scripts/resume_indexing.sh"
    echo "To check status: ./scripts/indexing_status.sh"
else
    echo "❌ Failed to create pause file"
    exit 1
fi