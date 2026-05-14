---
inclusion: always
---

# AI Generation Hygiene

When writing code, do NOT produce these common AI-generation artifacts:

## Don't add redundant defensive checks (P1)
- Don't add `if x is None: raise` when the parameter type is non-Optional
- Don't add `isinstance` checks on already-typed values
- Trust the type system for internal code
- Exception: checks at trust boundaries (user input, network data, deserialization) MUST stay

## Don't wrap everything in try/except (P2)
- Don't catch `Exception` just to log and re-raise unchanged
- Don't use bare `except:`
- Only catch specific exceptions you can handle meaningfully
- Exception: error *transformation* (converting low-level to domain exceptions) is correct

## Don't add comments that restate code (P3)
- No `# increment counter` above `counter += 1`
- No `# return the result` above `return result`
- DO add comments explaining *why* — non-obvious constraints, regulatory requirements, rejected alternatives

## Don't cast to types values already are (P8)
- No `str(f"hello {name}")` — f-strings are already strings
- No `list([1, 2, 3])` — list literals are already lists
- No `str()` on values already typed as `str`

## Don't add gratuitous logging (P9)
- No entry/exit logging: `logger.info("Entering process_user")`
- No parameter echo: `logger.debug(f"user={user}, config={config}")` right after the signature
- DO log meaningful events: errors, state transitions, business decisions
