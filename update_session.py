#!/usr/bin/env python3
import os
import sys
import json
import platform
script_dir = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.expanduser(script_dir + "/current_session.json")

def load_session():
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
            pass
            
    return default_session

def save_session(session):
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session, f, indent=4)
    except Exception as e:
        print(f"Warning: Failed to save session: {e}", file=sys.stderr)

def main():
    if len(sys.argv) < 3:
        print("Usage: update_session.py <user_query> <executed_command>")
        sys.exit(1)
        
    user_query = sys.argv[1]
    executed_command = sys.argv[2]
    
    session = load_session()
    
    # Update CWD and other context
    session['cwd'] = os.getcwd()
    session['shell'] = os.environ.get("SHELL", "unknown")
    session['os'] = platform.system()
    
    # Append to history
    session['history'].append({
        "command": user_query,
        "output": executed_command
    })
    
    # Keep history limited (optional, but good practice)
    if len(session['history']) > 20:
        session['history'] = session['history'][-20:]
        
    save_session(session)
    #print("\n session saved\n", file=sys.stderr)

if __name__ == "__main__":
    main()
