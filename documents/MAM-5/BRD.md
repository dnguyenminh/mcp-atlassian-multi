# Business Requirements Document (BRD)

## MCP Atlassian Multi — MAM-5: Fix Ruff line-length violations trong test files

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-5 |
| Title | Fix: Ruff line-length violations trong test files |
| Author | BA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Epic | MAM-1 |

---

## 1. Introduction

### 1.1 Scope

Fix 2 dòng code vượt quá giới hạn 88 ký tự (Ruff lint rule E501) trong test files, gây CI failure.

### 1.2 Impact

- **Minimal** — chỉ formatting change, không thay đổi logic
- 2 files affected: `tests/unit/utils/test_date.py`, `tests/unit/utils/test_media.py`

---

## 2. Business Requirements

### 2.1 Problem Statement

Ruff linter (line-length = 88) fail trên CI do 2 dòng quá dài trong test files.

### 2.2 Solution

| File | Issue | Fix |
|------|-------|-----|
| `tests/unit/utils/test_date.py` | `@pytest.mark.skipif(...)` decorator quá dài | Tách thành nhiều dòng |
| `tests/unit/utils/test_media.py` | Conditional expression cho `.zip` MIME type quá dài | Tách thành nhiều dòng |

### 2.3 Acceptance Criteria

1. `ruff check` passes without errors
2. All tests still pass
3. No logic changes

---

## 3. Classification

| Attribute | Value |
|-----------|-------|
| Type | Bug Fix (Lint) |
| Severity | Low |
| Effort | Trivial (< 30 min) |
| Risk | None |
| SDLC Documents Required | BRD only (no FSD/TDD needed for formatting fix) |
