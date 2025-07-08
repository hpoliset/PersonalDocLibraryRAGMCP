#!/bin/bash
# Test the log viewer

echo "📋 Testing MCP Log Viewer"
echo "========================"
echo ""

# Show help
echo "1. Showing help:"
./view_mcp_logs.sh -h
echo ""
echo "Press Enter to continue..."
read

# Show last 20 lines
echo "2. Showing last 20 lines:"
./view_mcp_logs.sh -n 20
echo ""
echo "Press Enter to continue..."
read

# Filter for errors
echo "3. Filtering for errors:"
./view_mcp_logs.sh -n 50 -g "ERROR"
echo ""
echo "Press Enter to continue..."
read

# Filter for search operations
echo "4. Filtering for search operations:"
./view_mcp_logs.sh -n 30 -g "search"
echo ""
echo "Press Enter to follow logs in real-time (Ctrl+C to stop)..."
read

# Follow logs in real-time
echo "5. Following logs in real-time:"
./view_mcp_logs.sh -f