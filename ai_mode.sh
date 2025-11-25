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
            # integrate with an actual AI API here
            echo -e "${PURPLE}🤖 AI: Processing '$ai_input'...${NC}"

            response=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
                        -H "x-goog-api-key: $GEMINI_API_KEY" \
                        -H 'Content-Type: application/json' \
                        -X POST \
                        -d '{
                            "systemInstruction": {"parts": [{"text": "You are a terminal command generator. Generate only the shell command needed, no explanations or markdown. Be concise, and as directly related to the query as you possibly can. "}]},
                            "contents": [{"role": "user", "parts": [{"text": "'"$ai_input"'"}]}],
                            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100, "thinkingConfig": {"thinkingBudget": 0}},
                        }')

            #echo "🤖 Raw Response: $response"

            # Correct Gemini parsing:
            result=$(echo "$response" | jq -r '.candidates[0].content.parts[0].text')
            echo -e "${PURPLE}🤖 AI: $result${NC}"

            echo -e "${CYAN}🤖 Suggested command: $result${NC}"
            echo -ne "${YELLOW}Execute this command? (y/n): ${NC}"
            read -r confirmInput
            #echo $result
            echo $confirmInput
            if [[ "${confirmInput}" == "y" || "${confirmInput}" == "Y" ]]; then
                eval "$result"
            else
                echo -e "${RED}Command cancelled${NC}"
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