---
name: testing-patterns
description: Testing strategies and patterns. Use when writing tests, choosing test approaches, or improving test coverage.
---

# Testing Patterns

## Principles

### Test behaviors, not implementations
Tests verify what code promises to callers — not internal mechanics. A test that breaks on refactoring (without behavior change) is testing the wrong thing.

### Tests are specifications
Write tests before implementation when possible. A test written first defines "correct" unambiguously — critical for AI-generated code where the generator needs falsifiable success criteria.

### Pure functions need no mocks
Functions that compute solely from arguments are trivially testable. If a test requires elaborate mocks, the code under test has too many dependencies — refactor the design, not the test.

### Avoid test fragility
Tests coupled to internal structure break on every refactoring. Signals: asserting on internal method calls, breaking when you rename a private helper, mirroring implementation step-by-step.

### Honest signatures enable test design
If a function says `Result<User, NotFound>`, there are exactly two cases to test. Fix the signature first; tests follow naturally.

## Test Pyramid

```
        /  E2E  \        Few, slow, high confidence
       / Integration \    Some, medium speed
      /    Unit Tests   \  Many, fast, focused
```

For demos/PoCs: unit + a few integration tests. Skip E2E unless customer-facing.

## Rules

- One assertion per concept — tests should fail for one reason
- Descriptive names: `'returns 404 when user not found'` not `'test1'`
- No test interdependence — each test runs independently
- Fast feedback — unit tests <1s each, full suite <30s
- Infrastructure tests: snapshot for drift detection, assertion for specific resources
- Mock at boundaries (HTTP, DB, filesystem) — not internal functions

## Domain Examples (read on demand for your stack)

- TypeScript/CDK: snapshot tests, `Template.fromStack()`, resource assertions
- Lambda/API: handler unit tests, `aws-sdk-client-mock` for service mocks
- React: `@testing-library/react`, render + fireEvent + screen queries
- Rust: `#[test]`, `assert_eq!`, `mockall` for trait mocks
- Python: `pytest`, fixtures, `unittest.mock.patch`

Don't memorize these — generate the right pattern from the principles above when you know the stack.
