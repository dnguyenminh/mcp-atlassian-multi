# Business Requirements Document (BRD)

## MCP Atlassian Multi — MAM-3: Multi-user credential support via _meta field

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-3 |
| Title | Feat: Multi-user credential support via _meta field |
| Author | BA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Epic | MAM-1: Fork mcp-atlassian và tạo mcp-atlassian-multi với multi-user support |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-13 | BA Agent | Initiate document — documented from implemented code |

---

## 1. Introduction

### 1.1 Scope

Cho phép MCP server chạy ở chế độ **gateway multi-user**: một process server duy nhất phục vụ nhiều user đồng thời, mỗi user gửi credentials riêng qua trường `_meta` trong mỗi MCP tool call request, thay vì hardcode credentials trong environment variables.

### 1.2 Out of Scope

- OAuth 2.0 multi-tenant flow (đã có sẵn qua HTTP transport)
- User session management / token refresh
- Rate limiting per user
- User permission management (dựa vào Atlassian permissions)

### 1.3 Preliminary Requirement

- MCP server đã hoạt động với single-user mode (basic auth, PAT, OAuth)
- Package đã được rebrand thành `mcp-atlassian-multi` (MAM-2)

---

## 2. Business Requirements

### 2.1 High Level Process Map

1. Client gửi MCP tool call request kèm `_meta.credentials` chứa Jira/Confluence credentials
2. Server extract credentials từ `_meta` field
3. Server tạo hoặc lấy từ cache một fetcher instance cho user đó
4. Server thực thi tool call với fetcher của user
5. Response trả về cho client

### 2.2 List of User Stories

| # | Story / Use Case | Priority | Source Ticket |
|---|------------------|----------|---------------|
| 1 | As a platform admin, I want to run a single MCP server that serves multiple users so that I reduce infrastructure costs | MUST HAVE | MAM-3 |
| 2 | As an AI client developer, I want to pass user credentials per-request via _meta so that each user accesses their own Atlassian data | MUST HAVE | MAM-3 |
| 3 | As a platform admin, I want credentials to be cached with TTL so that repeated requests don't re-authenticate every time | SHOULD HAVE | MAM-3 |
| 4 | As a platform admin, I want the server to skip Cloud auth validation at startup when in multi-user mode so that the server can start without pre-configured credentials | MUST HAVE | MAM-3 |

---

### 2.3 Details of User Stories

---

#### STORY 1: Multi-user Gateway Mode

> As a platform admin, I want to run a single MCP server that serves multiple users so that I reduce infrastructure costs.

**Requirement Details:**

1. Server PHẢI hỗ trợ environment variable `MCP_MULTI_USER=true` để enable multi-user mode
2. Khi multi-user mode enabled, server KHÔNG yêu cầu `JIRA_USERNAME` / `JIRA_API_TOKEN` tại startup
3. Server vẫn yêu cầu `JIRA_URL` để xác định base URL cho tất cả users

**Acceptance Criteria:**

1. Server start thành công với `MCP_MULTI_USER=true` và `JIRA_URL` mà không cần credentials
2. Server log message: "Multi-user mode: skipping Cloud auth validation"
3. Server vẫn hoạt động bình thường ở single-user mode khi `MCP_MULTI_USER` không set

---

#### STORY 2: Per-request Credentials via _meta

> As an AI client developer, I want to pass user credentials per-request via _meta so that each user accesses their own Atlassian data.

**Requirement Details:**

1. Client gửi credentials trong `_meta.credentials` object của mỗi tool call
2. Hỗ trợ cả Jira và Confluence credentials
3. Hỗ trợ 2 auth types: Basic Auth (username + API token) và PAT (Personal Access Token)

**Data Fields:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `_meta.credentials.jira_url` | string | Yes (Jira) | Jira instance URL | `https://company.atlassian.net` |
| `_meta.credentials.jira_username` | string | Conditional | Email for basic auth | `user@company.com` |
| `_meta.credentials.jira_token` | string | Conditional | API token for basic auth | `ATATT3x...` |
| `_meta.credentials.jira_personal_token` | string | Conditional | PAT for Server/DC | `MDk2...` |
| `_meta.credentials.confluence_url` | string | Yes (Confluence) | Confluence instance URL | `https://company.atlassian.net/wiki` |
| `_meta.credentials.confluence_username` | string | Conditional | Email for basic auth | `user@company.com` |
| `_meta.credentials.confluence_token` | string | Conditional | API token for basic auth | `ATATT3x...` |
| `_meta.credentials.confluence_personal_token` | string | Conditional | PAT for Server/DC | `MDk2...` |

