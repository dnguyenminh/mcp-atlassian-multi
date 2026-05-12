# Business Requirements Document (BRD)

## MCP Atlassian Multi — MAM-2: Rebrand mcp-atlassian → mcp-atlassian-multi

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-2 |
| Title | Rebrand: Rename mcp-atlassian → mcp-atlassian-multi toàn bộ codebase |
| Author | BA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Epic | MAM-1 |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-13 | BA Agent | Initiate document — documented from implemented changes |

---

## 1. Introduction

### 1.1 Scope

Rename toàn bộ codebase từ `mcp-atlassian` sang `mcp-atlassian-multi` để publish package riêng lên PyPI, tránh conflict với package gốc. Bao gồm package name, CLI entry point, documentation, Docker configs, và Helm charts.

### 1.2 Out of Scope

- Thay đổi internal module name (`mcp_atlassian` Python package name giữ nguyên)
- Thay đổi logic code
- Thay đổi API/tool signatures

### 1.3 Preliminary Requirement

- Fork từ `mcp-atlassian` repository đã hoàn thành
- Quyết định tên package mới: `mcp-atlassian-multi`

---

## 2. Business Requirements

### 2.1 List of User Stories

| # | Story | Priority | Source |
|---|-------|----------|--------|
| 1 | As a maintainer, I want a unique package name on PyPI so that users can install our fork without conflicting with the original | MUST HAVE | MAM-2 |
| 2 | As a user, I want a distinct CLI command so that both packages can coexist on the same system | MUST HAVE | MAM-2 |
| 3 | As a contributor, I want all documentation to reflect the new name so that there's no confusion about which project this is | SHOULD HAVE | MAM-2 |

---

### 2.3 Details of User Stories

#### STORY 1: Unique PyPI Package Name

> As a maintainer, I want a unique package name on PyPI.

**Requirement Details:**

1. `pyproject.toml` → `name = "mcp-atlassian-multi"`
2. Package installable via: `pip install mcp-atlassian-multi`
3. Internal Python module name unchanged: `mcp_atlassian` (backward compatible imports)

**Acceptance Criteria:**

1. `pip install mcp-atlassian-multi` installs the package
2. `import mcp_atlassian` works after installation
3. No conflict with `pip install mcp-atlassian` (original package)

---

#### STORY 2: Distinct CLI Entry Point

> As a user, I want a distinct CLI command.

**Requirement Details:**

1. CLI command: `mcp-atlassian-multi` (thay vì `mcp-atlassian`)
2. Entry point in pyproject.toml: `mcp-atlassian-multi = "mcp_atlassian:main"`

**Acceptance Criteria:**

1. `mcp-atlassian-multi --help` shows help text
2. `mcp-atlassian-multi` starts the MCP server

---

#### STORY 3: Documentation Update

> As a contributor, I want all documentation to reflect the new name.

**Files affected (~30 files):**

| Category | Files |
|----------|-------|
| Package config | `pyproject.toml` |
| Documentation | `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `AGENTS.md` |
| Docker | `Dockerfile`, `.dockerignore`, `smithery.yaml` |
| Helm | `helm/` chart files |
| CI/CD | `.github/workflows/*.yml` |
| Dev config | `.devcontainer/`, `.env.example` |

**Acceptance Criteria:**

1. No references to `mcp-atlassian` (without `-multi`) in user-facing docs
2. Docker image references updated
3. Helm chart name updated

---

## 3. Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| PyPI namespace | External | `mcp-atlassian-multi` must be available on PyPI |
| GitHub repository | Infrastructure | Repository already named `mcp-atlassian-multi` |

---

## 4. Risks and Assumptions

### 4.1 Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Missed rename in some file | Low | Medium | Grep for old name after rename |
| Import breakage | High | Low | Internal module name unchanged |

### 4.2 Assumptions

- Internal Python module name `mcp_atlassian` stays the same (PEP convention: underscores)
- Users will install via `pip install mcp-atlassian-multi`

---

## 5. Non-Functional Requirements

| Category | Requirement | Details |
|----------|-------------|---------|
| Compatibility | Python imports unchanged | `from mcp_atlassian import ...` still works |
| Discoverability | PyPI search finds package | Package description mentions "multi-user" |
