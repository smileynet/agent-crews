---
name: contribution-conventions
description: Discover project contribution conventions before submitting PRs or issues. Use when preparing contributions, writing PR descriptions, or filing issues on any project.
---

# Contribution Conventions Discovery

## When to Use
- Before writing your first PR for a project
- Before filing an issue
- When adapting the SA crew to a new project

## Step 1: Check for Templates

Look for these files (GitHub, GitLab, or local):
```bash
find . -path "*.github/PULL_REQUEST_TEMPLATE*" -o -path "*.github/ISSUE_TEMPLATE*" -o -path "*.gitlab/merge_request_templates*" -o -path "*.gitlab/issue_templates*" 2>/dev/null
```

Also check:
- `CONTRIBUTING.md` — contribution guidelines
- `DESIGN_STANDARDS.md` or `CODING_STANDARDS.md` — code conventions
- `.github/semantic.yml` — commit message enforcement
- `.github/release-drafter.yml` — changelog/release format

## Step 2: Review Recent PRs (Soft Style)

Read 3-5 recently merged PRs to understand the actual style in use:
- How detailed are descriptions? (1 sentence vs full context)
- Do they reference issue numbers?
- What's the commit message format? (conventional commits, free-form, prefixed)
- Are there screenshots or test evidence?
- How are breaking changes communicated?
- What labels are used?

## Step 3: Review Recent Issues

Read 3-5 recent issues to understand:
- How are bugs reported? (repro steps, expected/actual, environment)
- How are features requested? (user story, use case, acceptance criteria)
- What labels are applied?
- Are there assignees or milestones?

## Step 4: Review Recent Commits

Check `git log --oneline -20` for:
- Commit message format (prefix style, scope, length)
- Granularity (one commit per fix, or squashed)
- Co-author patterns
- Sign-off requirements (`Signed-off-by:`)

## Step 5: Document Findings

Write a brief conventions summary to `.kiro/steering/contribution-style.md`:
```markdown
# Contribution Style (discovered from repo history)

## PR Style
- [what you found]

## Commit Style
- [what you found]

## Issue Style
- [what you found]

## Templates
- PR: .github/PULL_REQUEST_TEMPLATE.md
- Issues: .github/ISSUE_TEMPLATE/*.yml
```

## Key Principle

Templates show the **minimum required structure**. Recent history shows the **actual expected quality bar**. Match both.
