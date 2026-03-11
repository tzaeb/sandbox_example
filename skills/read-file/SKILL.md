---
name: read-file
description: Read the contents of a file at a given path. Use when the user asks to view, inspect, or read a file.
---

# Read File

## Instructions

Read file contents using `cat` or Python:

```bash
cat path/to/file.txt
```

For large files, read only what's needed:

```bash
head -100 path/to/file.txt
```

Or with line numbers:

```bash
cat -n path/to/file.txt | head -100
```

## Guidelines

- Always print the content so the user can see it
- Use `errors="replace"` to handle binary/non-UTF8 files gracefully
- For very large files, show the first ~100 lines and note the truncation
- Show line numbers when displaying code files
