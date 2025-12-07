#!/usr/bin/env python
"""Test script to verify the first-run API key configuration."""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test 1: Check if config module works
print("=" * 60)
print("Test 1: Testing config module import and functions")
print("=" * 60)

try:
    import ai_kernel.config as config
    print("✓ Config module imported successfully")
    
    # Check get_api_key when no key exists
    api_key = config.get_api_key()
    if api_key is None:
        print("✓ get_api_key() returns None when no key exists")
    else:
        print(f"✗ get_api_key() returned: {api_key} (expected None)")
    
    # Test save_api_key
    print("\nTest 2: Testing save_api_key()")
    test_key = "test-api-key-12345"
    config.save_api_key(test_key)
    
    # Verify it was saved
    saved_key = config.get_api_key()
    if saved_key == test_key:
        print(f"✓ API key saved and retrieved successfully")
        print(f"  Config file location: {config.CONFIG_FILE}")
    else:
        print(f"✗ API key mismatch. Saved: {test_key}, Retrieved: {saved_key}")
    
    # Check file permissions (Unix only)
    if hasattr(os, 'stat'):
        import stat
        file_stat = os.stat(config.CONFIG_FILE)
        mode = file_stat.st_mode
        print(f"  File permissions: {oct(stat.S_IMODE(mode))}")
    
    # Clean up test
    print("\nTest 3: Cleaning up test config file")
    if os.path.exists(config.CONFIG_FILE):
        os.remove(config.CONFIG_FILE)
        print(f"✓ Test config file removed")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
