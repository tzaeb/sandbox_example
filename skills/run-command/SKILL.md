---
name: run-command
description: Run commands (git, build tools, tests, package managers, etc). Use when the user asks to run, execute, build, test, or install something.
---

# Run Command

## Instructions

Execute commands directly:

```bash
git status
```

For commands with pipes or redirection:

```bash
ls -la | head -20
```

For long-running commands, add a timeout:

```bash
timeout 30 make build
```

For long-running commands, use a longer timeout or stream output. Read the streaming guide:

```bash
cat /skills/run-command/STREAMING.md
```

## Guidelines

- Always set a `timeout` to prevent hanging
- Prefer list form (`["cmd", "arg"]`) over `shell=True` when possible
- Always check `returncode` and show stderr on failure
- Print the output so the user can see the results
