# Functional Specification Document (FSD)

## MCP Atlassian Multi — MAM-3: Multi-user credential support via _meta field

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-3 |
| Title | Feat: Multi-user credential support via _meta field |
| Author | BA Agent + TA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Related BRD | BRD-v1-MAM-3.docx |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-13 | BA + TA Agent | Initiate document — reverse-engineered from implemented code |

---

## 1. Introduction

### 1.1 Purpose

Đặc tả chi tiết chức năng multi-user credential support cho MCP Atlassian Multi server, cho phép một server instance phục vụ nhiều users đồng thời thông qua per-request credentials trong `_meta` field.

### 1.2 Scope

- Module `multi_user.py`: credential extraction và fetcher resolution
- Module `dependencies.py`: integration với FastMCP dependency injection
- Module `jira/config.py`: bypass Cloud auth validation khi multi-user mode

### 1.3 Definitions & Acronyms

| Term | Definition |
|------|------------|
| MCP | Model Context Protocol — giao thức giao tiếp giữa AI models và tools |
| _meta | Metadata field trong MCP tool call request, chứa thông tin bổ sung |
| PAT | Personal Access Token — token xác thực cho Jira/Confluence Server/DC |
| TTL | Time To Live — thời gian sống của cache entry |
| Fetcher | Object thực hiện API calls đến Jira/Confluence |

### 1.4 References

| Document | Location |
|----------|----------|
| BRD | documents/MAM-3/BRD.md |
| MCP Specification | https://modelcontextprotocol.io/docs |

---

## 2. System Overview

### 2.1 System Context

```
┌─────────────┐     MCP Request + _meta.credentials     ┌──────────────────┐
│  AI Client  │ ──────────────────────────────────────── │  MCP Server      │
│  (Claude,   │                                          │  (mcp-atlassian- │
│   Cursor,   │ ◄────────────────────────────────────── │   multi)         │
│   etc.)     │     MCP Response                         └────────┬─────────┘
└─────────────┘                                                   │
                                                                  │ Per-user credentials
                                                                  ▼
                                                    ┌──────────────────────────┐
                                                    │  Atlassian Cloud/Server  │
                                                    │  (Jira + Confluence)     │
                                                    └──────────────────────────┘
```

### 2.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ MCP Server Process                                           │
│                                                              │
│  ┌──────────────┐    ┌─────────────────┐    ┌────────────┐ │
│  │ FastMCP      │───▶│ dependencies.py  │───▶│ Fetcher    │ │
│  │ Tool Handler │    │ (DI resolver)    │    │ (Jira/     │ │
│  └──────────────┘    └────────┬────────┘    │ Confluence)│ │
│                               │              └────────────┘ │
│                               ▼                              │
│                      ┌─────────────────┐                    │
│                      │ multi_user.py   │                    │
│                      │ (credential     │                    │
│                      │  resolver +     │                    │
│                      │  TTL cache)     │                    │
│                      └─────────────────┘                    │
│                                                              │
│  ┌──────────────┐                                           │
│  │ jira/config  │  ← MCP_MULTI_USER=true bypass            │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Functional Requirements

### 3.1 Feature: Credential Resolution from _meta

**Source:** BRD Story 2

#### 3.1.1 Use Case UC-01: Resolve Jira Credentials from _meta

| Field | Value |
|-------|-------|
| Use Case ID | UC-01 |
| Actor | AI Client |
| Precondition | Server running with `MCP_MULTI_USER=true` |
| Trigger | Client sends MCP tool call with `_meta.credentials` containing Jira fields |

**Main Flow:**

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 1 | Client | Sends tool call with `_meta.credentials.jira_url`, `jira_username`, `jira_token` | — |
| 2 | System | Extracts `_meta` from request context | — |
| 3 | System | Calls `resolve_jira_from_meta(meta)` | — |
| 4 | System | Computes SHA-256 hash of credentials | Cache key generated |
| 5 | System | Checks TTLCache for existing fetcher | — |
| 6 | System | Cache miss → creates `JiraConfig` with basic auth | Config created |
| 7 | System | Creates `JiraFetcher(config=config)` | Fetcher instantiated |
| 8 | System | Stores fetcher in cache | Cache updated |
| 9 | System | Returns fetcher to tool handler | Tool executes with user's fetcher |

