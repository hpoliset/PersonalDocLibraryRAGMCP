#!/usr/bin/env python3
"""Test MCP resources implementation"""

import json
import subprocess
import sys

def send_request(method, params=None):
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
    init_req = {"method": "initialize", "params": {}, "jsonrpc": "2.0", "id": 0}
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()

    # Read initialize response
    init_resp = proc.stdout.readline()
    print(f"Initialize response: {json.loads(init_resp)}")

    # Send actual request
    request = {"method": method, "params": params or {}, "jsonrpc": "2.0", "id": 1}
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    # Read response
    response = proc.stdout.readline()

    proc.terminate()

    return json.loads(response) if response else None

print("Testing Resources Implementation")
print("=" * 40)

# Test resources/list
print("\n1. Testing resources/list:")
resources_resp = send_request("resources/list")
if resources_resp and "result" in resources_resp:
    print("✅ Resources available:")
    for resource in resources_resp["result"]["resources"]:
        print(f"   - {resource['uri']}: {resource['name']}")
        print(f"     Description: {resource['description']}")
        print(f"     MIME Type: {resource['mimeType']}")
else:
    print(f"❌ Failed: {resources_resp}")

# Test resources/read for library://stats
print("\n2. Testing resources/read for library://stats:")
read_resp = send_request("resources/read", {"uri": "library://stats"})
if read_resp and "result" in read_resp:
    print("✅ Successfully read resource")
    contents = read_resp["result"]["contents"][0]
    print(f"   URI: {contents['uri']}")
    print(f"   MIME Type: {contents['mimeType']}")
    print(f"   Content preview: {contents['text'][:200]}...")
else:
    print(f"❌ Failed: {read_resp}")