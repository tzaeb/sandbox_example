---
name: summarize-csv
description: Summarize CSV files with statistics and previews. Use when the user asks to analyze, summarize, or inspect a CSV file.
---

# Summarize CSV

## Instructions

Use the provided script to get a quick summary of any CSV file.

Run the script directly:

```bash
python3 /skills/summarize-csv/scripts/summarize.py path/to/file.csv
```

The script outputs:
- Row and column counts
- Column names and dtypes
- Numeric column statistics (mean, min, max)
- First 5 rows as a preview

For custom analysis beyond the summary, run python3 directly with your own code.
