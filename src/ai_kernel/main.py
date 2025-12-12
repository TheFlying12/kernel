#!/usr/bin/env python
import sys
import os
import subprocess
import shlex

# Handle imports for both package and direct execution
try:
    from . import core
    from . import db
    from . import config
except ImportError:
    import core
    import db
    import config

# ANSI Colors
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[0;33m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m' # No Color

import concurrent.futures
import json

def print_welcome():
    print(f"{BLUE}Ask Away!!{NC}")
    print("----------------------------------------")

def execute_command(command, mute_output=False):
    try:
        # Check for cd command
        if command.startswith("cd "):
            target_dir = command[3:].strip()
            # Handle absolute and relative paths
            if not target_dir: # just 'cd'
                target_dir = os.path.expanduser("~")
            else:
                target_dir = os.path.expanduser(target_dir)
            
            try:
                os.chdir(target_dir)
                if not mute_output:
                    print(f"{GREEN}Changed directory to: {os.getcwd()}{NC}")
                return 0, f"Changed directory to: {os.getcwd()}"
            except FileNotFoundError:
                err = f"Directory not found: {target_dir}"
                if not mute_output: print(f"{RED}{err}{NC}")
                return 1, err
            except OSError as e:
                err = f"Error changing directory: {e}"
                if not mute_output: print(f"{RED}{err}{NC}")
                return 1, err

        # Use shell=True to allow piping and complex commands
        # On Windows, this uses cmd.exe or PowerShell depending on the environment
        process = subprocess.run(command, shell=True, text=True, capture_output=True)
        
        output = process.stdout
        if process.stderr:
            output += f"\nStderr: {process.stderr}"
            
        if not mute_output:
            print(process.stdout)
            if process.stderr:
                print(f"{RED}{process.stderr}{NC}")
                
        return process.returncode, output
    except Exception as e:
        if not mute_output: print(f"{RED}Execution failed: {e}{NC}")
        return 1, str(e)

def execute_plan(plan):
    full_output = []
    overall_exit_code = 0
    
    print(f"{CYAN}Executing Plan ({len(plan)} steps)...{NC}")
    
    for i, step in enumerate(plan):
        print(f"\n{BLUE}Step {i+1}/{len(plan)}:{NC}")
        
        # If single command, run normally
        if len(step) == 1:
            cmd = step[0]
            print(f"{PURPLE}Running: {cmd}{NC}")
            details = f"Step {i+1} [Sequential]: {cmd}\n"
            exit_code, output = execute_command(cmd)
            details += f"Exit Code: {exit_code}\nOutput:\n{output}\n"
            full_output.append(details)
            if exit_code != 0:
                print(f"{RED}Step failed. Stopping plan execution.{NC}")
                overall_exit_code = exit_code
                break
        else:
            # Parallel execution
            print(f"{PURPLE}Running in parallel: {step}{NC}")
            details = f"Step {i+1} [Parallel]: {step}\n"
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # We map commands to futures
                future_to_cmd = {executor.submit(execute_command, cmd, mute_output=False): cmd for cmd in step}
                
                step_failed = False
                for future in concurrent.futures.as_completed(future_to_cmd):
                    cmd = future_to_cmd[future]
                    try:
                        exit_code, output = future.result()
                        details += f"-- Cmd: {cmd}\nExit Code: {exit_code}\nOutput:\n{output}\n"
                        if exit_code != 0:
                            step_failed = True
                    except Exception as exc:
                        details += f"-- Cmd: {cmd} generated an exception: {exc}\n"
                        step_failed = True
                
                full_output.append(details)
                if step_failed:
                    print(f"{RED}One or more parallel commands failed. Stopping plan execution.{NC}")
                    overall_exit_code = 1
                    break
                    
    return overall_exit_code, "\n".join(full_output)

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
    
    # Ensure API key is configured (prompt on first run)
    config.ensure_api_key()
    
    # Initialize DB
    try:
        db.init_db()
    except Exception:
        pass

    while True:
        try:
            cwd_str = os.getcwd().replace(os.path.expanduser("~"), "~")
            ai_input = input(f"{BLUE}{cwd_str} AI> {NC}")
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
        plan = result.get('plan')
        inverse = result.get('inverse')
        safety_warning = result.get('safety_warning')

        if plan:
            print(f"{PURPLE}🤖 AI Proposed Plan:{NC}")
            for i, step in enumerate(plan):
                if len(step) > 1:
                    print(f"  {i+1}. [Parallel] {step}")
                else:
                    print(f"  {i+1}. {step[0]}")
        elif command:
            print(f"{PURPLE}🤖 AI: {command}{NC}")

        if safety_warning:
            print(f"{RED}WARNING: {safety_warning}{NC}")
            confirm = input(f"{YELLOW}Execute this? (y/n/i to edit): {NC}").strip().lower()
        else:
            # Auto-run safe commands
            confirm = 'y'
            
        if confirm == 'i' and command:
            print(f"{YELLOW}Edit command: {NC}", end='')
            print(f"(Copy/Paste the command to edit: {command})")
            new_command = input()
            if new_command.strip():
                command = new_command
            confirm = 'y'
        elif confirm == 'i' and plan:
            print(f"{RED}Editing complex plans is not yet supported. Proceed or cancel.{NC}")
            confirm = input(f"{YELLOW}Execute plan? (y/n): {NC}").strip().lower()

        if confirm == 'y':
            session_id = db.get_latest_session_id()
            
            if plan:
                exit_code, output = execute_plan(plan)
                db.add_history(session_id, ai_input, json.dumps({"plan": plan}), inverse, exit_code, output)
            elif command:
                exit_code, output = execute_command(command)
                db.add_history(session_id, ai_input, command, inverse, exit_code, output)
        else:
            print(f"{RED}Command cancelled{NC}")

if __name__ == "__main__":
    main()
