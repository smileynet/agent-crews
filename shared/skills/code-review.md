---
name: code-review
description: Code review standards. Use when reviewing code, PRs, or implementations for quality.
---

# Code Review Standards

## Principles

- Review transfers knowledge, not just catches bugs. Every comment should teach.
- Automate the mechanical (style, lint, types in CI). Reserve humans for judgment.
- No LGTM syndrome. If you can't identify what changed and why, you haven't reviewed it.

## Review Priority (check in this order)

### 1. Correctness
- Does it do what it's supposed to?
- Edge cases handled? (null, empty, boundary values)
- Error paths explicit? (no silent swallowing)
- Function signature honestly represents behavior?

### 2. Security
- No hardcoded secrets
- Input validation on all external inputs
- Least-privilege permissions (no wildcards)
- No injection vectors (SQL, XSS, command)

### 3. Design
- Single responsibility per function/class
- Functions at one level of abstraction
- Small and focused (describe without "and")
- Errors in return types, not magic values
- No implicit coupling between modules

### 4. Reliability
- Timeouts on all external calls
- Retries with backoff for transient failures
- Graceful degradation when dependencies fail

### 5. Testing
- New code has tests (behavior, not implementation)
- Happy path + at least one error path
- Deterministic (no flaky timing)

### 6. Performance (only if relevant)
- No N+1 queries
- Pagination for list operations

## Feedback Format

Every comment uses **Request, Reason, Result**:

```
[CRITICAL] file:42 — SQL injection via string interpolation.
  Request: Use parameterized query.
  Reason: User input flows into query string.
  Result: Prevents arbitrary SQL execution.
```

## Severity

- **CRITICAL**: Must fix. Security, data loss, broken functionality.
- **IMPORTANT**: Should fix. Bug, missing error handling, design issue.
- **NIT**: Nice to fix. Style, naming. Don't block on these.

## Antipatterns to Flag

| Signal | Issue |
|--------|-------|
| Function > 20 lines or needs "and" to describe | God method |
| Empty catch blocks, ignored return values | Silent error swallowing |
| Signature doesn't match actual behavior | Functions that lie |
| Module reaches into another's internals | Implicit coupling |
| -1, null, empty string as error signals | Magic values |
| Approval without identifying what changed | LGTM syndrome |

## AI-Specific Patterns (flag during review)

| Pattern | What AI Does | Fix |
|---------|-------------|-----|
| Redundant None checks | `if x is None: raise` on typed non-Optional params | Trust the type system |
| Verbose error wrapping | try/except that logs and re-raises unchanged | Let errors propagate |
| Restating comments | `# check if user exists` above `if user:` | Delete; keep only "why" comments |
| Copy-paste duplication | Repeating blocks instead of extracting | Extract shared function |
| Identity casts | `str(f"...")`, `list([...])` | Remove redundant cast |
| Entry/exit logging | `logger.info("Entering/Exiting func")` | Log meaningful events only |

## False Positives (do NOT flag)

- **Trust boundary checks** — validation on user input/network data is correct even if types say otherwise
- **Error transformation** — `except SpecificError: raise DomainError(...)` is domain modeling
- **Meaningful intermediates** — variables that name a concept aid readability even if used once
- **"Why" comments** — explaining constraints, regulations, or rejected alternatives
