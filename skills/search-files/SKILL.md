---
name: search-files
description: Search for text patterns across files using regex. Use when the user asks to find, grep, or search for code, text, or patterns in files.
---

# Search Files

## Instructions

Search for a pattern across files using `grep`:

```bash
grep -rn "pattern" path/
```

Case-insensitive search:

```bash
grep -rni "pattern" path/
```

Filter by file extension:

```bash
grep -rn --include="*.py" "pattern" path/
```

Exclude common non-source directories:

```bash
grep -rn --exclude-dir={.git,node_modules,__pycache__} "pattern" path/
```

## Guidelines

- Skip `.git`, `node_modules`, `__pycache__`, and other non-source directories
- Use `errors="ignore"` to handle binary files
- Show results as `filepath:line_number: matching_line`
- Use `re.IGNORECASE` for case-insensitive search when appropriate

For advanced search patterns, read the patterns guide:

```bash
cat /skills/search-files/PATTERNS.md
```
