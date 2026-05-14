---
inclusion: always
---
# Git Protocol (Checkpoint)

Solo/personal workflow: commit frequently, push immediately.

## Workflow
- Work directly on current branch (or create feature branch for larger work)
- Commit after each meaningful unit of work
- Push immediately after commit
- No PR required — direct to branch

## Commit Timing (invariants — always true)
- Commit BEFORE risky operations (refactors, dependency changes)
- Commit AFTER reaching a working state
- Only commit AFTER verification passes
- Never commit broken code

## Commit Messages
- Use conventional commits: `type(scope): description`
- Types: feat, fix, docs, chore, refactor, test, style
- Message must explain WHAT changed and WHY (not HOW)
- One logical change per commit

## Rules
- Stage explicit files (not `git add .`)
- Never force-push without explicit user permission
- Never amend pushed commits
- If unsure whether to commit: commit (you can always squash later)