**Alternative Flow — Cache Hit (Step 5):**

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 5a | System | Cache hit → returns cached fetcher | Log: "Using cached JiraFetcher for hash=XXXXXXXX" |
| 5b | System | Skip steps 6-8 | — |

**Alternative Flow — PAT Auth (Step 6):**

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 6a | System | Detects `jira_personal_token` in credentials | — |
| 6b | System | Creates `JiraConfig` with `auth_type="pat"` | Config with PAT |

**Exception Flow — Incomplete Credentials:**

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 3a | System | `_meta` is None or missing `credentials` key | Returns None → fallback to global config |
| 3b | System | `credentials` missing `jira_url` | Returns None → fallback to global config |
| 3c | System | Has `jira_url` but no username/token AND no PAT | Log warning: "Incomplete Jira credentials in _meta", returns None |

**Exception Flow — Fetcher Creation Failure:**

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 7a | System | `JiraFetcher()` raises exception (invalid URL, network error) | Log error: "Failed to create JiraFetcher from _meta: {error}" |
| 7b | System | Returns None | Fallback to global config |

---

#### 3.1.2 Use Case UC-02: Resolve Confluence Credentials from _meta

| Field | Value |
|-------|-------|
| Use Case ID | UC-02 |
| Actor | AI Client |
| Precondition | Server running with multi-user mode |
| Trigger | Client sends tool call with `_meta.credentials` containing Confluence fields |

**Main Flow:** Identical to UC-01 but with Confluence-specific fields:
- `confluence_url` instead of `jira_url`
- `confluence_username` / `confluence_email` instead of `jira_username`
- `confluence_token` / `confluence_api_token` instead of `jira_token`
- `confluence_personal_token` / `confluence_pat` instead of `jira_personal_token`

---

#### 3.1.3 Use Case UC-03: Server Startup in Multi-user Mode

| Field | Value |
|-------|-------|
| Use Case ID | UC-03 |
| Actor | Platform Admin |
| Precondition | `MCP_MULTI_USER=true` set in environment |
| Trigger | Server process starts |

**Main Flow:**

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 1 | Admin | Sets `MCP_MULTI_USER=true` and `JIRA_URL=https://company.atlassian.net` | — |
| 2 | System | `JiraConfig.from_env()` called | — |
| 3 | System | Detects Cloud URL (atlassian.net) | — |
| 4 | System | Checks for username/api_token → missing | — |
| 5 | System | Checks `MCP_MULTI_USER` env var → "true" | — |
| 6 | System | Logs: "Multi-user mode: skipping Cloud auth validation" | — |
| 7 | System | Sets `auth_type = "basic"`, `username = "multi-user-placeholder"`, `api_token = "per-request-via-meta"` | — |
| 8 | System | Returns valid JiraConfig | Server starts successfully |

**Exception Flow — Multi-user mode NOT enabled:**

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 5a | System | `MCP_MULTI_USER` not set or "false" | — |
| 5b | System | Raises `ValueError` with message about missing credentials | Server fails to start |

---

### 3.2 Business Rules

| ID | Rule | Implementation |
|----|------|----------------|
| BR-01 | Credentials NEVER logged at any level | Only log hash prefix (8 chars) |
| BR-02 | Cache TTL = 300 seconds | `TTLCache(maxsize=50, ttl=300)` |
| BR-03 | Cache max size = 50 per service | Separate caches for Jira and Confluence |
| BR-04 | Fallback to global config when _meta missing | `resolve_*_from_meta()` returns None → DI uses global |
| BR-05 | Field name aliases supported | `jira_username` OR `jira_email`, `jira_token` OR `jira_api_token` |
| BR-06 | PAT takes priority over basic auth | If `jira_personal_token` present, use PAT regardless of username/token |

---

