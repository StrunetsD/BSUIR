---
description: Core project rules — prohibits unauthorized changes, enforces context management, and mandates Research → Plan → Implement workflow
globs: ["**/*"]
alwaysApply: true
---

# Core Project Rules

## Critical Prohibitions

### 1. No Unauthorized Changes
- NEVER commit changes without explicit permission
- NEVER push to remote repositories without confirmation
- NEVER execute commands that modify system state (git commit, git push, git rebase, npm publish, etc.) without approval
- NEVER perform complex refactors without prior discussion and approval

### 2. Permitted Actions
- Reading files and code analysis — always allowed
- Running safe commands (npm run test, npm run lint, npm run build) for viewing results only
- Proposing changes in "I suggest we do X, do you agree?" format

### 3. Command Execution Rules
Before executing any command that modifies files, alters git history, installs dependencies, or triggers deployment:

1. Ask for permission
2. Explain what the command does
3. Describe potential consequences
4. Wait for explicit confirmation

---

## Context Management

### Hooks
- Use pre-commit hooks to run linter and type checks
- Use pre-push hooks to run tests
- Create hooks via `.husky/` or in `package.json`

### Skills
Break complex tasks into specialized skills:
- `code-reviewer` — code analysis
- `architect` — architecture design
- `debugger` — debugging
- `tester` — test writing

### Context Engineering
1. **Prioritization**: Architecture and security first, then business logic, then implementation details
2. **Formation**: Use `AGENTS.md` for global rules, `.cursor/rules/*.mdc` for specific rules
3. **Limiting**: Don't load entire project at once; analyze only relevant sections
4. **Recovery**: Record current state in `context-session.md` when interrupted

---

## Workflow: Research → Plan → Implement

### Phase 1: Research
Understand the problem, gather information, assess risks.

**Output**:
- Understanding of current state
- List of affected files
- Identified risks
- Questions needing clarification

### Phase 2: Plan
Propose a concrete action plan.

**Output**:
- Clear list of changes
- Step-by-step plan
- Risk assessment
- Approval request

### Phase 3: Implement
Execute changes according to approved plan.

**Rules**:
- Follow approved plan strictly
- If deviations found — return to Plan phase
- Record intermediate results
- After completion — request review

---

## Pre-execution Checklist

Before proposing any changes:

1. Check current state: `git status` and `git diff`
2. Verify no prohibitions are violated
3. Format proposal: "I propose [what]. This affects [files]. Plan: [steps]. Risks: [what could go wrong]. Do you agree?"

---

## Git Operations

### Never Do
- `git commit -a`
- `git push --force` unless explicitly discussed
- `git reset --hard`
- Direct commits to `main`/`master`

### Always Do
- `git status` before any operation
- `git diff` before commit
- Commit messages: `type(scope): description` (feat, fix, refactor, docs, test, chore)

### Approval Flow
1. Show changes via `git diff` or description
2. Wait for explicit approval
3. Commit with proper message
4. Ask before push

---

## Communication Guidelines
- Respond in English
- If unclear — ask for clarification
- When encountering errors — suggest fixes
- Explain non-trivial decisions

---

## Self-Check Questions
1. Am I modifying something critical? → Need approval
2. Is this a commit or push? → Forbidden without permission
3. Is this a complex refactor? → Need discussion and planning
4. Did I follow Research → Plan → Implement? → Must follow process
5. Did I explain what and why? → Must explain

---

**Important**: You are an assistant. Your job is to help, not to make decisions. Any changes affecting code, repository history, or infrastructure require explicit consent.