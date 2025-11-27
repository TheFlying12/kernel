#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/colors.sh"


echo "${BLUE}Ask Away!!${NC}"
echo "----------------------------------------"

ai_mode() {
    #echo ""
    #echo "${GREEN}You can now interact with the AI assistant.${NC}"
    #echo "${GREEN}Type 'exit' to quit entirely${NC}"
    #echo ""
    
    while true; do
        printf "${BLUE}AI> ${NC}"
        read -r ai_input
        
        if [[ "$ai_input" == "exit" ]]; then
            exit 0
        elif [[ -z "$ai_input" ]]; then
            printf "${YELLOW}Please enter a command${NC}\n"
        else
            # Call the Python core (handles API, Context, Safety)
            # Capture stdout (command) and stderr (warnings/errors)
            # We use a temp file for stderr to keep it clean
            output=$("$SCRIPT_DIR/ai_core.py" "$ai_input" 2> /tmp/ai_error.log)
            echo $output
            exit_code=$?

            # Check for safety warnings or errors
            if [[ -s /tmp/ai_error.log ]]; then
                printf "${RED}$(cat /tmp/ai_error.log)${NC}\n"
            fi

            if [[ $exit_code -eq 0 ]]; then
                result="$output"
                printf "${PURPLE}🤖 AI: $result${NC}\n"
                #echo -e "${CYAN}🤖 Suggested command: $result${NC}"
                printf "${YELLOW}Execute this command? (y/n/i to edit): ${NC}"
                read -r confirmInput
                
                if [[ "${confirmInput}" == "i" || "${confirmInput}" == "I" ]]; then
                    # Check if running in Zsh
                    if [ -n "$ZSH_VERSION" ]; then
                        # Zsh editing
                        vared -p "${YELLOW}Edit command: ${NC}" -c result
                    elif command -v zsh >/dev/null 2>&1; then
                        # Bash on macOS (or Linux with zsh installed)
                        # Use zsh to handle the editing because Bash 3.2 (macOS default) is limited
                        result=$(PREFILLED="$result" zsh -f -i -c 'vared -p "Edit command: " -c PREFILLED; echo -n "$PREFILLED"')
                    else
                        # Fallback for Bash without Zsh
                        read -e -p "Edit command: " -i "$result" result
                    fi
                    
                    confirmInput="y"
                fi

                if [[ "${confirmInput}" == "y" || "${confirmInput}" == "Y" ]]; then
                    eval "$result"
                    # Update history only after successful execution
                    python3 "$SCRIPT_DIR/update_session.py" "$ai_input" "$result"
                else
                    printf "${RED}Command cancelled${NC}\n"
                fi
            else
                # Error or safety violation occurred
                printf "${RED}$result${NC}\n"
            fi

        fi
    done
}

# Start AI mode immediately
ai_mode