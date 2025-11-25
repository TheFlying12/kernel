# kernel.sh
# AI Terminal

A natural language terminal assistant that translates your English requests into shell commands.

## Features

- **Natural Language to Shell**: Just type what you want to do.
- **Safety First**: Dangerous commands (like `rm -rf`) are flagged, and all commands require confirmation.
- **Context Aware**: Runs in your current shell session, preserving directory and environment.
- **Privacy**: Runs locally (logic) and uses your own API key.

## Installation

1. Run the installer:
   ```bash
   ./install.sh
   ```
2. Restart your terminal or source your config (e.g., `source ~/.zshrc`).

## Usage

1. Type `agent` to enter AI mode.
2. Type your request, for example:
   - "List all python files modified yesterday"
   - "Find the largest file in this directory"
   - "Undo the last git commit"
3. Review the suggested command.
4. Type `y` to execute, or anything else to cancel.
5. Type `exit` to leave AI mode.

## Configuration

The configuration file is located at `~/.config/ai_terminal/config`.
You can set your API key there:
```
GEMINI_API_KEY=your_key_here
```
Alternatively, you can export `GEMINI_API_KEY` in your environment.

## Requirements

- Python 3
- Bash or Zsh
- Gemini API Key
