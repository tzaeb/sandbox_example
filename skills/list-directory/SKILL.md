---
name: list-directory
description: List files and directories at a given path. Use when the user asks to see what files exist, explore a project structure, or navigate directories.
---

# List Directory

## Instructions

List directory contents using `ls`:

```bash
ls -la path/
```

For recursive/tree listing:

```bash
find path/ -maxdepth 3 -not -path '*/.*' | head -50
```

Or with `tree` if available:

```bash
tree -L 3 path/
```

## Guidelines

- Skip hidden files/dirs (starting with `.`) in tree views unless explicitly asked
- Show directories with a trailing `/` indicator
- For deep trees, default to max depth of 3 to avoid noise
