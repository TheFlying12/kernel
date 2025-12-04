#!/usr/bin/env python
import sys
import os
import subprocess
import shlex
import core
import db

# ANSI Colors
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[0;33m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m' # No Color

def print_welcome():
    print(f"{BLUE}Ask Away!!{NC}")
    print("----------------------------------------")

def execute_command(command):
    try:
        # Use shell=True to allow piping and complex commands
        # On Windows, this uses cmd.exe or PowerShell depending on the environment
        process = subprocess.run(command, shell=True, text=True, capture_output=True)
        print(process.stdout)
        if process.stderr:
            print(f"{RED}{process.stderr}{NC}")
        return process.returncode, process.stdout
    except Exception as e:
        print(f"{RED}Execution failed: {e}{NC}")
        return 1, str(e)

def handle_undo(script_dir):
    try:
        history = db.get_recent_history(limit=1)
        if not history or not history[0].get('inverse'):
            print(f"{RED}Nothing to undo.{NC}")
            return

        undo_cmd = history[0]['inverse']
        print(f"{PURPLE}🤖 Undo: {undo_cmd}{NC}")
        
        # Safety Check for Undo
        is_safe, reason = core.safety_check(undo_cmd)
        if not is_safe:
            print(f"{RED}WARNING: Undo command matched danger pattern: {reason}{NC}")
            confirm = input(f"{YELLOW}Execute DANGEROUS undo? (y/n): {NC}")
            if confirm.lower() != 'y':
                print(f"{RED}Undo cancelled{NC}")
                return
        else:
            # Auto-confirm safe undo if desired, or keep manual for undo since it's sensitive
            # User asked for auto-run on "command", undo might be different. 
            # Let's keep manual confirm for undo as it's rare, OR allow editing.
            # The original code allowed editing.
            confirm = input(f"{YELLOW}Edit undo (Enter to execute): {NC}")
            if confirm.strip():
                undo_cmd = confirm

        if undo_cmd:
            exit_code, output = execute_command(undo_cmd)
            
            # Get latest session ID
            session_id = db.get_latest_session_id()
            db.add_history(session_id, "undo", undo_cmd, None, exit_code, output)
        else:
            print(f"{RED}Undo cancelled{NC}")

    except Exception as e:
        print(f"{RED}Undo error: {e}{NC}")

def main():
    print_welcome()
    
    # Initialize DB
    try:
        db.init_db()
    except Exception:
        pass

    while True:
        try:
            ai_input = input(f"{BLUE}AI> {NC}")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue

        if not ai_input.strip():
            print(f"{YELLOW}Please enter a command{NC}")
            continue

        if ai_input.strip().lower() == "exit":
            break
        
        if ai_input.strip().lower() == "undo":
            handle_undo(os.path.dirname(os.path.abspath(__file__)))
            continue

        # Process Query
        result = core.process_query(ai_input)

        if "error" in result:
            print(f"{RED}{result['error']}{NC}")
            continue

        command = result.get('command')
        inverse = result.get('inverse')
        safety_warning = result.get('safety_warning')

        print(f"{PURPLE}🤖 AI: {command}{NC}")

        if safety_warning:
            print(f"{RED}WARNING: {safety_warning}{NC}")
            confirm = input(f"{YELLOW}Execute this command? (y/n/i to edit): {NC}").strip().lower()
        else:
            # Auto-run safe commands
            confirm = 'y'
            
        if confirm == 'i':
            print(f"{YELLOW}Edit command: {NC}", end='')
            # Simple input for editing (prefill is hard cross-platform without deps)
            # We'll just ask for new input, defaulting to old if empty is not ideal but simple
            print(f"(Copy/Paste the command to edit: {command})")
            new_command = input()
            if new_command.strip():
                command = new_command
            confirm = 'y'

        if confirm == 'y':
            exit_code, output = execute_command(command)
            
            # Update History
            session_id = db.get_latest_session_id()
            db.add_history(session_id, ai_input, command, inverse, exit_code, output)
        else:
            print(f"{RED}Command cancelled{NC}")

if __name__ == "__main__":
    main()
