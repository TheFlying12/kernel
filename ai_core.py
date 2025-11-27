#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import sys
import json
import subprocess
import re
import urllib.request
import urllib.error
import platform
import logging


load_dotenv()

# Configuration
API_KEY_ENV = "GEMINI_API_KEY"
MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Check for local session file first (for dev/debugging), then global
if os.path.exists("current_session.json"):
    SESSION_FILE = "current_session.json"
else:
    SESSION_FILE = os.path.expanduser("~/.ai_terminal/current_session.json")

# Safety Patterns (from safety_check.py)
DANGER_PATTERNS = [
    r'rm\s+-rf\s+/',
    r'sudo\s+rm',
    r'dd\s+if=.*of=/dev/',
    r'mkfs',
    r'chmod\s+-R\s+777',
    r':\(\)\{ :\|:& \};:',
]

def get_api_key():
    # Try environment variable first
    api_key = os.getenv(API_KEY_ENV)
    if api_key:
        return api_key
    
    # Try config file
    config_path = os.path.expanduser("~/.config/ai_terminal/config")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass
            
    return None

def safety_check(command):
    for pattern in DANGER_PATTERNS:
        if re.search(pattern, command):
            return False, f"Matched danger pattern: {pattern}"
    return True, "Safe"

def load_session():
    # Default session structure
    default_session = {
        "history": [],
        "cwd": os.getcwd(),
        "shell": os.environ.get("SHELL", "unknown"),
        "os": platform.system(),
        "home_directory": os.path.expanduser("~")
    }
    
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass # Return default if load fails
            
    return default_session

def save_session(session):
    # Ensure directory exists
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session, f, indent=4)
    except Exception as e:
        print(f"Warning: Failed to save session: {e}", file=sys.stderr)

def call_gemini(query, api_key, session):
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    # Construct context-aware prompt
    history_text = ""
    for item in session.get("history", [])[-5:]: # Last 5 items
        history_text += f"User: {item['command']}\nAI: {item['output']}\n"
        
    context_prompt = f"""
Context:
- OS: {session['os']}
- Shell: {session['shell']}
- CWD: {session['cwd']}
- History:
{history_text}

User Query: {query}
"""

    data = {
        "systemInstruction": {
            "parts": [{"text": "You are a terminal command generator. Generate only the shell command needed, no explanations or markdown. Be concise. Use the provided context (OS, CWD, History) to generate accurate commands."}]
        },
        "contents": [{"role": "user", "parts": [{"text": context_prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100}
    }
    
    try:
        req = urllib.request.Request(MODEL_URL, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))

            try:
                candidate = result['candidates'][0]['content']['parts'][0]['text'].strip()
                # Clean up markdown code blocks if present
                candidate = re.sub(r'^```\w*\n', '', candidate)
                candidate = re.sub(r'\n```$', '', candidate)
                #print("\n"+candidate.strip()+"what api is returning\n", file=sys.stderr)
                return candidate.strip()
            except KeyError as e:
                return f"Error: KeyError - {e}"
            except IndexError as e:
                return f"Error: IndexError - {e}"
    except urllib.error.HTTPError as e:
        return f"Error: API request failed with status {e.code}: {e.read().decode('utf-8')}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: ai_core.py <natural_language_query>")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    
    api_key = get_api_key()
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment or config.")
        sys.exit(1)
        
    # Load and update session context
    session = load_session()
    session['cwd'] = os.getcwd() # Update CWD to current
    
    command = call_gemini(query, api_key, session)
    #print("\n"+command+"\nwhat api is returning post call_gemini\n", file=sys.stderr)
    if command.startswith("Error:"):
        print(command)
        sys.exit(1)
        
    is_safe, reason = safety_check(command)
    
    if not is_safe:
        print(f"WARNING: {reason}", file=sys.stderr)
        
    
    print(command)

if __name__ == "__main__":
    main()
