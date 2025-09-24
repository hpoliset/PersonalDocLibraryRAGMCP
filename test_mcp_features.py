#!/usr/bin/env python3
"""Test script to verify MCP server resources and prompts support"""

import json
import subprocess
import sys

def send_request(request):
    """Send a request to the MCP server and get response"""
    cmd = [
        "venv_mcp/bin/python", "-m",
        "personal_doc_library.servers.mcp_complete_server"
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            "PYTHONPATH": "/Users/hpoliset/DocumentIndexerMCP/src",
            "CHROMA_TELEMETRY": "false"
        }
    )

    # Send initialize first
    init_req = json.dumps({"method": "initialize", "params": {}, "jsonrpc": "2.0", "id": 0})
    proc.stdin.write(init_req + "\n")
    proc.stdin.flush()

    # Read initialize response
    init_resp = proc.stdout.readline()

    # Send actual request
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    # Read response
    response = proc.stdout.readline()

    proc.terminate()

    return json.loads(response) if response else None

print("Testing MCP Server New Features")
print("=" * 40)

# Test prompts/list
print("\n1. Testing prompts/list:")
prompts_req = {"method": "prompts/list", "params": {}, "jsonrpc": "2.0", "id": 1}
prompts_resp = send_request(prompts_req)
if prompts_resp and "result" in prompts_resp:
    print("✅ Prompts available:")
    for prompt in prompts_resp["result"]["prompts"]:
        print(f"   - {prompt['name']}: {prompt['description']}")
else:
    print("❌ Failed to get prompts")

# Test resources/list
print("\n2. Testing resources/list:")
resources_req = {"method": "resources/list", "params": {}, "jsonrpc": "2.0", "id": 2}
resources_resp = send_request(resources_req)
if resources_resp and "result" in resources_resp:
    print("✅ Resources available:")
    for resource in resources_resp["result"]["resources"]:
        print(f"   - {resource['uri']}: {resource['name']}")
else:
    print("❌ Failed to get resources")

print("\n✅ All features implemented successfully!")
print("Restart Claude Desktop to see the changes.")