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

# Load .env from script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)
import db
load_dotenv(os.path.join(script_dir, ".env"))

# Configuration
API_KEY_ENV = "GEMINI_API_KEY"
MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Always use global session file for consistency
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

def get_directory_context():
    """Scans relevant directories to provide context for navigation."""
    dirs = []
    
    # 1. Current Working Directory (Depth 1)
    try:
        cwd = os.getcwd()
        with os.scandir(cwd) as entries:
            for entry in entries:
                if entry.is_dir() and not entry.name.startswith('.'):
                    dirs.append(f"{entry.path} (in CWD)")
    except Exception:
        pass

    # 2. Home Directory (Depth 1)
    try:
        home = os.path.expanduser("~")
        with os.scandir(home) as entries:
            for entry in entries:
                if entry.is_dir() and not entry.name.startswith('.'):
                    dirs.append(f"{entry.path} (in Home)")
    except Exception:
        pass
        
    # 3. Documents (Depth 2 - to find things like ~/Documents/Me/Coding)
    try:
        docs = os.path.expanduser("~/Documents")
        if os.path.exists(docs):
             for root, subdirs, files in os.walk(docs):
                # Calculate depth
                depth = root[len(docs):].count(os.sep)
                if depth < 2:
                    for d in subdirs:
                        if not d.startswith('.'):
                            dirs.append(os.path.join(root, d))
                else:
                    # Don't go deeper
                    del subdirs[:]
    except Exception:
        pass
        
    # Deduplicate and limit
    unique_dirs = sorted(list(set(dirs)))
    # Limit to reasonable amount to save tokens, prioritizing deep matches if possible or just first 50
    return unique_dirs[:50]

def load_session():
    # Load recent history from DB
    try:
        history = db.get_recent_history(limit=5)
    except Exception:
        history = []
    
    return {
        "history": history,
        "cwd": os.getcwd(),
        "shell": os.environ.get("SHELL", "unknown"),
        "os": platform.system(),
        "home_directory": os.path.expanduser("~")
    }

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
        
    # Get directory context
    dir_context = get_directory_context()
    dir_list = "\n".join(dir_context)

    context_prompt = f"""
Context:
- OS: {session['os']}
- Shell: {session['shell']}
- CWD: {session['cwd']}
- Known Directories:
{dir_list}
- History:
{history_text}

User Query: {query}
"""

    data = {
        "systemInstruction": {
            "parts": [{"text": "You are a terminal command generator. You must output a JSON object with two keys: 'command' (the shell command to execute) and 'inverse' (the command to undo this action). If there is no undo (like 'ls'), set 'inverse' to null. Be concise. Example: {\"command\": \"mkdir foo\", \"inverse\": \"rmdir foo\"}"}]
        },
        "contents": [{"role": "user", "parts": [{"text": context_prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192, "responseMimeType": "application/json"}
    }
    

    try:
        req = urllib.request.Request(MODEL_URL, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # Debug: Save raw response
            try:
                with open('results.json', 'w') as f:
                    json.dump(result, f, indent=4)
            except Exception:
                pass


            try:
                if 'candidates' not in result or not result['candidates']:
                    return "Error: No candidates returned. Check safety settings or prompt."
                
                candidate_data = result['candidates'][0]
                
                if 'content' not in candidate_data:
                    finish_reason = candidate_data.get('finishReason', 'UNKNOWN')
                    return f"Error: No content generated. Finish reason: {finish_reason}"
                    
                if 'parts' not in candidate_data['content']:
                     return "Error: Content has no parts."

                candidate = candidate_data['content']['parts'][0]['text'].strip()
                # Clean up markdown code blocks if present
                candidate = re.sub(r'^```\w*\n', '', candidate)
                candidate = re.sub(r'\n```$', '', candidate)
                
                try:
                    response_json = json.loads(candidate)
                    return response_json
                except json.JSONDecodeError:
                    # Fallback if model forgets JSON
                    return {"command": candidate, "inverse": None}
            except KeyError as e:
                with open('errors.json', 'w') as f:
                    json.dump(result, f, indent=4)
                return f"Error: KeyError - {e}. Details saved to errors.json"
            except IndexError as e:
                with open('errors.json', 'w') as f:
                    json.dump(result, f, indent=4)
                return f"Error: IndexError - {e}. Details saved to errors.json"
    except urllib.error.HTTPError as e:
        return f"Error: API request failed with status {e.code}: {e.read().decode('utf-8')}"
        print(result, file=sys.stderr)
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: ai_core.py <natural_language_query>")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    
    # Initialize DB
    try:
        db.init_db()
    except Exception:
        pass # Fail gracefully if DB is locked or inaccessible
    
    api_key = get_api_key()
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment or config.")
        sys.exit(1)
        
    # Load context
    session = load_session()
    
    # Check Cache
    try:
        cached_command = db.check_cache(query, session['cwd'], session['shell'], session['os'])
        if cached_command:
            print(cached_command)
            sys.exit(0)
    except Exception:
        pass
    
    response = call_gemini(query, api_key, session)
    
    if isinstance(response, str) and response.startswith("Error:"):
        print(response)
        sys.exit(1)
        
    command = response.get('command', '')
    inverse = response.get('inverse', '')
    
    if not command:
        print("Error: No command generated")
        sys.exit(1)
        
    is_safe, reason = safety_check(command)
    
    if not is_safe:
        print(f"WARNING: {reason}", file=sys.stderr)
    else:
        # Cache successful response
        try:
            # We cache the JSON string to preserve the inverse
            db.cache_response(query, session['cwd'], session['shell'], session['os'], json.dumps(response))
        except Exception:
            pass
    
    # Output format: COMMAND | INVERSE (separator for shell script to parse)
    if inverse:
        print(f"{command}|{inverse}")
    else:
        print(f"{command}|")

if __name__ == "__main__":
    main()
