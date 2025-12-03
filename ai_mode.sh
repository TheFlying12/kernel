# #!/bin/bash

# SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# source "$SCRIPT_DIR/colors.sh"


# echo "${BLUE}Ask Away!!${NC}"
# echo "----------------------------------------"

# ai_mode() {
#     #echo ""
#     #echo "${GREEN}You can now interact with the AI assistant.${NC}"
#     #echo "${GREEN}Type 'exit' to quit entirely${NC}"
#     #echo ""
    
#     while true; do
#         printf "${BLUE}AI> ${NC}"
#         read -r ai_input
        
#         if [[ "$ai_input" == "exit" ]]; then
#             exit 0
#         elif [[ "$ai_input" == "undo" ]]; then
#             # Undo Logic
#             # Fetch the last inverse command from DB
#             undo_cmd=$(python -c "import sys; sys.path.append('$SCRIPT_DIR'); import db; h=db.get_recent_history(1); print(h[0]['inverse'] if h and 'inverse' in h[0] else '')")
            
#             if [[ -z "$undo_cmd" ]]; then
#                 printf "${RED}Nothing to undo.${NC}\n"
#                 continue
#             fi
            
#             printf "${PURPLE}🤖 Undo: $undo_cmd${NC}\n"
            
#             # Allow editing for Undo
#             if [ -n "$ZSH_VERSION" ]; then
#                 vared -p "${YELLOW}Edit undo (Enter to execute): ${NC}" -c undo_cmd
#             elif command -v zsh >/dev/null 2>&1; then
#                 undo_cmd=$(PREFILLED="$undo_cmd" zsh -f -i -c 'vared -p "Edit undo (Enter to execute): " -c PREFILLED; echo -n "$PREFILLED"')
#             else
#                 read -e -p "Edit undo (Enter to execute): " -i "$undo_cmd" undo_cmd
#             fi
            
#             if [[ -n "$undo_cmd" ]]; then
#                 # Capture output of undo
#                 exec_out=$(eval "$undo_cmd" 2>&1)
#                 exec_code=$?
#                 echo "$exec_out"
                
#                 python "$SCRIPT_DIR/update_session.py" "undo" "$undo_cmd" "" "$exec_code" "$exec_out"
#             else
#                 printf "${RED}Undo cancelled${NC}\n"
#             fi
#             continue
            
#         elif [[ -z "$ai_input" ]]; then
#             printf "${YELLOW}Please enter a command${NC}\n"
#         else
#             # Call the Python core (handles API, Context, Safety)
#             # Capture stdout (command) and stderr (warnings/errors)
#             # We use a temp file for stderr to keep it clean
#             output=$("$SCRIPT_DIR/ai_core.py" "$ai_input" 2> /tmp/ai_error.log)
#             echo $output
#             exit_code=$?

#             # Check for safety warnings or errors
#             if [[ -s /tmp/ai_error.log ]]; then
#                 printf "${RED}$(cat /tmp/ai_error.log)${NC}\n"
#             fi

#             if [[ $exit_code -eq 0 ]]; then
#                 # Split output into Command and Inverse
#                 # output format: COMMAND|INVERSE
#                 IFS='|' read -r result inverse_cmd <<< "$output"
                
#                 # If no pipe found, result is the whole output, inverse is empty
#                 if [[ -z "$result" && -n "$output" ]]; then
#                     result="$output"
#                 fi
                
#                 printf "${PURPLE}🤖 AI: $result${NC}\n"
                
#                 # Check for safety warning in stderr log
#                 is_safe=true
#                 if [[ -s /tmp/ai_error.log ]]; then
#                     if grep -q "WARNING" /tmp/ai_error.log; then
#                         is_safe=false
#                     fi
#                 fi
                
#                 confirmInput="y"
#                 if [[ "$is_safe" == "false" ]]; then
#                      printf "${YELLOW}Execute this command? (y/n/i to edit): ${NC}"
#                      read -r confirmInput
#                 fi
                
#                 if [[ "${confirmInput}" == "i" || "${confirmInput}" == "I" ]]; then
#                     # Check if running in Zsh
#                     if [ -n "$ZSH_VERSION" ]; then
#                         # Zsh editing
#                         vared -p "${YELLOW}Edit command: ${NC}" -c result
#                     elif command -v zsh >/dev/null 2>&1; then
#                         # Bash on macOS (or Linux with zsh installed)
#                         # Use zsh to handle the editing because Bash 3.2 (macOS default) is limited
#                         result=$(PREFILLED="$result" zsh -f -i -c 'vared -p "Edit command: " -c PREFILLED; echo -n "$PREFILLED"')
#                     else
#                         # Fallback for Bash without Zsh
#                         read -e -p "Edit command: " -i "$result" result
#                     fi
                    
#                     confirmInput="y"
#                 fi

#                 if [[ "${confirmInput}" == "y" || "${confirmInput}" == "Y" ]]; then
#                     # Execute and capture output (stdout + stderr combined)
#                     # We use a trick to print to screen AND capture to variable
#                     # But for simplicity in shell, let's just run it and redirect to a temp file to read back
                    
#                     eval "$result" > /tmp/ai_exec.log 2>&1
#                     exec_code=$?
#                     cat /tmp/ai_exec.log
#                     exec_out=$(cat /tmp/ai_exec.log)
                    
#                     # Update history with output and exit code
#                     python "$SCRIPT_DIR/update_session.py" "$ai_input" "$result" "$inverse_cmd" "$exec_code" "$exec_out"
#                 else
#                     printf "${RED}Command cancelled${NC}\n"
#                 fi
#             else
#                 # Error or safety violation occurred
#                 printf "${RED}$result${NC}\n"
#             fi

#         fi
#     done
# }

# # Start AI mode immediately
# ai_mode