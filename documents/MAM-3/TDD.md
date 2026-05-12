# Technical Design Document (TDD)

## MCP Atlassian Multi — MAM-3: Multi-user credential support via _meta field

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-3 |
| Title | Feat: Multi-user credential support via _meta field |
| Author | SA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Related BRD | BRD-v1-MAM-3.docx |
| Related FSD | FSD-v1-MAM-3.docx |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-13 | SA Agent | Initiate document — reverse-engineered from implemented code |

---

## 1. Introduction

### 1.1 Purpose

Technical design cho multi-user credential support, mô tả cách implement credential resolution, caching, và integration với existing dependency injection system.

### 1.2 Scope

- New module: `src/mcp_atlassian/servers/multi_user.py`
- Modified module: `src/mcp_atlassian/servers/dependencies.py`
- Modified module: `src/mcp_atlassian/jira/config.py`

### 1.3 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | ≥ 3.10 |
| Framework | FastMCP | 2.13.x |
| Caching | cachetools (TTLCache) | ≥ 5.0.0 |
| Hashing | hashlib (stdlib) | — |
| HTTP Client | atlassian-python-api | ≥ 4.0.0 |
| Type Checking | mypy (strict) | ≥ 1.8.0 |

### 1.4 Design Principles

- **Single Responsibility**: `multi_user.py` chỉ lo credential resolution + caching
- **Open/Closed**: Existing auth flows không bị modify, chỉ thêm branch mới
- **Graceful Degradation**: Mọi failure đều fallback về global config, không crash
- **Security by Default**: Credentials never logged, only hash prefixes

### 1.5 Constraints

- Python ≥ 3.10 (type union syntax `X | Y`)
- Must work with both stdio and HTTP transports
- Cache must be thread-safe (cachetools TTLCache is thread-safe for single operations)
- No external service dependencies for caching (in-memory only)

---

## 2. Architecture

### 2.1 Module Structure

```
src/mcp_atlassian/servers/
├── multi_user.py          ← NEW: credential resolver + cache
├── dependencies.py        ← MODIFIED: integrate multi_user resolver
├── main.py                ← UNCHANGED: server entry point
├── context.py             ← UNCHANGED: app context
└── client_storage.py      ← UNCHANGED: client storage

src/mcp_atlassian/jira/
└── config.py              ← MODIFIED: MCP_MULTI_USER bypass
```

### 2.2 Data Flow

```
Tool Call Request
       │
       ▼
┌─────────────────────┐
│ FastMCP Tool Handler │
│ (auto-injects ctx)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ get_jira_fetcher(ctx)       │  ← dependencies.py
│                             │
│ 1. Try HTTP request context │
│ 2. Check request.state cache│
│ 3. Check _meta credentials  │  ← NEW BRANCH
│ 4. Try header-based PAT     │
│ 5. Try basic auth           │
│ 6. Try OAuth/PAT            │
│ 7. Fallback to global       │
└──────────┬──────────────────┘
           │ (branch 3)
           ▼
┌─────────────────────────────┐
│ resolve_jira_from_meta(meta)│  ← multi_user.py
│                             │
│ 1. Validate meta structure  │
│ 2. Extract credentials      │
│ 3. Compute cache key (hash) │
│ 4. Check TTLCache           │
│ 5. Create JiraConfig        │
│ 6. Create JiraFetcher       │
│ 7. Store in cache           │
│ 8. Return fetcher           │
└─────────────────────────────┘
```

---

## 3. Detailed Design

### 3.1 Module: multi_user.py

#### 3.1.1 Module-level State

```python
# Global caches — one per service, module-level singletons
_jira_cache: TTLCache[str, JiraFetcher] = TTLCache(maxsize=50, ttl=300)
_confluence_cache: TTLCache[str, ConfluenceFetcher] = TTLCache(maxsize=50, ttl=300)
```

**Design Decision**: Module-level caches (not class-based) because:
- Simple — no need for singleton pattern
- Shared across all requests in the same process
- TTLCache handles eviction automatically

