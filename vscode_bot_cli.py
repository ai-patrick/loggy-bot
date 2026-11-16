#!/usr/bin/env python3
"""
VS Code Coding Bot - CLI Version (Works on Wayland)
Uses VS Code CLI for file operations, GUI automation only for terminal.

Requirements:
    pip install pyautogui pyperclip

Usage:
    python vscode_bot_cli.py
"""

import subprocess
import time
import sys
import platform
import tempfile
import os

# Try to import GUI automation (optional, for terminal) - lazy import to avoid X11 issues on Wayland
GUI_AVAILABLE = False
pyautogui = None
pyperclip = None

def _init_gui():
    """Initialize GUI automation modules."""
    global GUI_AVAILABLE, pyautogui, pyperclip
    if GUI_AVAILABLE:
        return True
    try:
        import pyautogui as _pyautogui
        import pyperclip as _pyperclip
        pyautogui = _pyautogui
        pyperclip = _pyperclip
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        GUI_AVAILABLE = True
        return True
    except Exception as e:
        print(f"[WARN] GUI automation unavailable: {e}")
        GUI_AVAILABLE = False
        return False

# =============================================================================
# CONFIGURATION
# =============================================================================
DELAY_SHORT = 0.5
DELAY_MEDIUM = 1.0
DELAY_LONG = 2.0
DELAY_VS_CODE_STARTUP = 3.0

CODE_SNIPPET = '''def hello_world():
    """Prints a friendly greeting."""
    print("Hello, World!")
    print("This code was written by the VS Code Coding Bot!")

if __name__ == "__main__":
    hello_world()
'''

OUTPUT_FILENAME = "bot_output.py"

OS_NAME = platform.system().lower()

# Platform-specific commands
if OS_NAME == "darwin":
    MOD_KEY = "command"
    TERMINAL_SHORTCUT = ["control", "`"]
    RUN_COMMAND = f"python3 {OUTPUT_FILENAME}"
elif OS_NAME == "windows":
    MOD_KEY = "ctrl"
    TERMINAL_SHORTCUT = ["ctrl", "`"]
    RUN_COMMAND = f"python {OUTPUT_FILENAME}"
else:
    MOD_KEY = "ctrl"
    TERMINAL_SHORTCUT = ["ctrl", "`"]
    RUN_COMMAND = f"python3 {OUTPUT_FILENAME}"

VSCODE_CMD = ["code"]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def safe_sleep(seconds: float) -> None:
    time.sleep(seconds + 0.1)

def press_keys(keys: list) -> None:
    if not _init_gui():
        print(f"[SKIP] Would press: {keys} (GUI not available)")
        return
    try:
        pyautogui.hotkey(*keys, interval=0.05)
        safe_sleep(DELAY_SHORT)
    except Exception as e:
        print(f"[ERROR] Failed to press keys {keys}: {e}")

def type_text(text: str) -> None:
    if not _init_gui():
        print(f"[SKIP] Would type: {text[:50]}... (GUI not available)")
        return
    try:
        if len(text) > 100:
            pyperclip.copy(text)
            press_keys([MOD_KEY, "v"])
        else:
            pyautogui.write(text, interval=0.01)
        safe_sleep(DELAY_SHORT)
    except Exception as e:
        print(f"[ERROR] Failed to type text: {e}")

# =============================================================================
# CLI-BASED OPERATIONS (Work on Wayland)
# =============================================================================

def launch_vscode_cli() -> None:
    """Launch VS Code using CLI."""
    print("[INFO] Launching VS Code via CLI...")
    try:
        # Launch VS Code in background with current directory
        subprocess.Popen(VSCODE_CMD + [".", "--new-window"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[INFO] Waiting {DELAY_VS_CODE_STARTUP}s for VS Code to start...")
        safe_sleep(DELAY_VS_CODE_STARTUP)
    except FileNotFoundError:
        print("[ERROR] 'code' command not found. Install VS Code and add to PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to launch VS Code: {e}")
        sys.exit(1)

def create_file_via_cli(filepath: str, content: str) -> bool:
    """Create file using VS Code CLI (works on Wayland)."""
    print(f"[INFO] Creating file via CLI: {filepath}")
    try:
        # Write content to temp file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Use VS Code to open the temp file, then save as target
        # Actually, simpler: just write directly and open
        with open(filepath, 'w') as f:
            f.write(content)
        
        # Open the file in VS Code
        subprocess.run(VSCODE_CMD + ["--reuse-window", filepath], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        safe_sleep(DELAY_MEDIUM)
        print(f"[SUCCESS] File created and opened: {filepath}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create file via CLI: {e}")
        return False

def open_terminal_gui() -> None:
    """Open integrated terminal using GUI automation."""
    if not GUI_AVAILABLE:
        print("[INFO] GUI not available - please open terminal manually (Ctrl+`)")
        return
    
    print("[INFO] Opening integrated terminal...")
    press_keys(TERMINAL_SHORTCUT)
    safe_sleep(DELAY_MEDIUM)

def run_code_gui() -> None:
    """Run the Python file in terminal using GUI automation."""
    if not _init_gui():
        print(f"[INFO] GUI not available - please run manually: {RUN_COMMAND}")
        return
    
    print(f"[INFO] Running '{RUN_COMMAND}'...")
    type_text(RUN_COMMAND)
    safe_sleep(DELAY_SHORT)
    pyautogui.press("enter")
    safe_sleep(DELAY_LONG)

# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def main():
    print("=" * 60)
    print("VS CODE CODING BOT - CLI Version (Wayland Compatible)")
    print("=" * 60)
    print(f"[INFO] Platform: {OS_NAME}")
    print(f"[INFO] Output file: {OUTPUT_FILENAME}")
    print(f"[INFO] GUI Automation: {'Available' if GUI_AVAILABLE else 'Not Available'}")
    print(f"[INFO] Session Type: {os.environ.get('XDG_SESSION_TYPE', 'unknown')}")
    print("-" * 60)
    
    # Safety check
    print("[WARNING] Starting in 3 seconds... Switch to desktop if needed!")
    print("[WARNING] Press Ctrl+C to cancel.")
    for i in range(3, 0, -1):
        print(f"       {i}...")
        time.sleep(1)
    
    try:
        # Step 1: Launch VS Code
        launch_vscode_cli()
        
        # Step 2: Create file via CLI (works on Wayland)
        filepath = os.path.join(os.getcwd(), OUTPUT_FILENAME)
        if not create_file_via_cli(filepath, CODE_SNIPPET):
            print("[ERROR] Failed to create file. Exiting.")
            sys.exit(1)
        
        # Step 3: Open terminal (requires GUI)
        open_terminal_gui()
        
        # Step 4: Run code (requires GUI)
        run_code_gui()
        
        print("-" * 60)
        print("[SUCCESS] Automation completed!")
        print(f"[INFO] File created: {filepath}")
        if GUI_AVAILABLE:
            print(f"[INFO] Check terminal output for 'Hello, World!'")
        else:
            print(f"[INFO] Run manually: cd {os.getcwd()} && {RUN_COMMAND}")
        
    except KeyboardInterrupt:
        print("\n[INFO] Automation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()