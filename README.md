# Loggy Bot - VS Code Automation & Self-Correcting Coding Agent

This repository contains two autonomous coding tools:

1. **VS Code Coding Bot** - UI automation for writing and running code in VS Code
2. **Self-Correcting Coding Bot** - AI-powered agent that generates, tests, and fixes code using NVIDIA API

## Features

- **Two Versions**:
  - **CLI Version** (`vscode_bot_cli.py`) - Works on **Wayland & X11** ✅
  - **GUI Version** (`vscode_bot.py`) - Requires **X11** (Linux) / Works on Windows & macOS
- Creates a Python file with a customizable code snippet
- Saves the file with a configurable name
- Opens VS Code's integrated terminal
- Runs the code automatically

## Quick Start

```bash
# Clone the repo
git clone https://github.com/ai-patrick/loggy-bot.git
cd loggy-bot

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install pyautogui pyperclip

# Run the CLI version (recommended for Wayland/Linux)
python vscode_bot_cli.py
```

## Version Comparison

| Feature | CLI Version (`vscode_bot_cli.py`) | GUI Version (`vscode_bot.py`) |
|---------|-----------------------------------|-------------------------------|
| **Wayland Support** | ✅ Yes | ❌ No (requires X11) |
| **X11 Support** | ✅ Yes | ✅ Yes |
| **Windows Support** | ✅ Yes | ✅ Yes |
| **macOS Support** | ✅ Yes | ✅ Yes |
| **File Operations** | VS Code CLI (`code` command) | PyAutoGUI keystrokes |
| **Terminal Control** | PyAutoGUI (optional) | PyAutoGUI (required) |
| **Reliability** | High (CLI-based) | Medium (timing-dependent) |

## Requirements

- **Python 3.8+**
- **VS Code** with `code` CLI installed:
  - **Windows**: Reinstall VS Code with "Add to PATH" checked
  - **macOS**: `Cmd+Shift+P` → "Shell Command: Install 'code' command in PATH"
  - **Linux**: Usually installed automatically (`code` in PATH)
- **Dependencies**: `pyautogui`, `pyperclip` (installed via pip)

## Installation

### Linux (Arch/Manjaro)
```bash
# System dependencies for pyautogui (X11)
sudo pacman -S python-xlib scrot

# Or for Ubuntu/Debian
sudo apt-get install python3-xlib scrot
```

### macOS
```bash
# Grant Accessibility permissions after first run:
# System Settings → Privacy & Security → Accessibility
# Enable: Terminal, Python, Visual Studio Code
```

### Windows
```bash
# No additional system dependencies needed
# Ensure VS Code is in PATH during installation
```

## Usage

### CLI Version (Recommended for Linux/Wayland)
```bash
source venv/bin/activate
python vscode_bot_cli.py
```
- Uses VS Code CLI for file creation (works on Wayland)
- Falls back to GUI automation only for terminal interaction
- If GUI unavailable, prints manual commands to run

