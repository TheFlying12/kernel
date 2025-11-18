#!/bin/bash

# run: chmod +x ai_shell.sh && ./ai_shell.sh

source .env

echo "Type 'agent' to enter AI mode, 'exit' to quit"
echo "----------------------------------------"

ai_mode() {
    echo ""
    echo "You can now interact with the AI assistant."
    echo "Type 'back' to return to normal shell mode"
    echo "Type 'exit' to quit entirely"
    echo ""
    
    while true; do
        echo -n "AI> "
        read -r ai_input
        
        if [[ "$ai_input" == "exit" ]]; then
            exit 0
        elif [[ -z "$ai_input" ]]; then
            continue
        else
            # integrate with an actual AI API here
            echo "🤖 AI: Processing '$ai_input'..."


                # Line 29-45 should be:
            # response=$(curl -s "https://api.openai.com/v1/chat/completions" \
            #     -H "Content-Type: application/json" \
            #     -H "Authorization: Bearer $OPENAI_API_KEY" \
            #     -d '{
            #         "model": "gpt-4-turbo",
            #         "messages": [
            #             {
            #                 "role": "system",
            #                 "content": "You are a terminal command generator. Generate only the shell command needed, no explanations or markdown. Be concise."
            #             },
            #             {
            #                 "role": "user",
            #                 "content": "'"$ai_input"'"
            #             }
            #         ]
            #     }')
            response=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent" \
                -H "x-goog-api-key: $GEMINI_API_KEY" \
                -H 'Content-Type: application/json' \
                -X POST \
                -d '{
                    "systemInstruction": {
                        "parts": [
                            {
                                "text": "Generate bash/zsh commands ONLY. Output the raw command with NO markdown, backticks, explanations, or formatting. Single line only.\n\nExamples:\nUser: list csv files → ls *.csv\nUser: disk usage sorted → du -sh * | sort -hr\nUser: find python files → find . -name \"*.py\""
                            }
                        ]
                    },
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": "'"$ai_input"'"}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 100
                    }
                }')
    echo "🤖 AI: $response"
    #result=$(echo "$response" | jq -r '.choices[0].message.content')
    #result=$(echo "$response" | python3 parse_response.py)
    #result=$(echo jq -r '.choices[0].message.content')
    result=$(echo "$response" | jq -r '.candidates[0].content.parts[0].text')
    echo "$result"
    read -p "Execute? (y/n) " execute
    if [[ "$execute" == "y" ]]; then
        eval "$result"
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
        continue
    fi
done