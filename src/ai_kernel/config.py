#!/usr/bin/env python
import os
import sys

# ANSI Colors
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[0;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

# Configuration
API_KEY_ENV = "GEMINI_API_KEY"
CONFIG_DIR = os.path.expanduser("~/.config/ktml-agent")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config")


def get_api_key():
    """
    Get the Gemini API key from environment variable or config file.
    
    Returns:
        str: The API key if found, None otherwise
    """
    # Try environment variable first
    api_key = os.getenv(API_KEY_ENV)
    if api_key:
        return api_key
    
    # Try config file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    if line.startswith(f"{API_KEY_ENV}="):
                        return line.split("=", 1)[1].strip()
        except Exception as e:
            print(f"{RED}Warning: Failed to read config file: {e}{NC}", file=sys.stderr)
            
    return None


def save_api_key(api_key):
    """
    Save the API key to the config file.
    
    Args:
        api_key (str): The API key to save
    """
    try:
        # Create config directory if it doesn't exist
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        # Write API key to config file
        with open(CONFIG_FILE, 'w') as f:
            f.write(f"{API_KEY_ENV}={api_key}\n")
        
        # Set file permissions to user-only read/write (Unix-like systems)
        if hasattr(os, 'chmod'):
            try:
                os.chmod(CONFIG_FILE, 0o600)
            except Exception:
                pass  # Ignore permission errors on Windows
                
        print(f"{GREEN}✓ API key saved successfully to {CONFIG_FILE}{NC}")
        
    except Exception as e:
        print(f"{RED}Error: Failed to save API key: {e}{NC}", file=sys.stderr)
        sys.exit(1)


def prompt_for_api_key():
    """
    Prompt the user to enter their Gemini API key on first run.
    
    Returns:
        str: The API key entered by the user, or None if cancelled
    """
    print(f"\n{CYAN}{'='*60}{NC}")
    print(f"{CYAN}Welcome to ktml-agent!{NC}")
    print(f"{CYAN}{'='*60}{NC}\n")
    
    print(f"{YELLOW}No API key found. Let's set up your Gemini API key.{NC}\n")
    
    print("To get your Gemini API key:")
    print(f"  1. Visit: {BLUE}https://aistudio.google.com/apikey{NC}")
    print("  2. Sign in with your Google account")
    print("  3. Click 'Create API Key'")
    print("  4. Copy the API key\n")
    
    try:
        api_key = input(f"{CYAN}Enter your Gemini API key (or press Ctrl+C to cancel): {NC}").strip()
        
        if not api_key:
            print(f"{RED}Error: API key cannot be empty{NC}")
            sys.exit(1)
        
        # Save the API key
        save_api_key(api_key)
        
        print(f"\n{GREEN}Setup complete! You can now use the agent.{NC}\n")
        
        return api_key
        
    except KeyboardInterrupt:
        print(f"\n{RED}Setup cancelled. You can run 'agent' again to set up your API key.{NC}")
        sys.exit(0)
    except EOFError:
        print(f"\n{RED}Setup cancelled. You can run 'agent' again to set up your API key.{NC}")
        sys.exit(0)


def ensure_api_key():
    """
    Ensure an API key is available, prompting the user if necessary.
    
    Returns:
        str: The API key
    """
    api_key = get_api_key()
    
    if not api_key:
        api_key = prompt_for_api_key()
    
    return api_key
