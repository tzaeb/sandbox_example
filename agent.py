"""
Agentic loop using llama.cpp server's /v1/chat/completions endpoint.

Implements progressive skill disclosure (Anthropic pattern):
- Level 1: Skill metadata is always in the system prompt
- Level 2: LLM reads SKILL.md via bash (cat /skills/<name>/SKILL.md)
- Level 3: LLM reads resources / runs scripts via bash

Single tool: bash — the LLM navigates the filesystem itself.
"""

import json

import requests


# ANSI color codes for terminal output
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    RED = "\033[31m"

from skills import discover_all_skills, build_metadata_prompt
from tool_python import Sandbox

TOOL_BASH = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": (
            "Run a bash command in your sandboxed workspace environment. "
            "Working directory is /workspace. Skills are at /skills/. "
            "Python 3.11 with numpy, pandas and matplotlib is available. "
            "Network access is disabled."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Bash command to execute",
                }
            },
            "required": ["command"],
        },
    },
}

SYSTEM_PROMPT = """\
You are a helpful coding agent. You have a single tool: `bash`, which runs
commands inside a sandboxed container.

## How to work

1. When a task matches a skill below, read its instructions first:
   bash: cat /skills/<skill-name>/SKILL.md
2. Follow the instructions. If they reference additional files (e.g. PATTERNS.md,
   STREAMING.md), read those too:
   bash: cat /skills/<skill-name>/PATTERNS.md
3. Run scripts and commands directly:
   bash: python3 /skills/summarize-csv/scripts/summarize.py data.csv
4. Working directory is /workspace. Skills are at /skills/.
5. Python 3.11 with numpy, pandas and matplotlib is available. Network access is disabled.

## {skills_metadata}
"""


class Agent:
    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url.rstrip("/")
        self.sandbox = Sandbox()
        self.tools = [TOOL_BASH]
        self.messages = []

        self._step_count = 0

        # Level 1: discover skills and put metadata in system prompt
        self.skills = discover_all_skills()
        metadata_prompt = build_metadata_prompt(self.skills)
        self.system_message = {
            "role": "system",
            "content": SYSTEM_PROMPT.format(skills_metadata=metadata_prompt),
        }

    def chat_completion(self, messages: list[dict]) -> dict:
        payload = {
            "messages": [self.system_message] + messages,
            "tools": self.tools,
            "tool_choice": "auto",
        }

        resp = requests.post(
            f"{self.server_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    def _print_tool_header(self, icon: str, label: str, detail: str):
        print(f"\n{Color.DIM}{'─' * 60}{Color.RESET}")
        print(f"{Color.BOLD}{icon} {label}{Color.RESET} {Color.DIM}{detail}{Color.RESET}")

    def _print_tool_output(self, output: str, max_lines: int = 15):
        lines = output.splitlines()
        preview = lines[:max_lines]
        for line in preview:
            print(f"  {Color.DIM}│{Color.RESET} {line}")
        if len(lines) > max_lines:
            print(f"  {Color.DIM}│ ... ({len(lines) - max_lines} more lines){Color.RESET}")
        print(f"{Color.DIM}{'─' * 60}{Color.RESET}")

    def handle_tool_call(self, tc: dict) -> str:
        func_name = tc["function"]["name"]
        raw_args = tc["function"]["arguments"]
        args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args)

        if func_name == "bash":
            command = args["command"]
            self._print_tool_header("▶", "bash", "")
            print(f"  {Color.CYAN}│{Color.RESET} {Color.DIM}{command}{Color.RESET}")
            confirm = input(f"  {Color.YELLOW}Execute? [y/N]{Color.RESET} ").strip().lower()
            if confirm != "y":
                return "(execution skipped by user)"
            output = self.sandbox.execute(command)
            print(f"  {Color.GREEN}┤ output:{Color.RESET}")
            self._print_tool_output(output)
            return output

        return f"Unknown tool: {func_name}"

    def handle_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        results = []
        for tc in tool_calls:
            output = self.handle_tool_call(tc)
            results.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": output,
            })
        return results

    def step(self, user_message: str | None = None) -> str | None:
        """Run one step. Returns assistant text if done, None if more tool calls needed."""
        if user_message:
            self.messages.append({"role": "user", "content": user_message})

        self._step_count += 1
        print(f"{Color.DIM}  ⏳ thinking (step {self._step_count})...{Color.RESET}", flush=True)

        response = self.chat_completion(self.messages)
        choice = response["choices"][0]
        assistant_msg = choice["message"]
        self.messages.append(assistant_msg)

        # Print any inline text the LLM included alongside tool calls
        if assistant_msg.get("content") and assistant_msg.get("tool_calls"):
            print(f"\n{Color.MAGENTA}  💭 {assistant_msg['content']}{Color.RESET}")

        if assistant_msg.get("tool_calls"):
            tool_results = self.handle_tool_calls(assistant_msg["tool_calls"])
            self.messages.extend(tool_results)
            return None

        return assistant_msg.get("content", "")

    def run(self, user_message: str, max_steps: int = 20) -> str:
        """Run the full agent loop until the LLM responds with text (no tool calls)."""
        self._step_count = 0
        result = self.step(user_message)

        steps = 0
        while result is None and steps < max_steps:
            result = self.step()
            steps += 1

        if result is None:
            return "(Agent reached maximum steps without a final response)"

        return result
