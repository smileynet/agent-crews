---
inclusion: always
---

# SA Project Conventions

## Context

These are Solutions Architect workload projects. Internal tooling, customer-facing demos, research, and contribution work.

## Conventions

- **Git hosting**: GitLab (internal) or GitHub. Use `cr` for code reviews or `gh` for GitHub PRs.
- **Internal tools**: Use organization-specific MCP servers and search tools when available.
- **Task runners**: Prefer `just` or `mise`. Use what the project already has.
- **Notifications**: Post to Slack on task completion (>5 min), blockers, and failures.

## Cloud Patterns

- **IAM**: Least privilege. No `*` in actions or resources.
- **Error handling**: Return structured errors. Log with correlation IDs.
- **Environment config**: Use environment variables. No hardcoded ARNs or account IDs.
- **Security**: No 0.0.0.0/0 without auth. No public endpoints without SG restriction.
- **Credentials**: Use managed test accounts. Never test against customer accounts.

## Project Structure

- README.md at root: what it does, how to deploy, how to test
- AGENTS.md: agent onboarding, tasks, config, doc index
- Infrastructure code separate from application code
- Tests colocated with source (or parallel `test/` directory)
- No generated files committed (except lock files)
- `scratch/` directory (gitignored) for intermediate results

## What "done" means

- Code works locally
- Tests pass (if they exist)
- Committed with a meaningful message
- Pushed (if remote exists)
- Slack notification sent (if task took >5 min)

## DO NOT

- Commit API keys or credentials
- Run destructive cloud commands without confirmation
- Modify .kiro/agents/*.json directly (generated files)