### 3.3 Data Specifications

#### 3.3.1 _meta.credentials Schema (Jira)

```json
{
  "_meta": {
    "credentials": {
      "jira_url": "https://company.atlassian.net",
      "jira_username": "user@company.com",
      "jira_token": "ATATT3xFfGF0..."
    }
  }
}
```

#### 3.3.2 _meta.credentials Schema (PAT)

```json
{
  "_meta": {
    "credentials": {
      "jira_url": "https://jira.company.com",
      "jira_personal_token": "MDk2NTM..."
    }
  }
}
```

#### 3.3.3 Cache Key Generation

```
Input: {"jira_url": "https://x.atlassian.net", "jira_username": "a@b.com", "jira_token": "tok123"}
Process: Sort items → join with "|" → SHA-256 → truncate to 16 chars
Output: "a1b2c3d4e5f6g7h8"
```

---

### 3.4 API Contracts

#### 3.4.1 Internal API: resolve_jira_from_meta

```python
def resolve_jira_from_meta(meta: dict[str, Any] | None) -> JiraFetcher | None:
    """
    Input: _meta dict from MCP request context (or None)
    Output: JiraFetcher instance (or None if credentials not present/invalid)

    Side effects:
    - May create new JiraFetcher and cache it
    - Logs at DEBUG/INFO/WARNING/ERROR levels
    """
```

#### 3.4.2 Internal API: resolve_confluence_from_meta

```python
def resolve_confluence_from_meta(meta: dict[str, Any] | None) -> ConfluenceFetcher | None:
    """
    Input: _meta dict from MCP request context (or None)
    Output: ConfluenceFetcher instance (or None if credentials not present/invalid)
    """
```

#### 3.4.3 Internal API: _hash_credentials

```python
def _hash_credentials(creds: dict[str, str]) -> str:
    """
    Input: Dictionary of credential key-value pairs
    Output: 16-character hex string (SHA-256 prefix)

    Properties:
    - Deterministic: same input → same output
    - Order-independent: sorted before hashing
    """
```

---

### 3.5 Error Handling

| Error Scenario | System Behavior | Log Level |
|----------------|-----------------|-----------|
| `_meta` is None | Return None, use global fallback | DEBUG |
| `credentials` key missing | Return None, use global fallback | DEBUG |
| `jira_url` missing | Return None, use global fallback | DEBUG |
| Incomplete credentials (no auth method) | Return None, log warning | WARNING |
| Fetcher creation fails (network, invalid URL) | Return None, log error with exception | ERROR |
| Cache full | LRU eviction (automatic by cachetools) | N/A |

---

## 4. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | Cache lookup | < 1ms |
| Performance | New fetcher creation | < 100ms (excluding network validation) |
| Security | Credential exposure | Zero — never in logs, never in responses |
| Scalability | Concurrent users | 50 (cache maxsize) |
| Reliability | Fallback behavior | Always graceful — never crash on bad _meta |
| Maintainability | Code coverage | Unit tests for all branches |

---

## 5. Integration Requirements

### 5.1 FastMCP Context Integration

The multi-user module integrates with FastMCP's dependency injection system:

1. `dependencies.py` calls `_extract_meta_from_context(ctx)` to get `_meta`
2. If `_meta` has credentials → call `resolve_jira_from_meta()` / `resolve_confluence_from_meta()`
3. If resolver returns a fetcher → use it instead of global fetcher
4. If resolver returns None → fall through to existing auth logic (OAuth, PAT, basic)

### 5.2 Environment Variable

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `MCP_MULTI_USER` | `true`, `1`, `yes` / anything else | disabled | Enable multi-user mode |

---

## 6. Open Issues

| # | Issue | Status | Decision |
|---|-------|--------|----------|
| 1 | Should cache TTL be configurable via env var? | Deferred | Currently hardcoded at 300s |
| 2 | Should we validate credentials on cache store (not just on first use)? | Deferred | Currently no pre-validation |
| 3 | Should we support OAuth tokens in _meta? | Deferred | Currently only basic + PAT |
