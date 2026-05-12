# Technical Design Document (TDD)

## MCP Atlassian Multi — MAM-4: CI/CD Build & Publish to PyPI workflow

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-4 |
| Title | CI/CD: Build & Publish to PyPI workflow |
| Author | SA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Related BRD | BRD-v1-MAM-4.docx |

---

## 1. Introduction

### 1.1 Purpose

Technical design cho GitHub Actions workflow `publish.yml` — build, test, và publish `mcp-atlassian-multi` package lên PyPI.

### 1.2 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| CI Platform | GitHub Actions | v4 (actions) |
| Package Manager | uv (astral-sh) | latest |
| Build Backend | hatchling | latest |
| Versioning | uv-dynamic-versioning | ≥ 0.7.0 |
| Verification | twine | latest |
| Release Upload | softprops/action-gh-release | v2 |

---

## 2. Workflow Architecture

### 2.1 Job Dependency Graph

```
┌─────────┐
│  build  │ ← Always runs first
└────┬────┘
     │ artifact: dist/
     ▼
┌──────────────┐
│ test-install │ ← Matrix: 3 OS × 4 Python
└──────┬───────┘
       │ (all pass)
       ├──────────────────────────┐
       ▼                          ▼
┌────────────────┐    ┌───────────────────┐
│publish-testpypi│    │   publish-pypi    │
│(manual trigger)│    │(release trigger)  │
└────────────────┘    └─────────┬─────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ github-release-assets   │
                    └─────────────────────────┘
```

### 2.2 Trigger Configuration

```yaml
on:
  release:
    types: [published]        # Auto-trigger on GitHub Release
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        default: false        # Manual trigger with dry-run option
```

---

## 3. Job Specifications

### 3.1 Job: build

| Aspect | Detail |
|--------|--------|
| Runner | ubuntu-latest |
| Python | 3.10 |
| Steps | checkout (depth 0) → setup-python → install uv → `uv build` → `twine check dist/*` → upload artifact |

**Key Design Decisions:**

- `fetch-depth: 0`: Required for `uv-dynamic-versioning` to read git tags
- `twine check`: Validates metadata before any publish attempt
- Artifact name: `dist` (shared across all downstream jobs)

### 3.2 Job: test-install

| Aspect | Detail |
|--------|--------|
| Runner | Matrix: ubuntu-latest, windows-latest, macos-latest |
| Python | Matrix: 3.10, 3.11, 3.12, 3.13 |
| Steps | setup-python → download artifact → `pip install dist/*.whl` → verify import → verify CLI |

**Key Design Decisions:**

- `shell: bash` for wheel installation: Ensures glob `*.whl` works on Windows (PowerShell doesn't expand globs the same way)
- Install from wheel (not sdist): Tests the actual distributable artifact
- CLI verification uses `|| true`: `--help` may exit non-zero on some configurations

### 3.3 Job: publish-testpypi

| Aspect | Detail |
|--------|--------|
| Condition | `workflow_dispatch` AND `dry_run == false` |
| Environment | `testpypi` (GitHub Environment with URL) |
| Permissions | `id-token: write` (for future trusted publishing) |
| Publish URL | `https://test.pypi.org/legacy/` |
| Token | `TEST_PYPI_API_TOKEN` secret |

### 3.4 Job: publish-pypi

| Aspect | Detail |
|--------|--------|
| Condition | `release` event AND `action == published` |
| Environment | `pypi` (GitHub Environment with URL) |
| Permissions | `id-token: write` |
| Publish URL | Default PyPI (no --publish-url needed) |
| Token | `PYPI_API_TOKEN` secret |

### 3.5 Job: github-release-assets

| Aspect | Detail |
|--------|--------|
| Condition | After `publish-pypi` succeeds, only on `release` event |
| Permissions | `contents: write` |
| Action | `softprops/action-gh-release@v2` |
| Files | `dist/*` (wheel + sdist) |

---

## 4. Security Design

### 4.1 Secret Management

| Secret | Scope | Usage |
|--------|-------|-------|
| `PYPI_API_TOKEN` | Environment: pypi | Publish to production PyPI |
| `TEST_PYPI_API_TOKEN` | Environment: testpypi | Publish to TestPyPI |
| `GITHUB_TOKEN` | Auto-provided | Upload release assets |

### 4.2 Permission Model

```yaml
# Minimal permissions per job
publish-pypi:
  permissions:
    id-token: write    # For OIDC trusted publishing (future)

github-release-assets:
  permissions:
    contents: write    # For uploading to releases
```

### 4.3 Environment Protection

- `pypi` environment: Should have required reviewers for production publishes
- `testpypi` environment: Can be less restrictive for testing

---

## 5. Implementation Details

### 5.1 File Location

`.github/workflows/publish.yml`

### 5.2 Version Resolution

```
Git tag (e.g., v0.1.0)
    → uv-dynamic-versioning reads tag
    → hatchling builds with version in metadata
    → wheel filename: mcp_atlassian_multi-0.1.0-py3-none-any.whl
```

### 5.3 Windows Compatibility Fix

```yaml
# Problem: PowerShell doesn't expand *.whl glob
# Solution: Force bash shell
- name: Install from wheel
  shell: bash
  run: pip install dist/*.whl
```

---

## 6. Deployment Considerations

### 6.1 Prerequisites for First Use

1. Create PyPI project: `mcp-atlassian-multi`
2. Create TestPyPI project: `mcp-atlassian-multi`
3. Generate API tokens for both
4. Add tokens to GitHub repository secrets
5. Create GitHub Environments: `pypi`, `testpypi`

### 6.2 Release Process

1. Developer creates git tag: `git tag v0.1.0`
2. Developer pushes tag: `git push origin v0.1.0`
3. Developer creates GitHub Release from tag
4. Workflow auto-triggers → build → test → publish → attach assets
5. Users can install: `pip install mcp-atlassian-multi`
