# ktml-agent

A powerful AI-powered terminal assistant that translates natural language into shell commands. Works on Windows, macOS, and Linux.

## Features

- **Natural Language to Shell**: Just describe what you want to do in plain English
- **Safety First**: Dangerous commands are automatically flagged and require explicit confirmation
- **Undo Support**: Automatically generates inverse commands to undo your last action
- **Intelligent Caching**: Remembers similar queries for faster responses
- **Session Tracking**: Maintains command history with exit codes and outputs
- **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux
- **Privacy Focused**: Runs locally using your own Gemini API key

## Installation

Install via pip:

```bash
pip install ktml-agent
```

## First Run Setup

The first time you run `agent`, you'll be prompted to enter your Gemini API key:

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key and paste it when prompted

Your API key will be securely saved to `~/.config/ktml-agent/config`.

## Usage

### Basic Usage

1. Type `agent` to enter AI mode
2. Describe what you want to do in natural language:
   - "List all python files modified yesterday"
   - "Find the largest file in this directory"
   - "Show me the git commit history for the last week"
   - "Create a backup of all .txt files"
3. Review the suggested command
4. Safe commands auto-execute; dangerous commands require confirmation (`y`/`n`/`i` to edit)
5. Type `exit` to leave AI mode

### Undo Feature

Made a mistake? Just type `undo` to reverse your last command:

```
AI> undo
```

The agent automatically generates inverse commands when possible (e.g., `mkdir` → `rmdir`).

### Command Editing

If you want to modify a suggested command before executing:

1. When prompted, type `i` to edit
2. Copy and modify the command
3. Press Enter to execute the edited version

## Configuration

### Configuration File

Location: `~/.config/ktml-agent/config`

The configuration file stores your API key:

```
GEMINI_API_KEY=your_key_here
```

### Environment Variable

Alternatively, you can set the API key as an environment variable:

```bash
export GEMINI_API_KEY=your_key_here
```

## How It Works

1. **Context Gathering**: Analyzes your current directory, OS, and shell environment
2. **AI Translation**: Uses Google's Gemini API to translate your request into shell commands
3. **Safety Check**: Scans for dangerous patterns (e.g., `rm -rf`, `dd`, `shutdown`)
4. **Execution**: Runs safe commands automatically; prompts for dangerous ones
5. **History Tracking**: Stores commands, outputs, and exit codes in a local SQLite database
6. **Caching**: Remembers similar queries for instant responses

## Data Storage

- **Configuration**: `~/.config/ktml-agent/config`
- **Database**: `~/.ai_terminal/brain.db` (SQLite)
  - Command history
  - Session tracking
  - Query cache

## Requirements

- Python 3.8 or higher
- Internet connection (for Gemini API calls)
- Gemini API key (free tier available)

## Safety Features

The agent includes built-in protection against dangerous commands:

- `rm -rf` (recursive deletion)
- `dd` operations on devices
- `chmod 777` (insecure permissions)
- System shutdown/reboot commands
- Piping to shell from web (`curl | sh`)
- And more...

Dangerous commands are flagged with a warning and require explicit confirmation.

## Development

### Project Structure

```
kernel/
├── src/
│   └── ai_kernel/
│       ├── main.py       # Entry point and CLI interface
│       ├── core.py       # AI processing and command generation
│       ├── config.py     # Configuration and API key management
│       ├── db.py         # Database operations and caching
│       └── session.py    # Session management
├── pyproject.toml        # Package configuration
└── README.md
```

### Building from Source

```bash
git clone <repository-url>
cd kernel
pip install -e .
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Troubleshooting

### API Key Issues

If you need to reset your API key:

```bash
rm ~/.config/ktml-agent/config
agent  # Will prompt for API key again
```

### Database Issues

If you encounter database errors:

```bash
rm ~/.ai_terminal/brain.db
agent  # Will recreate the database
```

## Credits

Powered by Google's Gemini API
