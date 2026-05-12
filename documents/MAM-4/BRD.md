# Business Requirements Document (BRD)

## MCP Atlassian Multi — MAM-4: CI/CD Build & Publish to PyPI workflow

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-4 |
| Title | CI/CD: Build & Publish to PyPI workflow |
| Author | BA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Epic | MAM-1 |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-13 | BA Agent | Initiate document — documented from implemented workflow |

---

## 1. Introduction

### 1.1 Scope

Thiết lập GitHub Actions workflow hoàn chỉnh để build, test, và publish package `mcp-atlassian-multi` lên PyPI và TestPyPI. Workflow bao gồm multi-platform testing (3 OS × 4 Python versions) và automatic release asset upload.

### 1.2 Out of Scope

- Docker image publishing (đã có workflow riêng: `docker-publish.yml`)
- Linting/testing CI (đã có: `lint.yml`, `tests.yml`)
- Version management strategy (dùng `uv-dynamic-versioning` từ git tags)

### 1.3 Preliminary Requirement

- Package đã được rebrand thành `mcp-atlassian-multi` (MAM-2)
- PyPI account và TestPyPI account đã được tạo
- GitHub repository secrets đã được configure

---

## 2. Business Requirements

### 2.1 List of User Stories

| # | Story | Priority | Source |
|---|-------|----------|--------|
| 1 | As a maintainer, I want to automatically publish to PyPI when creating a GitHub Release so that users can install the latest version | MUST HAVE | MAM-4 |
| 2 | As a maintainer, I want to test the build on multiple OS and Python versions before publishing so that I ensure compatibility | MUST HAVE | MAM-4 |
| 3 | As a maintainer, I want to manually trigger a publish to TestPyPI so that I can verify the package before a real release | SHOULD HAVE | MAM-4 |
| 4 | As a user, I want release assets (wheel + sdist) attached to GitHub Releases so that I can download directly | SHOULD HAVE | MAM-4 |

---

### 2.3 Details of User Stories

#### STORY 1: Auto-publish on GitHub Release

> As a maintainer, I want to automatically publish to PyPI when creating a GitHub Release.

**Requirement Details:**

1. Trigger: GitHub Release event (type: published)
2. Build package using `uv build`
3. Verify package metadata with `twine check`
4. Publish to PyPI using `uv publish`
5. Upload dist files as GitHub Release assets

**Acceptance Criteria:**

1. Creating a GitHub Release triggers the workflow automatically
2. Package appears on PyPI within 5 minutes of release
3. Both `.whl` and `.tar.gz` files are attached to the GitHub Release
4. Workflow fails if `twine check` finds metadata issues

---

#### STORY 2: Multi-platform Test Matrix

> As a maintainer, I want to test installation on multiple OS and Python versions.

**Requirement Details:**

1. Test matrix: ubuntu-latest × windows-latest × macos-latest
2. Python versions: 3.10, 3.11, 3.12, 3.13
3. Install from built wheel (not from source)
4. Verify: `import mcp_atlassian` succeeds
5. Verify: `mcp-atlassian-multi --help` CLI entry point works

**Acceptance Criteria:**

1. All 12 combinations (3 OS × 4 Python) pass
2. If any combination fails, publish is blocked
3. Test uses actual built artifact (not re-build)

---

#### STORY 3: Manual TestPyPI Publish

> As a maintainer, I want to manually publish to TestPyPI for pre-release verification.

**Requirement Details:**

1. Trigger: `workflow_dispatch` (manual) with `dry_run` option
2. If `dry_run = false`: publish to TestPyPI
3. If `dry_run = true`: build only, no publish
4. Uses separate `TEST_PYPI_API_TOKEN` secret

**Acceptance Criteria:**

1. Manual trigger available in GitHub Actions UI
2. Package appears on test.pypi.org after manual trigger
3. Dry run mode builds but does not publish

---

#### STORY 4: GitHub Release Assets

> As a user, I want dist files attached to GitHub Releases.

**Requirement Details:**

1. After successful PyPI publish, upload dist/* to the GitHub Release
2. Files: `mcp_atlassian_multi-{version}-py3-none-any.whl` and `.tar.gz`

**Acceptance Criteria:**

1. Release page shows downloadable wheel and sdist files
2. Files match exactly what was published to PyPI

---

## 3. Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `uv` (astral-sh/setup-uv@v3) | CI Tool | Package manager and builder |
| `twine` | CI Tool | Package metadata verification |
| `uv-dynamic-versioning` | Build Plugin | Version from git tags |
| PyPI API Token | Secret | `PYPI_API_TOKEN` in GitHub Secrets |
| TestPyPI API Token | Secret | `TEST_PYPI_API_TOKEN` in GitHub Secrets |
| GitHub Token | Secret | Auto-provided `GITHUB_TOKEN` for release assets |

---

## 4. Risks and Assumptions

### 4.1 Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| PyPI token leak | Critical | Low | Token stored in GitHub Secrets, never in code |
| Version conflict on PyPI | Medium | Low | uv-dynamic-versioning ensures unique versions from git tags |
| Windows glob expansion issue | Low | Medium | Use `bash` shell explicitly for glob patterns |

### 4.2 Assumptions

- Git tags follow PEP 440 versioning (e.g., `v0.1.0`)
- GitHub Environments `pypi` and `testpypi` are configured with appropriate protection rules
- `id-token: write` permission available for trusted publishing (future)

---

## 5. Non-Functional Requirements

| Category | Requirement | Details |
|----------|-------------|---------|
| Reliability | Workflow must not publish partial builds | test-install job gates publish |
| Security | Tokens scoped to minimum permissions | Separate tokens for PyPI vs TestPyPI |
| Performance | Total workflow time < 15 minutes | Parallel matrix execution |
| Auditability | All publish actions logged | GitHub Actions provides full audit trail |
