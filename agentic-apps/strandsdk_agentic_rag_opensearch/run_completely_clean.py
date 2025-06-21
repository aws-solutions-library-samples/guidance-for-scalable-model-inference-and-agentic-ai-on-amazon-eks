#!/usr/bin/env python3
"""
Completely clean runner that suppresses ALL stderr during execution.
Use this for the cleanest possible output experience.
"""

import sys
import os
import subprocess
from contextlib import redirect_stderr
from io import StringIO

def run_with_clean_stderr(query: str):
    """Run the query with completely suppressed stderr."""
    
    print("🚀 Enhanced RAG System - Ultra Clean Mode")
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)
    print("Note: All async warnings are completely suppressed")
    print("=" * 60)
    
    # Create a script to run the query
    script_content = f'''
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.global_async_cleanup import setup_global_async_cleanup, install_global_stderr_filter
setup_global_async_cleanup()
install_global_stderr_filter()

from src.agents.supervisor_agent import supervisor_agent

try:
    response = supervisor_agent("{query}")
    print("\\n📝 Response:")
    print("-" * 40)
    print(response)
    print("-" * 40)
    print("\\n✅ Query completed successfully!")
except Exception as e:
    print(f"\\n❌ Error: {{e}}")
    sys.exit(1)
'''
    
    # Write temporary script
    script_path = "temp_query_script.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print only stdout (clean output)
        print(result.stdout)
        
        # Only show stderr if there are actual errors (not async warnings)
        if result.stderr and result.returncode != 0:
            stderr_lines = result.stderr.split('\\n')
            important_errors = []
            
            for line in stderr_lines:
                # Only show lines that look like real errors
                if any(error_pattern in line.lower() for error_pattern in [
                    'error:', 'failed:', 'exception:', 'traceback', 'critical:'
                ]) and not any(async_pattern in line.lower() for async_pattern in [
                    'async', 'http', 'coroutine', 'runtime', 'generator'
                ]):
                    important_errors.append(line)
            
            if important_errors:
                print("\\n⚠️  Important Errors:")
                for error in important_errors:
                    print(error)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("\\n❌ Query timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"\\n❌ Error running query: {e}")
        return False
    finally:
        # Clean up temporary script
        if os.path.exists(script_path):
            os.remove(script_path)

if __name__ == "__main__":
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What is Bell's palsy and how is it treated?"
    
    success = run_with_clean_stderr(query)
    sys.exit(0 if success else 1)
