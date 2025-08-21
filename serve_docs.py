#!/usr/bin/env python3
"""
Simple Flask server to serve the architecture documentation
"""
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# Get the docs directory path
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')

@app.route('/')
def serve_architecture():
    """Serve the architecture.html file"""
    return send_from_directory(DOCS_DIR, 'architecture.html')

@app.route('/<path:filename>')
def serve_file(filename):
    """Serve any file from the docs directory"""
    return send_from_directory(DOCS_DIR, filename)

if __name__ == '__main__':
    print("📚 Starting Documentation Server")
    print("📌 Open http://localhost:5001 in your browser")
    print("   Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5001, debug=False)