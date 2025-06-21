#!/usr/bin/env python3
"""
Clean main application runner that suppresses async warnings.
"""

# Import global async cleanup FIRST
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.global_async_cleanup import setup_global_async_cleanup, install_global_stderr_filter

# Ensure global cleanup is applied
setup_global_async_cleanup()
install_global_stderr_filter()

# Now import and run the main application
from src.main import main

if __name__ == "__main__":
    print("🚀 Starting Enhanced RAG System (Clean Mode)")
    print("=" * 60)
    print("Note: Async warnings are suppressed for cleaner output")
    print("=" * 60)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        sys.exit(1)
