#!/usr/bin/env python3
"""
Self-Correcting Coding Bot
==========================
An autonomous coding agent that:
1. Takes a high-level programming goal from the user
2. Uses NVIDIA API (via OpenAI SDK) to generate code iteratively
3. Writes files to disk and opens them in VS Code for live viewing
4. Executes code, captures errors, and self-corrects
5. Continues until the goal is complete or max iterations reached

Requirements:
    pip install openai python-dotenv

Environment Variables (.env):
    NVIDIA_API_KEY=your_api_key
    NVIDIA_API_URL=https://integrate.api.nvidia.com/v1
    NVIDIA_DEFAULT_MODEL=nvidia/nemotron-3-ultra
"""

import os
import sys
import json
import time
import subprocess
import signal
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARN] python-dotenv not installed. Using system environment variables only.")

try:
    from openai import OpenAI
except ImportError:
    print("[ERROR] openai package not installed. Run: pip install openai")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_ITERATIONS = 20              # Hard limit to prevent infinite loops / credit burn
EXECUTION_TIMEOUT = 30           # Seconds before killing a running script
VSCODE_REUSE_WINDOW = True       # Use --reuse-window flag
WORKING_DIR = Path.cwd()         # Project directory

# Model configuration from environment
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_API_URL = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_DEFAULT_MODEL = os.getenv("NVIDIA_DEFAULT_MODEL", "nvidia/nemotron-3-ultra")

# =============================================================================
# SYSTEM PROMPT - Defines the agent's behavior and JSON response format
# =============================================================================

SYSTEM_PROMPT = """You are an Autonomous Self-Correcting Coding Agent.

Your job is to achieve a user's programming goal by writing complete, runnable files one step at a time.

### RULES:
1. **Always output valid JSON** with the exact structure specified below.
2. **Write complete, runnable files** - no snippets, no placeholders, no "..." ellipsis.
3. **One file per response** - focus on a single logical step.
4. **If given an error**, fix the code in the SAME file and return the corrected version.
5. **Never use external dependencies** not in Python standard library unless explicitly asked.
6. **Keep files focused** - one script/module per file.

### JSON RESPONSE FORMAT:
{
  "thought_process": "Your reasoning: what you're doing, why, and how it advances the goal.",
  "filename": "relative/path/to/file.py",
  "code_content": "Complete file content as a string (escape newlines as \\n in JSON)",
  "next_step": "Description of what should happen next (e.g., 'Run this file to test', 'Create test file', 'Fix the bug in X')",
  "status": "continue" | "complete" | "error"
}

### STATUS VALUES:
- "continue": Goal not yet achieved, more steps needed
- "complete": Goal fully achieved, all tests pass, nothing more to do
- "error": Something went wrong with your reasoning (rare)

### EXAMPLES:

**Step 1 - Create main script:**
{
  "thought_process": "Creating the main prime number calculator script with a function to check primality and a main block to test it.",
  "filename": "prime_calculator.py",
  "code_content": "def is_prime(n: int) -> bool:\\n    \"\"\"Check if a number is prime.\"\"\"\\n    if n < 2:\\n        return False\\n    for i in range(2, int(n**0.5) + 1):\\n        if n % i == 0:\\n            return False\\n    return True\\n\\ndef find_primes(limit: int) -> list:\\n    \"\"\"Find all primes up to limit.\"\"\"\\n    return [n for n in range(2, limit + 1) if is_prime(n)]\\n\\nif __name__ == \"__main__\":\\n    primes = find_primes(100)\\n    print(f\"Primes up to 100: {primes}\")\\n    print(f\"Count: {len(primes)}\")",
  "next_step": "Run this file to verify it works correctly",
  "status": "continue"
}

**Step 2 - Fix after error:**
{
  "thought_process": "The previous run had an IndentationError. Fixing the indentation in the is_prime function.",
  "filename": "prime_calculator.py",
  "code_content": "def is_prime(n: int) -> bool:\\n    \"\"\"Check if a number is prime.\"\"\"\\n    if n < 2:\\n        return False\\n    for i in range(2, int(n**0.5) + 1):\\n        if n % i == 0:\\n            return False\\n    return True\\n\\ndef find_primes(limit: int) -> list:\\n    \"\"\"Find all primes up to limit.\"\"\"\\n    return [n for n in range(2, limit + 1) if is_prime(n)]\\n\\nif __name__ == \"__main__\":\\n    primes = find_primes(100)\\n    print(f\"Primes up to 100: {primes}\")\\n    print(f\"Count: {len(primes)}\")",
  "next_step": "Run the fixed file to verify",
  "status": "continue"
}

**Step 3 - Create test file:**
{
  "thought_process": "Main script works. Now creating a comprehensive test file with edge cases.",
  "filename": "test_prime_calculator.py",
  "code_content": "import unittest\\nfrom prime_calculator import is_prime, find_primes\\n\\nclass TestPrimeCalculator(unittest.TestCase):\\n    def test_is_prime_edge_cases(self):\\n        self.assertFalse(is_prime(-1))\\n        self.assertFalse(is_prime(0))\\n        self.assertFalse(is_prime(1))\\n        self.assertTrue(is_prime(2))\\n        self.assertTrue(is_prime(3))\\n        self.assertFalse(is_prime(4))\\n        self.assertTrue(is_prime(17))\\n        self.assertFalse(is_prime(100))\\n    \\n    def test_find_primes(self):\\n        self.assertEqual(find_primes(10), [2, 3, 5, 7])\\n        self.assertEqual(find_primes(20), [2, 3, 5, 7, 11, 13, 17, 19])\\n        self.assertEqual(find_primes(1), [])\\n\\nif __name__ == \"__main__\":\\n    unittest.main()",
  "next_step": "Run the test file to verify all tests pass",
  "status": "continue"
}

**Step 4 - Complete:**
{
  "thought_process": "All tests pass. The prime calculator is complete with main functionality and comprehensive tests.",
  "filename": "",
  "code_content": "",
  "next_step": "Goal achieved: Prime number calculator with tests created and verified.",
  "status": "complete"
}
"""


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AgentResponse:
    """Structured response from the LLM."""
    thought_process: str
    filename: str
    code_content: str
    next_step: str
    status: str  # "continue" | "complete" | "error"

    @classmethod
    def from_json(cls, json_str: str) -> "AgentResponse":
        """Parse JSON response, handling potential formatting issues."""
        # Try to extract JSON from markdown code blocks if present
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        data = json.loads(json_str)
        return cls(
            thought_process=data.get("thought_process", ""),
            filename=data.get("filename", ""),
            code_content=data.get("code_content", ""),
            next_step=data.get("next_step", ""),
            status=data.get("status", "continue")
        )


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    execution_time: float