#### 3.1.2 Function: _hash_credentials

```python
def _hash_credentials(creds: dict[str, str]) -> str:
    """Create deterministic hash of credentials for cache key.

    Algorithm:
    1. Sort dict items by key (deterministic ordering)
    2. Join as "key=value" separated by "|"
    3. SHA-256 hash the UTF-8 encoded string
    4. Return first 16 hex characters

    Why SHA-256 truncated to 16 chars:
    - Collision probability negligible for < 50 entries
    - Short enough for readable logs
    - Deterministic regardless of dict insertion order
    """
```

#### 3.1.3 Function: resolve_jira_from_meta

```python
def resolve_jira_from_meta(meta: dict[str, Any] | None) -> JiraFetcher | None:
    """Resolve JiraFetcher from _meta credentials if present.

    Decision tree:
    1. meta is None → return None
    2. meta has no "credentials" key → return None
    3. credentials has no "jira_url" → return None
    4. Compute hash → check cache → return if hit
    5. Determine auth type:
       a. jira_personal_token OR jira_pat → PAT auth
       b. (jira_username OR jira_email) AND (jira_token OR jira_api_token) → basic auth
       c. Neither → log warning, return None
    6. Create JiraConfig → Create JiraFetcher → cache → return
    7. On any exception → log error, return None
    """
```

#### 3.1.4 Field Name Aliases

| Canonical Field | Aliases |
|----------------|---------|
| `jira_username` | `jira_email` |
| `jira_token` | `jira_api_token` |
| `jira_personal_token` | `jira_pat` |
| `confluence_username` | `confluence_email` |
| `confluence_token` | `confluence_api_token` |
| `confluence_personal_token` | `confluence_pat` |

**Rationale**: Different AI clients may use different naming conventions. Supporting aliases reduces integration friction.

---

### 3.2 Module: dependencies.py (Modifications)

#### 3.2.1 New Import

```python
from mcp_atlassian.servers.multi_user import resolve_jira_from_meta, resolve_confluence_from_meta
```

#### 3.2.2 New Function: _extract_meta_from_context

```python
def _extract_meta_from_context(ctx: Context) -> dict[str, Any] | None:
    """Extract _meta from the current tool call context.

    Tries multiple access patterns because FastMCP's internal structure
    may vary between versions:
    1. ctx.request_context.meta (preferred)
    2. ctx._meta (fallback)
    3. ctx.request_context.params._meta (legacy)
    4. ctx.request_context.params["_meta"] (dict-style)

    Returns None on any failure (never raises).
    """
```

#### 3.2.3 Integration Point in _get_fetcher

The `_get_fetcher` function in `dependencies.py` already handles multiple auth branches. The multi-user resolution is integrated as an additional early-exit path:

```python
async def _get_fetcher(ctx: Context, spec: _ServiceSpec) -> Any:
    # ... existing code ...

    # NEW: Check _meta for multi-user credentials
    meta = _extract_meta_from_context(ctx)
    if meta:
        if spec.name == "Jira":
            fetcher = resolve_jira_from_meta(meta)
        else:
            fetcher = resolve_confluence_from_meta(meta)
        if fetcher:
            return fetcher

    # ... existing auth branches continue ...
```

---

### 3.3 Module: jira/config.py (Modifications)

#### 3.3.1 Change Location

In `JiraConfig.from_env()`, within the Cloud auth validation block:

```python
# Before (raises ValueError):
if not username or not api_token:
    raise ValueError("Cloud authentication requires...")

# After (with multi-user bypass):
if not username or not api_token:
    if os.getenv("MCP_MULTI_USER", "").lower() in ("true", "1", "yes"):
        logger.info("Multi-user mode: skipping Cloud auth validation")
        auth_type = "basic"
        username = username or "multi-user-placeholder"
        api_token = api_token or "per-request-via-meta"
    else:
        raise ValueError("Cloud authentication requires...")
```

