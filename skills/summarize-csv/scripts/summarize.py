"""Summarize a CSV file: shape, dtypes, basic stats, and preview."""
import sys
import pandas as pd


def summarize(path: str) -> None:
    df = pd.read_csv(path)

    print(f"Rows: {len(df)}  Columns: {len(df.columns)}\n")

    print("Columns:")
    for col in df.columns:
        print(f"  {col} ({df[col].dtype})")

    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        print("\nNumeric stats:")
        for col in numeric.columns:
            s = numeric[col]
            print(f"  {col}: mean={s.mean():.2f}  min={s.min()}  max={s.max()}")

    print(f"\nPreview (first 5 rows):\n{df.head().to_string(index=False)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: summarize.py <csv-file>")
        sys.exit(1)
    summarize(sys.argv[1])
