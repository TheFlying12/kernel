#!/bin/bash

# run: chmod +x ai_shell.sh && ./ai_shell.sh

source .env
source colors.sh

echo -e "${BLUE}Type 'agent' to enter AI mode, 'exit' to quit${NC}"
echo "----------------------------------------"

ai_mode() {
    echo ""
    echo -e "${GREEN}You can now interact with the AI assistant.${NC}"
    echo -e "${GREEN}Type 'exit' to quit entirely${NC}"
    echo ""
    
    while true; do
        echo -ne "${BLUE}AI> ${NC}"
        read -r ai_input
        
        if [[ "$ai_input" == "exit" ]]; then
            exit 0
        elif [[ -z "$ai_input" ]]; then
            echo -e "${YELLOW}Please enter a command${NC}"
        else
            # Call the Python core (handles API, Context, Safety)
            # Capture stdout (command) and stderr (warnings/errors)
            # We use a temp file for stderr to keep it clean
            echo "Pre calling ai_core.py"
            output=$(./ai_core.py "$ai_input" 2> /tmp/ai_error.log)
            echo $output
            exit_code=$?
            echo "Post calling ai_core.py"

            # Check for safety warnings or errors
            if [[ -s /tmp/ai_error.log ]]; then
                echo -e "${RED}$(cat /tmp/ai_error.log)${NC}"
            fi

            if [[ $exit_code -eq 0 ]]; then
                result="$output"
                echo -e "${PURPLE}🤖 AI: $result${NC}"
                #echo -e "${CYAN}🤖 Suggested command: $result${NC}"
                echo -ne "${YELLOW}Execute this command? (y/n/i to edit): ${NC}"
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
                else
                    echo -e "${RED}Command cancelled${NC}"
                fi
            else
                # Error or safety violation occurred
                echo -e "${RED}$result${NC}"
            fi

        fi
    done
}

# Main shell loop
while true; do
    read -r input
    if [[ "$input" == "agent" ]]; then
        ai_mode
    elif [[ "$input" == "exit" ]]; then
        break
    else
        echo -e "${RED}Invalid command${NC}"
    fi
done