# Streaming Command Output

For long-running commands where you want to see output as it comes:

```python
import subprocess

process = subprocess.Popen(
    ["python", "-m", "pytest", "-v"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True
)

output_lines = []
for line in process.stdout:
    print(line, end="")
    output_lines.append(line)

process.wait()
print(f"\nExit code: {process.returncode}")
```

## Running background tasks

```python
import subprocess, threading

def run_in_background(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Background task finished: {cmd}")
    print(result.stdout)

thread = threading.Thread(target=run_in_background, args=("npm run build",))
thread.start()
```