### GUI Version (Windows/macOS/X11 Linux)
```bash
source venv/bin/activate
python vscode_bot.py
```
- Fully automated via PyAutoGUI keystrokes
- Requires X11 on Linux (won't work on pure Wayland)

## Configuration

Edit the **CONFIGURATION** section at the top of either script:

```python
# Timing (adjust for your system speed)
DELAY_SHORT = 0.5
DELAY_MEDIUM = 1.0
DELAY_LONG = 2.0
DELAY_VS_CODE_STARTUP = 3.0

# Code to write
CODE_SNIPPET = '''def hello_world():
    print("Hello, World!")'''

# Output filename
OUTPUT_FILENAME = "bot_output.py"
```

## How It Works

### CLI Version Flow
1. Launches VS Code via `code . --new-window`
2. Writes code to file directly using Python `open()`
3. Opens file in VS Code via `code --reuse-window filepath`
4. Opens terminal with `Ctrl+\`` (GUI)
5. Types and runs `python3 bot_output.py` (GUI)

### GUI Version Flow
1. Launches VS Code via `subprocess.Popen(["code", "."])`
2. `Ctrl+N` → New file
3. `pyautogui.write()` → Types code
4. `Ctrl+S` → Save dialog → Types filename → `Enter`
5. `Ctrl+\`` → Opens terminal
6. Types `python bot_output.py` → `Enter`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `code` command not found | Install VS Code CLI (see Requirements) |
| "Can't connect to display" | Use CLI version, or switch to X11 session |
| Keys not registering | Increase `DELAY_*` values |
| Terminal doesn't open | Press `Ctrl+\`` manually first to initialize |
| Permission denied (macOS) | Grant Accessibility access to Terminal/Python/VS Code |
| Wayland + GUI version fails | Use CLI version instead |

## Switching to X11 (for GUI version on Linux)

1. Log out
2. Click gear icon at login screen
3. Select **"GNOME on Xorg"** or **"Ubuntu on Xorg"**
4. Log in

## Safety Features

- **PyAutoGUI Failsafe**: Move mouse to top-left corner (0,0) to emergency stop
- **3-second countdown** before starting
- **Ctrl+C** to cancel at any time

## License

MIT License - Feel free to use and modify.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## Self-Correcting Coding Bot (`self_correcting_coding_bot.py`)

A fully autonomous AI coding agent that:
- Takes a high-level programming goal from the user
- Uses **NVIDIA API** (via OpenAI SDK) to generate code iteratively
- Writes files to disk and opens them in **VS Code** for live viewing
- Executes code, captures errors, and **self-corrects** automatically
- Runs purely on CLI/API operations (no GUI automation required)

### Features

- **Autonomous Loop**: Goal → Generate → Write → Execute → Fix → Repeat
- **Structured JSON Output**: LLM forced to return valid JSON with `thought_process`, `filename`, `code_content`, `next_step`, `status`
- **Self-Correction**: On execution error, feeds stderr back to LLM to fix the same file
- **VS Code Integration**: Opens each generated file via `code --reuse-window`
- **Safety Limits**: `MAX_ITERATIONS` (default 20), execution timeout, graceful Ctrl+C handling
- **Complete Context**: Maintains project files, execution history, and conversation state

### Quick Start

```bash
# Clone and setup
git clone https://github.com/ai-patrick/loggy-bot.git
cd loggy-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure API (get key from https://build.nvidia.com/)
cp .env.example .env
# Edit .env with your NVIDIA_API_KEY

# Run the bot
python self_correcting_coding_bot.py
```

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_ITERATIONS` | Hard limit on agent loops | 20 |
| `EXECUTION_TIMEOUT` | Seconds before killing script | 30 |
| `VSCODE_REUSE_WINDOW` | Use `--reuse-window` flag | true |
| `NVIDIA_API_URL` | NVIDIA API endpoint | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_DEFAULT_MODEL` | Model to use | `nvidia/nemotron-3-ultra` |

### How the Self-Correction Loop Works

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT LOOP                                │
├─────────────────────────────────────────────────────────────┤
│  1. USER GOAL                                                │
│     ↓                                                        │
│  2. LLM GENERATES (JSON)                                     │
│     - thought_process: reasoning                             │
│     - filename: target file                                  │
│     - code_content: complete file                            │
│     - next_step: what to do next                             │
│     - status: continue/complete/error                        │
│     ↓                                                        │
│  3. WRITE FILE → OPEN IN VS CODE                             │
│     ↓                                                        │
│  4. EXECUTE (python3 filename)                               │
│     ↓                                                        │
│  5a. SUCCESS → Save output → LLM plans NEXT step            │
│  5b. ERROR   → Feed stderr to LLM → LLM FIXES same file     │
│     ↓                                                        │
│  6. REPEAT until status="complete" or MAX_ITERATIONS        │
└─────────────────────────────────────────────────────────────┘
```

### Example Goals

```bash
# Simple script
"Create a Python script that calculates prime numbers up to N and tests it"

# With tests
"Build a TODO list CLI app with add/list/remove commands and JSON persistence"

# Multi-file project
"Create a Flask REST API with user authentication (register/login) and SQLite database"
```

### Requirements

- **Python 3.8+**
- **VS Code** with `code` CLI in PATH
- **NVIDIA API Key** from [build.nvidia.com](https://build.nvidia.com/)
- **Dependencies**: `openai>=1.0.0`, `python-dotenv>=1.0.0`

### Environment Variables (`.env`)

```bash
NVIDIA_API_KEY=your_api_key_here
NVIDIA_API_URL=https://integrate.api.nvidia.com/v1
NVIDIA_DEFAULT_MODEL=nvidia/nemotron-3-ultra
```

### Safety Features

- **MAX_ITERATIONS**: Hard limit prevents infinite loops / credit burn
- **Execution Timeout**: Kills runaway scripts (default 30s)
- **Graceful Shutdown**: Ctrl+C finishes current iteration then exits
- **No PyAutoGUI**: Pure CLI/API - works on Wayland, headless servers, CI/CD
- **JSON Schema Enforcement**: `response_format={"type": "json_object"}` guarantees parseable output

---

**Note**: The CLI version is recommended for modern Linux distributions running Wayland. The GUI version is maintained for compatibility with Windows, macOS, and X11-based Linux systems.