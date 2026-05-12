---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

# Python Lint Rules — mcp-atlassian-multi

## Line Length

- **Maximum 88 characters per line** (enforced by Ruff)
- Before writing or editing any Python file, ensure ALL lines stay within 88 chars
- Break long lines using:
  - Multi-line function signatures with trailing comma
  - Multi-line strings or f-strings
  - Multi-line list/dict literals
  - Parenthesized expressions

## Common Violations to Avoid

```python
# BAD — line > 88 chars
loggers = ["mcp-atlassian-multi", "mcp.server", "mcp.server.lowlevel.server", "mcp-jira"]

# GOOD — multi-line list
loggers = [
    "mcp-atlassian-multi",
    "mcp.server",
    "mcp.server.lowlevel.server",
    "mcp-jira",
]

# BAD — long function signature
def resolve_confluence_from_meta(meta: dict[str, Any] | None) -> ConfluenceFetcher | None:

# GOOD — wrapped signature
def resolve_confluence_from_meta(
    meta: dict[str, Any] | None,
) -> ConfluenceFetcher | None:

# BAD — long decorator
@pytest.mark.skipif(sys.platform == "win32", reason="Windows doesn't support large timestamps")

# GOOD — multi-line decorator
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows doesn't support large timestamps",
)
```

## File Endings

- Every Python file MUST end with a newline character
- Ruff rule W292 enforces this

## Pre-commit Checks

Before committing Python files, mentally verify:
1. No line exceeds 88 characters
2. File ends with newline
3. Imports are sorted (isort via Ruff)
4. No unused imports
