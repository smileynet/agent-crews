---
name: situation-routing
description: Maps observable code situations to applicable principles. Use when routing work, diagnosing issues, or choosing which practice to apply.
---

# Situation Routing

## When to Use
- Deciding which principle applies to a problem
- Routing review feedback to the right concern
- Diagnosing why code is hard to change, test, or understand

## Situation → Principle Map

### Structure Problems

| You observe... | Apply... |
|----------------|----------|
| Function requires scrolling to read | Keep functions small; extract to named helpers |
| Inline comments explain what sections do | Extract each section to a named function |
| High-level code handles low-level details | Layers of abstraction; abstraction barriers |
| Changing implementation breaks distant callers | Abstraction barriers; depend on interfaces not internals |

### Error Handling Problems

| You observe... | Apply... |
|----------------|----------|
| Callers check for -1, null, or empty string | Handle errors explicitly; use Result/Option types |
| Catch-all that logs and continues | Fail fast for unrecoverable; explicit handling for recoverable |
| Bug symptoms far from root cause | Fail fast, fail loud; errors should surface at origin |
| Function returns valid-looking value on failure | Functions must not lie; encode failure in return type |

### State Problems

| You observe... | Apply... |
|----------------|----------|
| Debugging requires tracking mutations across frames | Prefer immutability; functional core |
| Passing object to function changes caller's state | Prefer immutability; copy-on-write |
| Testing requires setting up IO/databases | Functional core / imperative shell; dependency injection |
| Function calculates AND writes to database | Separate actions from calculations |

### Testing Problems

| You observe... | Apply... |
|----------------|----------|
| Refactoring breaks tests without behavior change | Test behaviors, not implementations |
| Every test needs elaborate mock setup | Functional core (pure logic needs no mocks); dependency injection |
| PRs approved in seconds without comments | Automate mechanical checks; enforce review standards |
| Bugs found in production that tests should catch | Build feedback loops; test at behavior boundaries |

### Performance Problems

| You observe... | Apply... |
|----------------|----------|
| Unsure what's slow before optimizing | Measure first; profile before changing |
| Works at 100 items, times out at 10,000 | Choose algorithm by growth rate (O notation) |
| Profiler shows cache misses on hot path | Exploit cache locality; data layout matters |

### Design Problems

| You observe... | Apply... |
|----------------|----------|
| Business rule duplicated in multiple places | Single source of truth |
| Adding feature requires touching unrelated init code | Dependency injection; abstraction barriers |
| Boolean flags that redirect function behavior | Make code hard to misuse; split into separate functions |
| Type allows construction of invalid states | Make illegal states unrepresentable |

## Decision Heuristic for Leads

When routing a task or choosing an approach:
1. Identify the observable symptom (what's wrong or hard)
2. Look up the principle cluster above
3. Apply the narrowest fix first (local refactor > interface change > architecture shift)
4. If the symptom recurs after local fix, escalate to the structural principle
