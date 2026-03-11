---
name: write-file
description: Write or create files with given content. Use when the user asks to create, write, edit, or modify files.
---

# Write File

## Instructions

Write content to a file, creating parent directories as needed.

```bash
mkdir -p path/to/
cat > path/to/file.txt << 'EOF'
file content here
EOF
```

For editing existing files with Python:

```bash
python3 -c "
import os
path = 'path/to/file.txt'
with open(path, encoding='utf-8') as f:
    lines = f.readlines()
lines[5] = 'replacement line\n'
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('File updated')
"

## Guidelines

- Always create parent directories with `os.makedirs`
- Confirm the write by printing the path and bytes written
- When editing, read the file first to understand its structure
- Use UTF-8 encoding explicitly