# =============================================================================
# CORE CLASSES
# =============================================================================

class CodingBot:
    """Main autonomous coding bot."""
    
    def __init__(self, api_key: str, api_url: str, model: str):
        if not api_key:
            raise ValueError("NVIDIA_API_KEY not set. Please set it in .env or environment.")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_url
        )
        self.model = model
        self.iteration = 0
        self.conversation_history: List[Dict[str, str]] = []
        self.project_files: Dict[str, str] = {}  # filename -> content
        self.execution_history: List[Dict[str, Any]] = []
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self._shutdown_requested = False
    
    def _signal_handler(self, signum, frame):
        print("\n\n[INTERRUPT] Shutdown requested. Finishing current iteration...")
        self._shutdown_requested = True
    
    def _build_user_prompt(self, goal: str, last_result: Optional[ExecutionResult] = None) -> str:
        """Build the user prompt with context."""
        prompt_parts = [f"## GOAL: {goal}\n"]
        
        if self.project_files:
            prompt_parts.append("## CURRENT PROJECT FILES:")
            for fname, content in self.project_files.items():
                prompt_parts.append(f"\n### {fname}\n```python\n{content}\n```")
        
        if self.execution_history:
            prompt_parts.append("\n## EXECUTION HISTORY (most recent first):")
            for i, entry in enumerate(reversed(self.execution_history[-5:])):  # Last 5
                prompt_parts.append(f"\n### Execution {len(self.execution_history) - i}")
                prompt_parts.append(f"File: {entry['filename']}")
                prompt_parts.append(f"Success: {entry['success']}")
                if entry['stdout']:
                    prompt_parts.append(f"STDOUT:\n{entry['stdout'][:2000]}")
                if entry['stderr']:
                    prompt_parts.append(f"STDERR:\n{entry['stderr'][:2000]}")
        
        if last_result:
            prompt_parts.append(f"\n## LAST EXECUTION RESULT:")
            prompt_parts.append(f"File: {last_result.filename if hasattr(last_result, 'filename') else 'N/A'}")
            prompt_parts.append(f"Success: {last_result.success}")
            if last_result.stdout:
                prompt_parts.append(f"STDOUT:\n{last_result.stdout}")
            if last_result.stderr:
                prompt_parts.append(f"STDERR:\n{last_result.stderr}")
            prompt_parts.append("\n**The above execution failed. Fix the code in the same file and return the corrected version.**")
        
        prompt_parts.append("\n## YOUR TASK:")
        prompt_parts.append("Generate the next step as JSON. Follow the SYSTEM_PROMPT format exactly.")
        
        return "\n".join(prompt_parts)
    
    def query_llm(self, goal: str, last_result: Optional[ExecutionResult] = None) -> AgentResponse:
        """Query the LLM for the next action."""
        user_prompt = self._build_user_prompt(goal, last_result)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        print(f"\n{'='*60}")
        print(f"[ITERATION {self.iteration + 1}/{MAX_ITERATIONS}] Querying LLM ({self.model})...")
        print(f"{'='*60}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,  # Low temperature for consistent code generation
                max_tokens=4096,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            content = response.choices[0].message.content
            print(f"[LLM] Response received ({len(content)} chars)")
            
            # Parse and validate
            agent_response = AgentResponse.from_json(content)
            
            # Log the thought process
            print(f"[THOUGHT] {agent_response.thought_process}")
            print(f"[FILE] {agent_response.filename or '(none)'}")
            print(f"[NEXT] {agent_response.next_step}")
            print(f"[STATUS] {agent_response.status}")
            
            return agent_response
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM JSON response: {e}")
            print(f"[RAW] {content[:500]}...")
            raise
        except Exception as e:
            print(f"[ERROR] LLM query failed: {e}")
            raise
    
    def write_file(self, filename: str, content: str) -> Path:
        """Write file to disk and open in VS Code."""
        filepath = WORKING_DIR / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Track project file
        self.project_files[filename] = content
        
        print(f"[WRITE] Created/Updated: {filepath}")
        
        # Open in VS Code
        try:
            cmd = ["code"]
            if VSCODE_REUSE_WINDOW:
                cmd.append("--reuse-window")
            cmd.append(str(filepath))
            subprocess.run(cmd, check=False, capture_output=True)
            print(f"[VSCODE] Opened in editor")
        except Exception as e:
            print(f"[VSCODE] Warning: Could not open in VS Code: {e}")
        
        return filepath
    
    def execute_file(self, filepath: Path) -> ExecutionResult:
        """Execute a Python file and capture output."""
        print(f"[EXECUTE] Running: python3 {filepath.name}")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["python3", str(filepath)],
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT,
                cwd=WORKING_DIR
            )
            execution_time = time.time() - start_time
            
            exec_result = ExecutionResult(
                success=(result.returncode == 0),
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                execution_time=execution_time
            )
            
            # Add filename for context
            exec_result.filename = filepath.name
            
            if exec_result.success:
                print(f"[SUCCESS] Exit code 0 ({execution_time:.2f}s)")
                if exec_result.stdout:
                    print(f"[STDOUT] {exec_result.stdout[:500]}")
            else:
                print(f"[ERROR] Exit code {result.returncode} ({execution_time:.2f}s)")
                if exec_result.stderr:
                    print(f"[STDERR] {exec_result.stderr[:500]}")
            
            return exec_result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print(f"[TIMEOUT] Execution exceeded {EXECUTION_TIMEOUT}s")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {EXECUTION_TIMEOUT} seconds",
                returncode=-1,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"[EXEC ERROR] {e}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=-1,
                execution_time=execution_time
            )
    
    def run(self, goal: str):
        """Main agent loop."""
        print(f"\n{'#'*60}")
        print(f"# SELF-CORRECTING CODING BOT STARTED")
        print(f"# Goal: {goal}")
        print(f"# Model: {self.model}")
        print(f"# Max Iterations: {MAX_ITERATIONS}")
        print(f"# Working Dir: {WORKING_DIR}")
        print(f"{'#'*60}")
        
        last_execution_result: Optional[ExecutionResult] = None
        
        while self.iteration < MAX_ITERATIONS:
            if self._shutdown_requested:
                print("\n[SHUTDOWN] Graceful exit requested.")
                break
            
            self.iteration += 1
            
            try:
                # 1. Query LLM for next action
                response = self.query_llm(goal, last_execution_result)
                
                # 2. Check termination condition
                if response.status == "complete":
                    print(f"\n{'='*60}")
                    print(f"[COMPLETE] Goal achieved!")
                    print(f"[SUMMARY] {response.next_step}")
                    print(f"{'='*60}")
                    break
                
                if response.status == "error":
                    print(f"\n[ERROR] LLM reported error status: {response.next_step}")
                    break
                
                # 3. Write file (if filename provided)
                if response.filename and response.code_content:
                    filepath = self.write_file(response.filename, response.code_content)
                    
                    # 4. Execute the file
                    last_execution_result = self.execute_file(filepath)
                    
                    # 5. Record execution history
                    self.execution_history.append({
                        "iteration": self.iteration,
                        "filename": response.filename,
                        "success": last_execution_result.success,
                        "stdout": last_execution_result.stdout,
                        "stderr": last_execution_result.stderr,
                        "returncode": last_execution_result.returncode,
                        "execution_time": last_execution_result.execution_time
                    })
                    
                    # 6. If error, loop will continue with error context
                    if not last_execution_result.success:
                        print(f"[LOOP] Error detected. Will send error context to LLM for fix.")
                        continue
                    
                    # Success - continue to next step
                    last_execution_result = None  # Clear error context for next iteration
                    
                elif response.filename and not response.code_content:
                    print(f"[WARN] Filename provided but no code content. Skipping.")
                
                # Small delay to avoid rate limiting
                time.sleep(1)
                
            except json.JSONDecodeError:
                print("[ERROR] Invalid JSON from LLM. Retrying...")
                continue
            except KeyboardInterrupt:
                print("\n[INTERRUPT] User cancelled.")
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                # Create an error result to feed back
                last_execution_result = ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"Bot internal error: {e}",
                    returncode=-1,
                    execution_time=0
                )
                continue
        
        if self.iteration >= MAX_ITERATIONS:
            print(f"\n[LIMIT] Maximum iterations ({MAX_ITERATIONS}) reached.")
        
        # Final summary
        self._print_summary()
    
    def _print_summary(self):
        """Print final summary of the session."""
        print(f"\n{'='*60}")
        print(f"SESSION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Iterations: {self.iteration}")
        print(f"Files Created/Modified: {len(self.project_files)}")
        for fname in self.project_files:
            print(f"  - {fname}")
        print(f"Executions: {len(self.execution_history)}")
        successes = sum(1 for e in self.execution_history if e['success'])
        print(f"  Successful: {successes}")
        print(f"  Failed: {len(self.execution_history) - successes}")
        print(f"{'='*60}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    # Validate environment
    if not NVIDIA_API_KEY:
        print("[ERROR] NVIDIA_API_KEY not found in environment.")
        print("Please create a .env file with:")
        print("  NVIDIA_API_KEY=your_key_here")
        print("  NVIDIA_API_URL=https://integrate.api.nvidia.com/v1")
        print("  NVIDIA_DEFAULT_MODEL=nvidia/nemotron-3-ultra")
        sys.exit(1)
    
    print(f"[CONFIG] API URL: {NVIDIA_API_URL}")
    print(f"[CONFIG] Model: {NVIDIA_DEFAULT_MODEL}")
    print(f"[CONFIG] Working Dir: {WORKING_DIR}")
    
    # Get user goal
    print("\n" + "="*60)
    print("SELF-CORRECTING CODING BOT")
    print("="*60)
    print("Enter your programming goal (e.g., 'Create a Python script that")
    print("calculates prime numbers up to N and includes unit tests')")
    print("Press Ctrl+C at any time to stop gracefully.\n")
    
    try:
        goal = input("Goal: ").strip()
    except KeyboardInterrupt:
        print("\n[EXIT] Cancelled by user.")
        sys.exit(0)
    
    if not goal:
        print("[ERROR] No goal provided.")
        sys.exit(1)
    
    # Initialize and run bot
    bot = CodingBot(NVIDIA_API_KEY, NVIDIA_API_URL, NVIDIA_DEFAULT_MODEL)
    bot.run(goal)


if __name__ == "__main__":
    main()