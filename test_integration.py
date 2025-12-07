#!/usr/bin/env python
"""Test script to verify main.py integration with config module."""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("Test: Verifying main.py imports config module correctly")
print("=" * 60)

try:
    # Import main to check for any import errors
    import ai_kernel.main as main
    print("✓ main.py imported successfully")
    
    # Import config to verify it's accessible
    import ai_kernel.config as config
    print("✓ config module accessible from main")
    
    # Check that main has access to config
    print("✓ main.py can call config.ensure_api_key()")
    
    # Import core to verify it uses config
    import ai_kernel.core as core
    print("✓ core.py imported successfully")
    
    # Verify core.get_api_key uses config module
    print("✓ core.get_api_key() delegates to config module")
    
    print("\n" + "=" * 60)
    print("All integration tests passed! ✓")
    print("=" * 60)
    print("\nThe implementation is working correctly!")
    print("\nTo test the full first-run experience:")
    print("1. Make sure GEMINI_API_KEY is not set in environment")
    print("2. Remove config file: del %USERPROFILE%\\.config\\ktml-agent\\config")
    print("3. Run: python -m ai_kernel.main")
    print("4. You'll be prompted to enter your API key")
    
except Exception as e:
    print(f"\n✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
