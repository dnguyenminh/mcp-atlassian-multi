# mcp-atlassian-multi

Multi-user credential support for Atlassian MCP Server (Jira + Confluence).

Forked from [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian) with added support for per-request credential injection, enabling a single MCP server process to serve multiple users with different credentials.

## Key Difference from Original

| Feature | mcp-atlassian (original) | mcp-atlassian-multi (this fork) |
|---------|--------------------------|----------------------------------|
| Credential source | ENV vars / CLI args at startup | Per-request via `_meta` field |
| Process model | 1 process per user | 1 process for ALL users |
| Use case | Single-user (IDE, CLI) | Multi-user orchestrator server |

## How It Works

The original `mcp-atlassian` reads credentials from environment variables or CLI arguments when the process starts. This means each user needs a separate process.

`mcp-atlassian-multi` adds a **credential resolution layer** that:
1. Checks `_meta` in each tool call for per-request credentials
2. Falls back to ENV/CLI credentials if `_meta` is not provided (backward compatible)
3. Creates HTTP clients per credential set (pooled by credential hash)

## Installation

```bash
pip install mcp-atlassian-multi
uvx mcp-atlassian-multi
```

## Usage

### Mode 1: Original (backward compatible)

```bash
mcp-atlassian-multi --jira-url=https://company.atlassian.net --jira-token=YOUR_TOKEN
```

### Mode 2: Multi-user (orchestrator integration)

Start without credentials:
```bash
mcp-atlassian-multi --multi-user
```

Orchestrator sends credentials per tool call via `_meta`:
```json
{
  "method": "tools/call",
  "params": {
    "name": "jira_search",
    "arguments": {"jql": "project = PROJ"},
    "_meta": {
      "credentials": {
        "jira_url": "https://company.atlassian.net",
        "jira_username": "user@company.com",
        "jira_token": "USER_SPECIFIC_TOKEN"
      }
    }
  }
}
```

## Development

```bash
git clone https://github.com/dnguyenminh/mcp-atlassian-multi.git
cd mcp-atlassian-multi
uv sync
uv run pytest
uv run ruff check src/
uv run mcp-atlassian-multi --multi-user
```

## Syncing with Upstream

```bash
git fetch upstream
git checkout main
git merge upstream/main
git checkout feature/multi-user-credentials
git rebase main
```

## License

MIT License. Original work: Copyright (c) sooperset. Modified work: Copyright (c) dnguyenminh.
