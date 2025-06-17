#!/usr/bin/env python3
"""
Quick start script for the Multi-Agent RAG System
"""

import subprocess
import sys
import time
import threading
from pathlib import Path

def start_mcp_server():
    """Start the MCP filesystem server in the background."""
    print("🚀 Starting MCP Filesystem Server...")
    try:
        subprocess.run([
            sys.executable, "mcp_filesystem_server.py"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start MCP server: {e}")
    except KeyboardInterrupt:
        print("🛑 MCP server stopped")

def main():
    """Main startup function."""
    print("🤖 Multi-Agent RAG System Startup")
    print("=" * 50)
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found. Please create one based on .env.example")
        return
    
    # Start MCP server in background thread
    mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
    mcp_thread.start()
    
    # Wait a moment for MCP server to start
    print("⏳ Waiting for MCP server to initialize...")
    time.sleep(3)
    
    # Start the main application
    print("🚀 Starting Multi-Agent System...")
    try:
        from src.main import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
