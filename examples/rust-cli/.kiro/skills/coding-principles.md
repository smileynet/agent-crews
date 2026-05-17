---
name: coding-principles
description: Cross-book consensus principles for writing and evaluating code. Use as decision heuristics when implementing features, reviewing code, or choosing between approaches.
---

# Coding Principles

## When to Use
- Writing new code (apply as design constraints)
- Reviewing code (use as evaluation lenses)
- Choosing between implementation approaches
- Refactoring existing code

## The Principles (ranked by cross-source consensus)

### 1. Separation of Concerns
Each unit does one thing. Data, logic, and effects belong in distinct layers.

**Apply when:** A function does two things, a module mixes IO with computation, or a class handles both persistence and business logic.

**Test:** Can you describe the function without "and"? If not, split it.

### 2. Layers of Abstraction
Each layer speaks in terms of the layer below. Never skip levels or mix vocabulary.

**Apply when:** A high-level function contains low-level details (SQL in a controller, byte manipulation in business logic).

**Test:** Does every line in the function operate at the same level of detail?

### 3. Test Behaviors, Not Implementations
Tests verify what code promises to callers — not how it works internally.

**Apply when:** Writing tests, evaluating test quality, or deciding what to mock.

**Test:** Would this test break if you refactored the implementation without changing behavior? If yes, it's testing the wrong thing.

### 4. Keep Functions Small and Focused
A function should do one thing at one level of abstraction.

**Apply when:** A function exceeds ~20 lines, has multiple levels of nesting, or requires scrolling to read.

**Test:** Can you name it with a verb phrase that fully describes its behavior?

### 5. Prefer Immutability
Default to values that don't change after creation. Mutation is opt-in and bounded.

**Apply when:** Choosing between let/const, deciding whether to mutate an argument, or designing data flow.

**Test:** Could this variable be const/final/readonly? If yes, make it so.

### 6. Handle Errors Explicitly
Signal errors through the type system. Never return magic values or swallow failures silently.

**Apply when:** A function can fail (IO, parsing, validation, network).

**Test:** Can a caller know from the signature alone that this function can fail and what failures are possible?

### 7. Decompose Before Coding
Break the problem into independently solvable subproblems before writing any code.

**Apply when:** Starting a new feature, facing a complex bug, or the solution isn't obvious.

**Test:** Can you list 3-5 subproblems that, solved independently, compose into the full solution?

### 8. Prefer Pure Functions
Functions that compute solely from arguments with no side effects are trivially testable and safe to compose.

**Apply when:** Writing business logic, data transformations, or validation.

**Test:** Does this function read or write anything outside its arguments and return value? If yes, can that be extracted?

### 9. Prefer Composition Over Inheritance
Build complex behavior by combining simple components, not by deriving from class hierarchies.

**Apply when:** Designing relationships between types, adding behavior variants, or seeing inheritance depth > 2.

**Test:** Would a "has-a" relationship work here instead of "is-a"?

### 10. Make Illegal States Unrepresentable
Use the type system so invalid values cannot be constructed.

**Apply when:** Modeling domain state, designing APIs, or seeing runtime validation that could be compile-time.

**Test:** Can a caller construct an instance of this type that violates business rules?

## Decision Heuristic

When choosing between approaches, prefer the one that:
1. Separates concerns more cleanly
2. Makes errors visible in types
3. Keeps functions smaller and purer
4. Makes wrong usage harder (not just documented as wrong)

## Anti-Patterns (flag these always)

| Signal | Issue | Fix |
|--------|-------|-----|
| Function > 20 lines or needs "and" to describe | God Method | Extract each responsibility |
| Empty catch blocks, ignored return values | Silent Error Swallowing | Propagate, log, or convert to explicit failure |
| Signature doesn't match behavior | Functions That Lie | Make signature honest (Result/Option) |
| Module reaches into another's internals | Implicit Coupling | Depend on contracts, not implementations |
| -1, null, empty string as error signals | Magic Values | Option for absence, Result for errors |
| Generic params used by one type, config for unasked variations | Speculative Generality | Build for today, refactor when second use arrives |
| Logic buried 4+ levels deep | Deep Nesting | Early returns, extract to named functions |
| Multiple components mutating shared data | Mutable Shared State | Immutable default, mutation behind single owner |
| Complex optimization without measured bottleneck | Premature Optimization | Clear code first, measure, optimize hot path only |
