---
inclusion: always
---
# Git Protocol (PR-Based)

Team/shared workflow: feature branches, PRs to merge.

## Workflow
- Create feature branch from main: `feat/<description>` or `fix/<description>`
- Commit frequently on feature branch
- Push feature branch (never push to main directly)
- Create PR when work is complete and verified
- Never merge your own PR without review

## Branch Naming
- `feat/<short-description>` — new features
- `fix/<short-description>` — bug fixes
- `docs/<short-description>` — documentation
- `chore/<short-description>` — maintenance

## Commit Timing (invariants)
- Commit BEFORE risky operations
- Commit AFTER reaching a working state
- Only commit AFTER verification passes
- Never commit broken code

## Commit Messages
- Use conventional commits: `type(scope): description`
- One logical change per commit
- Message explains WHAT and WHY

## Rules
- Stage explicit files (not `git add .`)
- Never force-push without explicit user permission
- Never push directly to main/master
- Never amend pushed commits
- Keep PRs focused — one concern per PR
