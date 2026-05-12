# Technical Design Document (TDD)

## MCP Atlassian Multi — MAM-2: Rebrand mcp-atlassian → mcp-atlassian-multi

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-2 |
| Title | Rebrand: Rename mcp-atlassian → mcp-atlassian-multi toàn bộ codebase |
| Author | SA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Related BRD | BRD-v1-MAM-2.docx |

---

## 1. Introduction

### 1.1 Purpose

Technical design cho việc rebrand package name across toàn bộ codebase. Đây là thay đổi thuần cosmetic/configuration — không có logic code changes.

### 1.2 Design Principles

- **Minimal disruption**: Chỉ thay đổi tên hiển thị, không thay đổi internal module structure
- **Backward compatible imports**: `mcp_atlassian` Python module name giữ nguyên
- **Comprehensive**: Tất cả user-facing references phải được update

---

## 2. Change Specification

### 2.1 Naming Convention

| Context | Old Name | New Name |
|---------|----------|----------|
| PyPI package | `mcp-atlassian` | `mcp-atlassian-multi` |
| CLI command | `mcp-atlassian` | `mcp-atlassian-multi` |
| Python module | `mcp_atlassian` | `mcp_atlassian` (UNCHANGED) |
| Docker image | `mcp-atlassian` | `mcp-atlassian-multi` |
| Helm chart | `mcp-atlassian` | `mcp-atlassian-multi` |
| Logger names | `mcp-atlassian.*` | `mcp-atlassian-multi.*` |

### 2.2 Files Modified

| # | File | Change |
|---|------|--------|
| 1 | `pyproject.toml` | `name = "mcp-atlassian-multi"`, entry point rename |
| 2 | `README.md` | All references to package name |
| 3 | `CONTRIBUTING.md` | Installation instructions |
| 4 | `SECURITY.md` | Package references |
| 5 | `AGENTS.md` | CLI commands, package references |
| 6 | `CLAUDE.md` | CLI commands |
| 7 | `Dockerfile` | Labels, entry point |
| 8 | `smithery.yaml` | Package name |
| 9 | `.github/workflows/*.yml` | CLI references in CI |
| 10 | `.devcontainer/post-create.sh` | Install commands |
| 11 | `helm/Chart.yaml` | Chart name |
| 12 | `helm/values.yaml` | Image name |
| 13 | `docs/*.mdx` | Installation instructions |
| 14 | `src/mcp_atlassian/utils/logging.py` | Logger name prefix |
| 15 | `.env.example` | Comments referencing package |

### 2.3 Files NOT Modified

| File | Reason |
|------|--------|
| `src/mcp_atlassian/__init__.py` | Python module name stays `mcp_atlassian` |
| `src/mcp_atlassian/**/*.py` (imports) | Internal imports use `mcp_atlassian` |
| `tests/**/*.py` | Tests import `mcp_atlassian` |

---

## 3. Implementation Strategy

### 3.1 Search & Replace Pattern

```bash
# Primary replacements (order matters):
1. "mcp-atlassian-multi" → skip (already correct, from previous partial renames)
2. "mcp-atlassian" → "mcp-atlassian-multi" (in non-Python files)
3. Logger names: "mcp-atlassian." → "mcp-atlassian-multi."
```

### 3.2 Verification

```bash
# After rename, verify no stale references:
grep -r "mcp-atlassian" --include="*.md" --include="*.yml" --include="*.yaml" \
  --include="*.toml" --include="*.json" | grep -v "mcp-atlassian-multi"

# Verify package builds:
uv build
twine check dist/*

# Verify CLI:
uv run mcp-atlassian-multi --help

# Verify imports:
python -c "import mcp_atlassian; print('OK')"
```

---

## 4. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Missed reference | Post-rename grep verification |
| Broken imports | Module name unchanged, only package name changes |
| Docker build failure | Test Docker build after rename |
| Helm deployment issue | Update Helm values, test template rendering |

---

## 5. Deployment Impact

- **PyPI**: New package name → first publish creates new project
- **Docker Hub**: New image name → update deployment configs
- **Existing users**: Must change `pip install` command and CLI invocation
- **No code changes required by users**: `import mcp_atlassian` still works
