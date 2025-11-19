import os
import sys
import re

DANGER_PATTERNS = [
    r'rm\s+-rf\s+/',
    r'sudo\s+rm',
    r'dd\s+if=.*of=/dev/',
    r'mkfs',
    r'chmod\s+-R\s+777',
]

def safety_check(command):
    for pattern in DANGER_PATTERNS:
        if re.search(pattern, command):
            return False
    return True

print(safety_check("ls -l"))