# Common Search Patterns

## Finding definitions

```python
# Python function definitions
pattern = re.compile(r"^\s*def\s+(\w+)")

# Python class definitions
pattern = re.compile(r"^\s*class\s+(\w+)")

# JavaScript/TypeScript function definitions
pattern = re.compile(r"(?:function|const|let|var)\s+(\w+)\s*(?:=\s*)?(?:\(|=>)")
```

## Finding imports

```python
# Python imports
pattern = re.compile(r"^(?:from\s+\S+\s+)?import\s+")

# JavaScript/TypeScript imports
pattern = re.compile(r"^import\s+")
```

## Finding TODOs and FIXMEs

```python
pattern = re.compile(r"(?:TODO|FIXME|HACK|XXX|WARN)", re.IGNORECASE)
```
