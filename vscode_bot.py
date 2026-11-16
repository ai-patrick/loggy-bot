#!/usr/bin/env python3
"""
VS Code Coding Bot
Automates VS Code to create, write, save, and execute a Python file.

Requirements:
    pip install pyautogui pyperclip

Usage:
    python vscode_bot.py
"""

import subprocess
import time
import sys
import platform
import pyautogui
import pyperclip

# =============================================================================
# CONFIGURATION - Adjust these based on your system performance
# =============================================================================
DELAY_SHORT = 0.5      # Short delays (ms)
DELAY_MEDIUM = 1.0     # Medium delays (ms)
DELAY_LONG = 2.0       # Long delays (ms)
DELAY_VS_CODE_STARTUP = 3.0  # Time for VS Code to fully launch

# Code snippet to write (customize as needed)
CODE_SNIPPET = '''def hello_world():
    """Prints a friendly greeting."""
    print("Hello, World!")
    print("This code was written by the VS Code Coding Bot!")

if __name__ == "__main__":
    hello_world()
'''

# Output filename
OUTPUT_FILENAME = "bot_output.py"

# =============================================================================
# PLATFORM-SPECIFIC CONFIGURATION
# =============================================================================
OS_NAME = platform.system().lower()

# Key mappings for different OS
if OS_NAME == "darwin":  # macOS
    MOD_KEY = "command"
    NEW_FILE_SHORTCUT = ["command", "n"]
    SAVE_SHORTCUT = ["command", "s"]
    TERMINAL_SHORTCUT = ["control", "`"]  # Ctrl+` on macOS
    RUN_COMMAND = f"python3 {OUTPUT_FILENAME}"
elif OS_NAME == "windows":
    MOD_KEY = "ctrl"
    NEW_FILE_SHORTCUT = ["ctrl", "n"]
    SAVE_SHORTCUT = ["ctrl", "s"]
    TERMINAL_SHORTCUT = ["ctrl", "`"]
    RUN_COMMAND = f"python {OUTPUT_FILENAME}"
else:  # Linux
    MOD_KEY = "ctrl"
    NEW_FILE_SHORTCUT = ["ctrl", "n"]
    SAVE_SHORTCUT = ["ctrl", "s"]
    TERMINAL_SHORTCUT = ["ctrl", "`"]
    RUN_COMMAND = f"python3 {OUTPUT_FILENAME}"

# VS Code launch command
if OS_NAME == "darwin":
    VSCODE_CMD = ["code", "."]
elif OS_NAME == "windows":
    VSCODE_CMD = ["code", "."]
else:
    VSCODE_CMD = ["code", "."]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def safe_sleep(seconds: float) -> None:
    """Sleep with a small buffer for safety."""
    time.sleep(seconds + 0.1)

def press_keys(keys: list, interval: float = 0.05) -> None:
    """Press a combination of keys (e.g., ['ctrl', 's'])."""
    try:
        pyautogui.hotkey(*keys, interval=interval)
        safe_sleep(DELAY_SHORT)
    except Exception as e:
        print(f"[ERROR] Failed to press keys {keys}: {e}")
        sys.exit(1)

def type_text(text: str, interval: float = 0.01) -> None:
    """Type text using pyautogui (fallback to clipboard for large text)."""
    try:
        # For longer text, use clipboard paste for reliability
        if len(text) > 100:
            pyperclip.copy(text)
            press_keys([MOD_KEY, "v"])
        else:
            pyautogui.write(text, interval=interval)
        safe_sleep(DELAY_SHORT)
    except Exception as e:
        print(f"[ERROR] Failed to type text: {e}")
        sys.exit(1)

def launch_vscode() -> None:
    """Launch VS Code in the current directory."""
    print("[INFO] Launching VS Code...")
    try:
        # Use subprocess.Popen to not block
        subprocess.Popen(VSCODE_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[INFO] Waiting {DELAY_VS_CODE_STARTUP}s for VS Code to start...")
        safe_sleep(DELAY_VS_CODE_STARTUP)
    except FileNotFoundError:
        print("[ERROR] 'code' command not found. Please install VS Code and ensure 'code' is in PATH.")
        print("  - Windows: Reinstall VS Code with 'Add to PATH' checked")
        print("  - macOS: Run 'Shell Command: Install code command in PATH' from Command Palette")
        print("  - Linux: Install via package manager or add to PATH manually")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to launch VS Code: {e}")
        sys.exit(1)

def create_new_file() -> None:
    """Create a new file in VS Code (Ctrl/Cmd + N)."""
    print("[INFO] Creating new file...")
    press_keys(NEW_FILE_SHORTCUT)
    safe_sleep(DELAY_MEDIUM)

def write_code() -> None:
    """Write the code snippet into the editor."""
    print("[INFO] Writing code snippet...")
    type_text(CODE_SNIPPET)
    safe_sleep(DELAY_MEDIUM)

def save_file(filename: str = OUTPUT_FILENAME) -> None:
    """Save the file with the given filename (Ctrl/Cmd + S)."""
    print(f"[INFO] Saving file as '{filename}'...")
    press_keys(SAVE_SHORTCUT)
    safe_sleep(DELAY_MEDIUM)
    
    # Type filename in save dialog
    type_text(filename)
    safe_sleep(DELAY_SHORT)
    
    # Press Enter to confirm save
    pyautogui.press("enter")
    safe_sleep(DELAY_MEDIUM)

def open_terminal() -> None:
    """Open the integrated terminal (Ctrl/Cmd + `)."""
    print("[INFO] Opening integrated terminal...")
    press_keys(TERMINAL_SHORTCUT)
    safe_sleep(DELAY_MEDIUM)

def run_code() -> None:
    """Run the Python file in the terminal."""
    print(f"[INFO] Running '{RUN_COMMAND}'...")
    type_text(RUN_COMMAND)
    safe_sleep(DELAY_SHORT)
    pyautogui.press("enter")
    safe_sleep(DELAY_LONG)  # Give time for execution

# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def main():
    print("=" * 60)
    print("VS CODE CODING BOT - Starting Automation")
    print("=" * 60)
    print(f"[INFO] Platform: {OS_NAME}")
    print(f"[INFO] Output file: {OUTPUT_FILENAME}")
    print(f"[INFO] Modifier key: {MOD_KEY}")
    print("-" * 60)
    
    # Safety check - give user time to cancel
    print("[WARNING] Starting in 3 seconds... Switch to desktop if needed!")
    print("[WARNING] Press Ctrl+C to cancel.")
    for i in range(3, 0, -1):
        print(f"       {i}...")
        time.sleep(1)
    
    try:
        # Step 1: Launch VS Code
        launch_vscode()
        
        # Step 2: Create new file
        create_new_file()
        
        # Step 3: Write code
        write_code()
        
        # Step 4: Save file
        save_file()
        
        # Step 5: Open terminal
        open_terminal()
        
        # Step 6: Run code
        run_code()
        
        print("-" * 60)
        print("[SUCCESS] Automation completed!")
        print(f"[INFO] Check the terminal output in VS Code for 'Hello, World!'")
        
    except KeyboardInterrupt:
        print("\n[INFO] Automation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # PyAutoGUI safety features
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.1      # Small pause between actions
    
    main()