**Acceptance Criteria:**

1. Tool call với valid `_meta.credentials` trả về data từ Atlassian instance của user đó
2. Tool call không có `_meta.credentials` fallback về global config (single-user mode)
3. Tool call với invalid credentials trả về error message rõ ràng
4. Credentials KHÔNG được log ở bất kỳ level nào

---

#### STORY 3: Credential Caching

> As a platform admin, I want credentials to be cached with TTL so that repeated requests don't re-authenticate every time.

**Requirement Details:**

1. Fetcher instances được cache theo hash của credentials
2. Cache có TTL = 300 seconds (5 phút)
3. Cache có max size = 50 entries (per service: Jira/Confluence riêng)
4. Cache key = SHA-256 hash (truncated 16 chars) của sorted credential fields

**Acceptance Criteria:**

1. Request thứ 2 với cùng credentials sử dụng cached fetcher (không tạo mới)
2. Sau 5 phút, cached fetcher bị evict và request tiếp theo tạo fetcher mới
3. Khi cache đầy (50 entries), entry cũ nhất bị evict (LRU)

---

#### STORY 4: Skip Cloud Auth Validation in Multi-user Mode

> As a platform admin, I want the server to skip Cloud auth validation at startup when in multi-user mode.

**Requirement Details:**

1. Khi `MCP_MULTI_USER=true` và URL là Cloud (atlassian.net), bypass validation thiếu username/api_token
2. Sử dụng placeholder values: `username = "multi-user-placeholder"`, `api_token = "per-request-via-meta"`
3. Auth type vẫn set là "basic" để config object hợp lệ

**Acceptance Criteria:**

1. `JiraConfig.from_env()` không raise ValueError khi `MCP_MULTI_USER=true` dù thiếu credentials
2. Config object có `auth_type = "basic"` với placeholder values
3. Actual authentication xảy ra per-request qua `_meta` credentials

---

## 3. Dependencies

| Dependency | Type | Related Ticket | Description |
|------------|------|----------------|-------------|
| mcp-atlassian-multi package | System | MAM-2 | Package phải đã được rebrand |
| cachetools library | External | N/A | TTLCache cho credential caching |
| FastMCP framework | External | N/A | Context object cung cấp _meta access |

---

## 4. Stakeholders

| Role | Name / Team | Responsibility |
|------|-------------|----------------|
| Developer / Reporter | Duc Nguyen | Implementation, testing |
| Platform Users | AI Client Developers | Consume multi-user API |

---

## 5. Risks and Assumptions

### 5.1 Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Credential leak via logging | High | Low | Never log credential values, only hash prefixes |
| Cache memory pressure with many users | Medium | Low | TTL eviction + max size limit |
| Stale cached fetcher after password change | Medium | Medium | Short TTL (5 min) ensures refresh |

### 5.2 Assumptions

- Client (AI agent) có khả năng inject `_meta` field vào MCP tool calls
- Mỗi user có valid Atlassian credentials riêng
- Network connectivity từ server đến Atlassian instances ổn định

---

## 6. Non-Functional Requirements

| Category | Requirement | Details |
|----------|-------------|---------|
| Performance | Credential resolution < 50ms | Cache hit phải gần instant |
| Security | No credential logging | Chỉ log hash prefix (8 chars) |
| Scalability | Support 50 concurrent users | Cache maxsize = 50 |
| Reliability | Graceful fallback | Nếu _meta không có → dùng global config |

---

## 7. Related Tickets

| Ticket Key | Summary | Status | Type | Relationship |
|------------|---------|--------|------|--------------|
| MAM-1 | Epic: Fork mcp-atlassian và tạo mcp-atlassian-multi | Done | Epic | Parent epic |
| MAM-2 | Rebrand: Rename mcp-atlassian → mcp-atlassian-multi | Done | Task | Prerequisite |
| MAM-3 | Feat: Multi-user credential support via _meta field | Done | Task | Main ticket |
