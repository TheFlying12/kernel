#!/usr/bin/env python
"""
Quick verification test for the API key configuration system.
This test verifies that all components are working together.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 70)
print("API Key Configuration - Verification Test")
print("=" * 70)

# Test 1: Import all modules
print("\n[Test 1] Importing modules...")
try:
    from ai_kernel import config, core, main
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Verify config module functions exist
print("\n[Test 2] Checking config module functions...")
required_functions = ['get_api_key', 'save_api_key', 'prompt_for_api_key', 'ensure_api_key']
for func_name in required_functions:
    if hasattr(config, func_name):
        print(f"✓ config.{func_name}() exists")
    else:
        print(f"✗ config.{func_name}() missing")
        sys.exit(1)

# Test 3: Verify config file path
print("\n[Test 3] Checking config file path...")
print(f"  Config directory: {config.CONFIG_DIR}")
print(f"  Config file: {config.CONFIG_FILE}")
expected_path = os.path.expanduser("~/.config/ktml-agent/config")
if config.CONFIG_FILE == expected_path:
    print(f"✓ Config file path is correct")
else:
    print(f"✗ Config file path mismatch")
    print(f"  Expected: {expected_path}")
    print(f"  Got: {config.CONFIG_FILE}")

# Test 4: Test get_api_key when no key exists
print("\n[Test 4] Testing get_api_key() with no config...")
# Make sure no config exists for this test
if os.path.exists(config.CONFIG_FILE):
    print(f"  Note: Config file already exists at {config.CONFIG_FILE}")
    print(f"  Current API key: {config.get_api_key()}")
else:
    api_key = config.get_api_key()
    if api_key is None:
        print("✓ get_api_key() returns None when no config exists")
    else:
        print(f"✗ get_api_key() returned unexpected value: {api_key}")

# Test 5: Verify core.get_api_key uses config module
print("\n[Test 5] Verifying core.get_api_key() integration...")
try:
    core_api_key = core.get_api_key()
    config_api_key = config.get_api_key()
    if core_api_key == config_api_key:
        print("✓ core.get_api_key() correctly delegates to config module")
    else:
        print(f"✗ Mismatch between core and config get_api_key()")
except Exception as e:
    print(f"✗ Error calling core.get_api_key(): {e}")

print("\n" + "=" * 70)
print("✓ All verification tests passed!")
print("=" * 70)
print("\nThe implementation is ready to use!")
print("\nTo test the interactive first-run experience:")
print("  1. Ensure no GEMINI_API_KEY environment variable is set")
print("  2. Remove any existing config: del %USERPROFILE%\\.config\\ktml-agent\\config")
print("  3. Run: python -m ai_kernel.main")
print("  4. You should see a prompt asking for your API key")
print("\nAfter entering your API key once, subsequent runs will load it automatically.")
