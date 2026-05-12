# Business Requirements Document (BRD)

## MCP Atlassian Multi — MAM-6: Thiết lập Kiro agents, steering, hooks và document templates

---

## Document Information

| Field | Value |
|-------|-------|
| Jira Ticket | MAM-6 |
| Title | Infra: Thiết lập Kiro agents, steering, hooks và document templates |
| Author | BA Agent |
| Version | 1.0 |
| Date | 2026-05-13 |
| Status | Approved (Post-implementation) |
| Epic | MAM-1 |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-13 | BA Agent | Initiate document — documented from implemented infrastructure |

---

## 1. Introduction

### 1.1 Scope

Thiết lập hạ tầng phát triển tự động hóa theo SDLC pipeline với multi-agent system (Kiro). Bao gồm agent definitions, steering rules, code intelligence hooks, và document templates cho toàn bộ lifecycle.

### 1.2 Out of Scope

- Agent runtime/execution engine (do Kiro platform cung cấp)
- CI/CD pipeline execution (MAM-4)
- Actual document generation (thực hiện bởi agents khi được invoke)

### 1.3 Preliminary Requirement

- Kiro IDE/platform đã được cài đặt
- Repository structure đã ổn định (MAM-2 rebrand hoàn thành)

---

## 2. Business Requirements

### 2.1 List of User Stories

| # | Story | Priority | Source |
|---|-------|----------|--------|
| 1 | As a developer, I want pre-defined AI agents for each SDLC role so that I can invoke specialized assistance | MUST HAVE | MAM-6 |
| 2 | As a developer, I want steering rules that enforce code standards automatically so that code quality is consistent | MUST HAVE | MAM-6 |
| 3 | As a developer, I want document templates for all SDLC artifacts so that generated documents follow a standard format | MUST HAVE | MAM-6 |
| 4 | As a developer, I want code intelligence hooks that auto-index on file changes so that agents always have up-to-date codebase knowledge | SHOULD HAVE | MAM-6 |

---

### 2.3 Details of User Stories

#### STORY 1: AI Agent Definitions

> As a developer, I want pre-defined AI agents for each SDLC role.

**Requirement Details:**

11 agent definitions covering the full SDLC:

| # | Agent | Role | Responsibility |
|---|-------|------|----------------|
| 1 | ba-agent | Business Analyst | BRD, FSD creation |
| 2 | ta-agent | Technical Analyst | FSD enrichment, technical review |
| 3 | sa-agent | Solution Architect | TDD creation |
| 4 | dev-agent | Developer | Code implementation |
| 5 | qa-agent | QA Engineer | STP, STC, test execution |
| 6 | ui-agent | UI Designer | Wireframes, design system |
| 7 | devops-agent | DevOps Engineer | DPG, RLN, deployment |
| 8 | security-agent | Security Engineer | Security review |
| 9 | sm-agent | Scrum Master | Pipeline orchestration |
| 10 | scrum-master | Scrum Master (alt) | Full SDLC coordination |
| 11 | code-indexer | Code Intelligence | Codebase indexing |

**Acceptance Criteria:**

1. Each agent has a `.kiro/agents/{name}.md` definition file
2. Each definition includes: role, responsibilities, tools, constraints
3. Agents can be invoked from Kiro IDE

---

#### STORY 2: Steering Rules

> As a developer, I want steering rules that enforce code standards.

**Requirement Details:**

8 steering files covering different aspects:

| # | File | Purpose |
|---|------|---------|
| 1 | `code-standards.md` | File size limits, naming conventions, function design |
| 2 | `backend-structure.md` | Python project structure rules |
| 3 | `drawio.md` | Diagram generation standards |
| 4 | `jira-workflow.md` | Jira status transition rules |
| 5 | `testing.md` | Test strategy and conventions |
| 6 | `documentation.md` | Document writing standards |
| 7 | `security.md` | Security coding practices |
| 8 | `git-workflow.md` | Branch naming, commit conventions |

**Acceptance Criteria:**

1. Steering files at `.kiro/steering/*.md`
2. Rules are automatically applied to all agent interactions
3. Code standards enforce: max 200 lines/file, max 20 lines/function

---

#### STORY 3: Document Templates

> As a developer, I want document templates for all SDLC artifacts.

**Requirement Details:**

12 templates covering full SDLC documentation:

| # | Template | Purpose |
|---|----------|---------|
| 1 | BRD-TEMPLATE.md | Business Requirements Document |
| 2 | FSD-TEMPLATE.md | Functional Specification Document |
| 3 | TDD-TEMPLATE.md | Technical Design Document |
| 4 | STP-TEMPLATE.md | Software Test Plan |
| 5 | STC-TEMPLATE.md | Software Test Cases |
| 6 | UG-TEMPLATE.md | User Guide |
| 7 | DPG-TEMPLATE.md | Deployment Guide |
| 8 | RLN-TEMPLATE.md | Release Notes |
| 9 | TEST-REPORT-TEMPLATE.md | Test Execution Report |
| 10 | SECURITY-REPORT-TEMPLATE.md | Security Assessment Report |
| 11 | UI-SPEC-TEMPLATE.md | UI Specification |
| 12 | DESIGN-SYSTEM.md | Design System Reference |

**Acceptance Criteria:**

1. Templates at `documents/templates/*.md`
2. Each template has placeholder variables: `{TICKET_KEY}`, `{SYSTEM_NAME}`, etc.
3. Templates follow consistent structure with Document Info, Revision History, Sign-Off sections

---

#### STORY 4: Code Intelligence Hooks

> As a developer, I want auto-indexing on file changes.

**Requirement Details:**

1. File watcher hooks trigger on create/edit/delete of source files
2. Hooks invoke code-indexer agent to update `.analysis/code-intelligence/`
3. Index includes: project structure, module analysis, file metadata

**Acceptance Criteria:**

1. Hook definitions at `.kiro/hooks/`
2. Creating/editing `.py` files triggers re-index
3. Index output at `.analysis/code-intelligence/`

---

## 3. Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Kiro IDE | Platform | Agent execution environment |
| MCP tools | External | Jira, KB, file system access for agents |
| draw.io | Tool | Diagram generation (referenced in steering) |

---

## 4. Non-Functional Requirements

| Category | Requirement | Details |
|----------|-------------|---------|
| Maintainability | Templates version-controlled | All in git, reviewable via PR |
| Extensibility | Easy to add new agents/templates | Follow naming convention, drop file in folder |
| Consistency | All agents follow same steering rules | Steering applied globally |
