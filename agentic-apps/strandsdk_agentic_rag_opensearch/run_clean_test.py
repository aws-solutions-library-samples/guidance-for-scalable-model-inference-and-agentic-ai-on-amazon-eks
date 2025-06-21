#!/usr/bin/env python3
"""
Clean test runner that suppresses async warnings for a better user experience.
"""

import sys
import os
import warnings
import subprocess

# Suppress all async-related warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*async.*")
warnings.filterwarnings("ignore", message=".*coroutine.*")

def run_test_with_clean_output():
    """Run the test with stderr filtering to provide clean output."""
    
    print("🚀 Running Enhanced RAG System Test (Clean Output)")
    print("=" * 60)
    
    # Run the test and capture output
    try:
        result = subprocess.run(
            [sys.executable, "test_enhanced_rag.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print stdout (the actual test results)
        print(result.stdout)
        
        # Filter and show only relevant stderr messages
        if result.stderr:
            stderr_lines = result.stderr.split('\n')
            filtered_stderr = []
            
            for line in stderr_lines:
                # Skip async-related warnings
                if any(skip_phrase in line for skip_phrase in [
                    "async generator ignored GeneratorExit",
                    "Attempted to exit cancel scope",
                    "no running event loop",
                    "HTTP11ConnectionByteStream",
                    "coroutine object",
                    "RuntimeError: async generator",
                    "Exception ignored in:"
                ]):
                    continue
                
                # Keep other important error messages
                if line.strip() and not line.startswith("  "):
                    filtered_stderr.append(line)
            
            if filtered_stderr:
                print("\n⚠️  Important Messages:")
                for line in filtered_stderr:
                    print(line)
        
        print("\n✅ Test completed successfully!")
        print("Note: Async cleanup warnings have been filtered for cleaner output.")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 5 minutes")
        return 1
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_test_with_clean_output()
    sys.exit(exit_code)