**Design Decision**: Placeholder values instead of None because:
- `JiraConfig` dataclass expects non-None for basic auth
- Downstream code may check `config.username` truthiness
- Placeholder values are clearly identifiable in debug logs
- Actual auth happens per-request via `_meta`

---

## 4. Security Design

### 4.1 Credential Handling

| Aspect | Implementation |
|--------|---------------|
| Storage | In-memory only (TTLCache), never persisted |
| Logging | Only hash prefix logged: `hash=a1b2c3d4` |
| Transport | Credentials travel in MCP request body (encrypted by transport layer) |
| Eviction | Automatic after 300s TTL or LRU when cache full |
| Isolation | Each user gets own fetcher instance with own session |

### 4.2 Attack Vectors Considered

| Vector | Mitigation |
|--------|-----------|
| Credential stuffing via _meta | Rate limiting at transport layer (not in scope) |
| Cache poisoning | Hash-based keys prevent collision; TTL limits exposure |
| Memory dump | Credentials in Python objects; no special protection (OS-level concern) |
| SSRF via jira_url | URL validation in fetcher creation (existing SSRF hooks) |

---

## 5. Testing Strategy

### 5.1 Unit Tests

| Test Case | Description |
|-----------|-------------|
| `test_hash_credentials_deterministic` | Same input → same hash |
| `test_hash_credentials_order_independent` | Different key order → same hash |
| `test_resolve_jira_none_meta` | None input → None output |
| `test_resolve_jira_no_credentials` | Meta without credentials key → None |
| `test_resolve_jira_no_url` | Credentials without jira_url → None |
| `test_resolve_jira_basic_auth` | Valid username + token → JiraFetcher |
| `test_resolve_jira_pat_auth` | Valid PAT → JiraFetcher with pat config |
| `test_resolve_jira_cache_hit` | Second call with same creds → cached fetcher |
| `test_resolve_jira_incomplete` | URL but no auth → None + warning log |
| `test_resolve_jira_creation_failure` | Invalid URL → None + error log |
| `test_multi_user_config_bypass` | MCP_MULTI_USER=true → no ValueError |

### 5.2 Integration Tests

| Test Case | Description |
|-----------|-------------|
| `test_tool_call_with_meta_credentials` | Full flow: tool call → _meta extraction → fetcher resolution |
| `test_fallback_to_global_when_no_meta` | Tool call without _meta → uses global config |

---

## 6. Implementation Checklist

| # | File | Change Type | Description |
|---|------|-------------|-------------|
| 1 | `src/mcp_atlassian/servers/multi_user.py` | NEW | Credential resolver + TTL cache |
| 2 | `src/mcp_atlassian/servers/dependencies.py` | MODIFY | Import multi_user, add _extract_meta_from_context, integrate in _get_fetcher |
| 3 | `src/mcp_atlassian/jira/config.py` | MODIFY | Add MCP_MULTI_USER bypass in from_env() |
| 4 | `pyproject.toml` | MODIFY | Add `cachetools` dependency |
| 5 | `tests/unit/servers/test_multi_user.py` | NEW | Unit tests for multi_user module |

---

## 7. Deployment Considerations

### 7.1 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MCP_MULTI_USER` | No | disabled | Set to `true` to enable multi-user mode |
| `JIRA_URL` | Yes | — | Base URL (still required for global config) |

### 7.2 Backward Compatibility

- **100% backward compatible**: If `MCP_MULTI_USER` is not set, behavior is identical to before
- No breaking changes to existing single-user deployments
- No changes to MCP tool signatures or responses

### 7.3 Performance Impact

| Metric | Impact |
|--------|--------|
| Memory | +~2MB per cached fetcher × 50 max = ~100MB worst case |
| Latency (cache hit) | +< 1ms (hash computation + dict lookup) |
| Latency (cache miss) | +50-200ms (fetcher creation + initial connection) |
| Startup time | No impact (bypass skips validation) |
