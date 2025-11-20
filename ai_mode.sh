#!/bin/bash

# run: chmod +x ai_shell.sh && ./ai_shell.sh

source .env

echo "Type 'agent' to enter AI mode, 'exit' to quit"
echo "----------------------------------------"

ai_mode() {
    echo ""
    echo "You can now interact with the AI assistant."
    echo "Type 'exit' to quit entirely"
    echo ""
    
    while true; do
        echo -n "AI> "
        read -r ai_input
        
        if [[ "$ai_input" == "exit" ]]; then
            exit 0
        elif [[ -z "$ai_input" ]]; then
            echo "Please enter a command"
        else
            # integrate with an actual AI API here
            echo "🤖 AI: Processing '$ai_input'..."


                # Line 29-45 should be:
            # response=$(curl -s "https://api.openai.com/v1/chat/completions" \
            #     -H "Content-Type: application/json" \
            #     -H "Authorization: Bearer sk-abcdef1234567890abcdef1234567890abcdef12" \
            #     -d '{
            #         "model": "gpt-5-nano",
            #         "messages": [
            #             {
            #                 "role": "system",
            #                 "content": "You are a terminal command generator. Generate only the shell command needed, no explanations or markdown. Be concise."
            #             },
            #             {
            #                 "role": "user",
            #                 "content": "list all files"
            #             }
            #         ],
            #         "temperature": 0.3
            #     }')

            response=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
                        -H "x-goog-api-key: $GEMINI_API_KEY" \
                        -H 'Content-Type: application/json' \
                        -X POST \
                        -d '{
                            "systemInstruction": {
                                "parts": [{"text": "Generate bash/zsh commands ONLY..."}]
                            },
                            "contents": [
                                {"role": "user", "parts": [{"text": "'"$ai_input"'"}]}
                            ],
                            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100, "thinkingConfig": {"thinkingBudget": 0}},
                            
                        }')

            echo "🤖 Raw Response: $response"

            # Correct Gemini parsing:
            result=$(echo "$response" | jq -r '.candidates[0].content.parts[0].text')
            echo "🤖 AI: $result"

            echo "🤖 Suggested command: $result"
            echo -n "Execute this command? (y/n): "
            read -r confirmInput
            if [[ "${confirmInput,,}" == "y" ]]; then
                eval "$result"
            else
                echo "Command cancelled"
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
        echo "Invalid command"
    fi
done