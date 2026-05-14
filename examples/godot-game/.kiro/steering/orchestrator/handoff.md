---
inclusion: always
---
# Handoff Protocol (Scope-Based)

## Routing Table


## Rules
- When work shifts outside your crew's declared scope, suggest handoff
- Use the routing table above to recommend the correct crew/agent
- Format: "This looks like [crew] territory. Switch with [command]"
- Never absorb work that belongs to another crew
- If no crew matches, ask the user where to route it

## Refusal
When a request falls in your `refuses` list:
- Acknowledge the request
- Explain which crew handles it
- Provide the switch command
- Do NOT attempt partial work on refused tasks

## Scope Shift Detection
When user's request shifts to a new task domain:
- Narrate: "Scope shift: [current domain] → [new domain]"
- Check routing table for better-fit crew
- If current crew handles it: proceed
- If another crew is better: suggest handoff
