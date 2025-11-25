import sys
import json
import re

DANGER_PATTERNS = [
    r'rm\s+-rf\s+/',
    r'sudo\s+rm',
    r'dd\s+if=.*of=/dev/',
    r'mkfs',
    r'chmod\s+-R\s+777',
    r':\(\)\{ :\|:& \};:',
]

def safety_check(command):
    for pattern in DANGER_PATTERNS:
        if re.search(pattern, command):
            return False
    return True

def main():
    try:
       
        raw_input = sys.stdin.read()
        if not raw_input:
            print("Error: No input received from API", file=sys.stderr)
            sys.exit(1)

        data = json.loads(raw_input)

        if 'error' in data:
            print(f"API Error: {data['error'].get('message', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)

        if 'candidates' not in data or not data['candidates']:
            if 'promptFeedback' in data and 'blockReason' in data['promptFeedback']:
                 print(f"Blocked by safety filters: {data['promptFeedback']['blockReason']}", file=sys.stderr)
                 sys.exit(1)
            print("Error: No candidates returned from API", file=sys.stderr)
            sys.exit(1)

        candidate = data['candidates'][0]
        if 'content' not in candidate:
             print("Error: No content in candidate", file=sys.stderr)
             sys.exit(1)
        
        command = candidate['content']['parts'][0]['text'].strip()

        command = re.sub(r'^```\w*\n', '', command)
        command = re.sub(r'\n```$', '', command)
        command = command.strip()

        if safety_check(command):
            print(command)
            sys.exit(0)
        else:
            print(f"Safety Violation: Command '{command}' contains dangerous patterns.", file=sys.stderr)
            sys.exit(1)

    except json.JSONDecodeError:
        print("Error: Failed to parse API response", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()