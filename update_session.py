#!/usr/bin/env python3
import os
import sys

# Ensure we can import db
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)
import db

def main():
    if len(sys.argv) < 3:
        print("Usage: update_session.py <user_query> <executed_command>")
        sys.exit(1)
        
    user_query = sys.argv[1]
    executed_command = sys.argv[2]
    inverse_command = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        # Initialize DB if needed (though ai_core should have done it)
        db.init_db()
        
        # Get current session
        session_id = db.get_latest_session_id()
        
        # Add to history
        db.add_history(session_id, user_query, executed_command, inverse_command)
        
    except Exception as e:
        print(f"Warning: Failed to update session history: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
