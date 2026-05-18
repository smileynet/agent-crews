# AI References Review — Recommendations

**Date:** 2026-05-12
**Sources:** matt-skills, nicobailon/pi-extensions, indydevdan
**Gaps Identified:** 33 (4 critical, 10 high, 13 medium, 6 low)

---

## 1. EXECUTIVE SUMMARY

We reviewed three external AI agent framework references (matt-skills for progressive skill disclosure and token efficiency, nicobailon/pi-extensions for delegation safety and observability, indydevdan for iterative review loops and confidence signals) and compared their patterns against our current agent-crews component architecture. We identified 33 gaps across 4 severity levels. The most critical findings are safety-related: agents can spawn infinite sub-agents with no depth guard, orchestrators have no supervisor loop to detect silent worker failures, and verification gates are advisory with no enforcement mechanism. The top priorities for immediate action are adding delegation depth limits, a supervisor timeout, and a preToolUse safety hook — all achievable within existing component YAML structure. Short-term, we need confidence ladders in signaling, file reservation for parallel work, and progressive skill disclosure. Medium-term, we should build an observability event system and implement context modes for delegation.

---

## 2. IMMEDIATE ACTIONS (Week 1)

### 2.1 Delegation Depth Guard
- **What:** Add `max_depth: 3` to orchestrator toolsSettings.subagent and inject a depth counter into spawn hooks
- **Files:** `shared/components/completion/standard.yaml`, `base/crews/general.yaml` (architypes.orchestrator section)
- **Effort:** S
- **Impact:** Prevents infinite sub-agent recursion (Critical #1)
- **Implementation:**
```yaml
# In each crew's orchestrator archetype toolsSettings:
toolsSettings:
  subagent:
    maxDepth: 3
```
And in orchestrator steering, add:
```markdown
## Delegation Depth
- You are at depth 0. Workers you spawn are depth 1.
- Workers MUST NOT spawn sub-agents beyond depth 2.
- If a worker needs further delegation, it must return BLOCKED and you re-route.
```

### 2.2 Supervisor Timeout Loop
- **What:** Add steering rule requiring orchestrators to check worker status after delegation
- **Files:** `shared/components/narration/verified.yaml` (add supervisor section to steering)
- **Effort:** S
- **Impact:** Prevents orchestrator hang on silent worker failure (Critical #2)
- **Implementation:** Add to orchestrator steering:
```markdown
## Supervisor Loop
After delegating to a worker:
1. If worker returns DONE/PARTIAL/BLOCKED/FAILED → process normally
2. If worker returns no signal → treat as FAILED after 1 attempt
3. Never delegate the same task to the same worker twice without changing the approach
4. If 2 workers fail the same task → escalate to user (BLOCKED signal)
```

### 2.3 Verification Enforcement via Steering
- **What:** Strengthen verification gate from advisory to mandatory with explicit anti-patterns
- **Files:** `shared/components/verification/gate.yaml`
- **Effort:** S
- **Impact:** Makes phase gates harder to skip (Critical #3, #4)
- **Implementation:** Prepend to steering:
```markdown
## MANDATORY — No Exceptions
You CANNOT report DONE without completing the gate workflow.
If you report DONE without evidence, the orchestrator WILL reject your signal.
Skipping verification is a protocol violation equivalent to FAILED.
```

### 2.4 Builder/Validator Tool Separation
- **What:** Remove `shell` from reviewer agent tools; reviewer should only read and report
- **Files:** `base/crews/general.yaml` (reviewer agent), `base/crews/bug-fix.yaml` (reviewer agent)
- **Effort:** S
- **Impact:** Prevents reviewer from fixing instead of reporting (High #13)
- **Implementation:**
```yaml
# reviewer agent definition
- name: reviewer
  tools: [read]
  allowedTools: [read]
```

### 2.5 preToolUse Safety Hook (Shell Guard)
- **What:** Add a preToolUse hook that blocks dangerous shell commands
- **Files:** `shared/components/verification/gate.yaml` (add hooks section)
- **Effort:** S
- **Impact:** Catches destructive commands before execution (High #14)
- **Implementation:**
```yaml
hooks:
  preToolUse:
    - matcher: "execute_bash"
      command: |
        echo "$TOOL_INPUT" | grep -qE "(rm -rf /|DROP TABLE|git push --force)" && echo "BLOCKED: destructive command" && exit 1 || exit 0
      timeout_ms: 5000
```

### 2.6 Task Priority Labels
- **What:** Add P0-P3 priority syntax to task-tracking steering
- **Files:** `shared/components/task-tracking/soft-hard.yaml`
- **Effort:** S
- **Impact:** Enables priority-based work ordering (High #11)
- **Implementation:** Add to steering:
```markdown
## Priority Labels
- P0: Blocking — do immediately, everything else waits
- P1: High — do in current session
- P2: Normal — do when P0/P1 clear
- P3: Low — file as follow-up issue

When planning work, always assign a priority. Execute in P0→P1→P2 order.
Dependencies: note with `blocked-by: [task-id]` if a task requires another first.
```


---

## 3. SHORT-TERM IMPROVEMENTS (Weeks 2-4)

### 3.1 Confidence Ladder in Signaling
- **Spec:** Extend signaling-standard with confidence levels on DONE signals
- **Files to create:** `shared/components/signaling/confidence.yaml` (new variant extending standard)
- **Dependencies:** None
- **Design:**
```yaml
# Confidence levels (required on DONE signals)
# PERFECT   — deterministic proof (all tests pass, build succeeds, lint clean)
# VERIFIED  — independent verification passed (verifier subagent confirmed)
# PARTIAL   — some checks pass, others skipped or N/A
# UNVERIFIED — no automated checks available, self-assessed only
```
Orchestrators use confidence to decide whether to dispatch verifier:
- PERFECT → accept immediately
- VERIFIED → accept
- PARTIAL → dispatch verifier
- UNVERIFIED → always dispatch verifier

### 3.2 File Reservation for Parallel Agents
- **Spec:** Lock file mechanism so parallel workers don't clobber each other
- **Files to create:** `shared/components/file-reservation/claim-based.yaml`
- **Dependencies:** Task tracking component (for task IDs)
- **Design:**
```yaml
name: file-reservation-claim-based
description: "Prevents parallel agents from editing the same files"
targets: [worker]
steering: |
  ---
  inclusion: always
  ---
  # File Reservation
  Before editing any file, declare your claim in `.scratch/reservations.md`:
  ```
  ## [agent-name] — [task-id]
  - src/auth/login.ts
  - src/auth/session.ts
  ```
  Before editing, check if another agent has claimed the file.
  If claimed by another agent → BLOCKED (report conflict).
  Release claims in your DONE signal.
```

### 3.3 Progressive Skill Disclosure
- **Spec:** Skills split into summary (always loaded) + detail (loaded on trigger)
- **Files to modify:** All skills in `shared/skills/`
- **Dependencies:** None (convention change)
- **Design:** Each skill directory gets:
```
shared/skills/<name>/
├── SKILL.md          # ≤30 lines — summary + trigger phrases
└── detail/
    ├── examples.md   # loaded when agent needs examples
    ├── reference.md  # loaded when agent needs full spec
    └── templates/    # loaded when agent needs boilerplate
```
SKILL.md contains only: purpose, when-to-use triggers, and `@import` references to detail files. Agents load detail on-demand via resource references.

### 3.4 Context Modes for Delegation
- **Spec:** Orchestrator specifies how much context a worker receives
- **Files to create:** `shared/components/delegation/context-modes.yaml`
- **Dependencies:** Delegation depth guard (#2.1)
- **Design:**
```yaml
name: delegation-context-modes
description: "Three context modes for sub-agent delegation"
targets: [orchestrator]
steering: |
  ---
  inclusion: always
  ---
  # Context Modes for Delegation
  When dispatching a worker, choose a context mode:

  ## fresh (default)
  Worker gets: task description + relevant file paths only.
  Use for: independent tasks, verification, review.

  ## summary
  Worker gets: task + 5-sentence summary of current state.
  Use for: continuation work, tasks needing prior context.

  ## fork
  Worker gets: task + full conversation excerpt (last 10 exchanges).
  Use for: debugging, complex multi-step work requiring full history.
  ⚠️ Token-expensive. Use sparingly.

  Always prefer `fresh` unless the task genuinely needs prior context.
```

### 3.5 Iterative Review Loop
- **Spec:** Builder → Reviewer → Builder cycle (max 3 iterations)
- **Files to modify:** `shared/components/narration/verified.yaml`
- **Dependencies:** Builder/validator separation (#2.4)
- **Design:** Add to orchestrator steering:
```markdown
## Iterative Review Loop
For code tasks:
1. Dispatch builder → receives DONE
2. Dispatch reviewer (read-only) → receives PASS or CHANGES_REQUESTED
3. If CHANGES_REQUESTED: re-dispatch builder with reviewer feedback
4. Max 3 iterations. If still failing → escalate to user.

Reviewer output format:
- PASS — code meets requirements, no issues
- CHANGES_REQUESTED — list specific issues with file:line references
```

### 3.6 Token Efficiency Mode (Caveman Protocol)
- **Spec:** Compressed communication style for token-constrained contexts
- **Files to create:** `shared/components/signaling/caveman.yaml`
- **Dependencies:** None
- **Design:**
```yaml
name: signaling-caveman
description: "Ultra-compressed signaling for token efficiency (~75% reduction)"
targets: [worker]
steering: |
  ---
  inclusion: always
  ---
  # Caveman Mode (Token Efficiency)
  When token budget is constrained, switch to compressed communication:
  - No articles (a, an, the)
  - No filler words
  - Abbreviate: fn=function, impl=implementation, cfg=config, dep=dependency
  - Status: ✅/⚠️/❌/🔄 instead of DONE/PARTIAL/FAILED/BLOCKED
  - Evidence: command + exit code only, no output unless relevant
  - No explanations unless asked

  Example:
  ✅ Task: add auth middleware
  Evidence: `cargo test` exit 0, `cargo clippy` exit 0
  Files: src/middleware/auth.rs (new), src/main.rs (modified)
  Next: integrate with /api/users endpoint
```


---

## 4. MEDIUM-TERM ARCHITECTURE (Months 1-2)

### 4.1 Observability/Event System
- **Rationale:** Currently no way to trace what happened across a multi-agent session without reading raw JSONL. Need structured events for debugging, metrics, and session analysis.
- **Design:**
  - Events written to `.scratch/events.jsonl` during session
  - Each event: `{"ts": "ISO8601", "agent": "name", "event": "type", "data": {}}`
  - Event types: `task_started`, `task_completed`, `delegation`, `verification_result`, `blocked`, `error`, `file_claimed`, `file_released`
  - `analyze-session.py` reads events for structured reporting
- **Migration path:**
  1. Add event-writing to completion component steering (agents write events as part of protocol)
  2. Update `analyze-session.py` to read `.scratch/events.jsonl` alongside JSONL transcripts
  3. Add `just events <project>` recipe for quick event inspection
- **Risks:** Token cost of writing events. Mitigate with caveman-format events (single line each).

### 4.2 Wave Execution Model
- **Rationale:** Currently orchestrators dispatch workers sequentially. For independent tasks, parallel dispatch (waves) would be faster.
- **Design:**
  - Orchestrator plans work in waves: `Wave 1: [task-a, task-b]` (parallel), `Wave 2: [task-c]` (depends on wave 1)
  - File reservation component prevents conflicts within a wave
  - Orchestrator waits for all wave-N tasks before starting wave-N+1
- **Migration path:**
  1. Add wave planning to task-tracking steering
  2. Integrate file reservation as prerequisite
  3. Update orchestrator prompts to use wave syntax
- **Risks:** Kiro CLI may not support true parallel subagents. Fallback: sequential dispatch within wave but with explicit independence markers.

### 4.3 A2A (Agent-to-Agent) Messaging
- **Rationale:** Workers currently can only communicate back to their orchestrator. Cross-worker coordination (e.g., "I found a bug in your module") requires orchestrator relay.
- **Design:**
  - Message drop: `.scratch/messages/<recipient-agent>.md`
  - Workers check their inbox at task start
  - Messages are append-only, timestamped
  - Orchestrator can broadcast to all workers
- **Migration path:**
  1. Add message-check to agentSpawn hook
  2. Add message-write to completion component
  3. Orchestrator steering: "check .scratch/messages/ for cross-worker findings"
- **Risks:** Message spam. Mitigate with max 3 messages per agent per session.

### 4.4 Custom Compaction Strategy
- **Rationale:** When context window fills, kiro-cli compacts automatically. Agents lose important state. Custom compaction would preserve critical context.
- **Design:**
  - `.scratch/session/compaction-anchor.md` — facts that MUST survive compaction
  - Agent writes critical state here before context fills
  - agentSpawn hook reads compaction-anchor if it exists
  - Format: structured key-value pairs (task, progress, decisions, blockers)
- **Migration path:**
  1. Add compaction-anchor writing to memory component steering
  2. Update agentSpawn hook to cat compaction-anchor if present
  3. Add "write anchor every 5 tool calls" rule to orchestrator steering
- **Risks:** Anchor file grows unbounded. Mitigate with max 50 lines, overwrite (not append).

### 4.5 Dual-Track Problem Solving
- **Rationale:** Single-track solving means if an approach fails, the agent backtracks in the same context (wasting tokens on failed reasoning). Dual-track dispatches two workers with different approaches.
- **Design:**
  - Orchestrator identifies "uncertain" tasks (multiple viable approaches)
  - Dispatches 2 workers with different strategies (fresh context each)
  - First to return DONE with PERFECT/VERIFIED confidence wins
  - Other worker's result discarded (or filed as alternative)
- **Migration path:**
  1. Add dual-track decision criteria to orchestrator steering
  2. Requires file reservation (workers must claim different files or use worktrees)
  3. Add `approach: "description"` field to delegation
- **Risks:** Double token cost. Only use for P0/P1 tasks where speed matters more than cost.


---

## 5. NEW COMPONENTS TO CREATE

### 5.1 `delegation/depth-guard`
- **Purpose:** Enforce maximum delegation depth, prevent infinite recursion
- **Used by:** All crews (orchestrator target)
- **Structure:**
```yaml
name: delegation-depth-guard
description: "Prevents infinite sub-agent spawning with depth limits"
targets: [orchestrator]
prompt: ""
allowed_commands: []
resources: []
hooks: {}
steering: |
  ---
  inclusion: always
  ---
  # Delegation Depth Guard
  
  ## Rules
  - Maximum delegation depth: 3 (you → worker → sub-worker)
  - Track depth in task description: `[depth:N]` prefix
  - Workers at depth 2 MUST NOT delegate. Return BLOCKED if task needs further breakdown.
  - If you receive BLOCKED from a depth-2 worker needing delegation, break the task smaller yourself.
  
  ## Violation Response
  If a worker spawns beyond depth 3, treat its output as FAILED.
  Re-plan with smaller, self-contained tasks.
subagents: []
```

### 5.2 `supervision/timeout`
- **Purpose:** Detect and recover from silent worker failures
- **Used by:** All crews (orchestrator target)
- **Structure:**
```yaml
name: supervision-timeout
description: "Supervisor loop — detect silent failures and recover"
targets: [orchestrator]
prompt: ""
allowed_commands: []
resources: []
hooks: {}
steering: |
  ---
  inclusion: always
  ---
  # Supervisor Loop
  
  After dispatching a worker:
  1. Worker MUST return a signal (DONE/PARTIAL/BLOCKED/FAILED)
  2. If worker returns empty or malformed response → treat as FAILED
  3. If worker returns DONE without Evidence field → treat as UNVERIFIED, dispatch verifier
  4. Never re-dispatch same task to same worker without changing approach
  5. After 2 different workers fail same task → BLOCKED to user
  
  ## Recovery Actions
  | Worker Response | Your Action |
  |----------------|-------------|
  | DONE + evidence | Accept or verify |
  | DONE no evidence | Dispatch verifier |
  | PARTIAL | Decide: continue or re-plan |
  | BLOCKED | Unblock or re-route |
  | FAILED | Try different worker/approach |
  | No response | Log as FAILED, try different worker |
subagents: []
```

### 5.3 `file-reservation/claim-based`
- **Purpose:** Prevent parallel agents from editing same files
- **Used by:** All crews with parallel workers (worker target)
- **Structure:**
```yaml
name: file-reservation-claim-based
description: "File locking via claim declarations for parallel safety"
targets: [worker]
prompt: ""
allowed_commands: []
resources: []
hooks: {}
steering: |
  ---
  inclusion: always
  ---
  # File Reservation Protocol
  
  ## Before Editing
  1. Check `.scratch/reservations.md` for existing claims
  2. If target file is claimed by another agent → BLOCKED (report conflict)
  3. Declare your claims:
  ```
  ## [your-agent-name] — [task-id]
  - path/to/file1.ts
  - path/to/file2.ts
  ```
  
  ## After Completing
  Remove your claims from `.scratch/reservations.md` in your completion sequence.
  
  ## Conflict Resolution
  - First claim wins (check timestamp in file)
  - If you need a claimed file urgently → return BLOCKED with reason
  - Orchestrator resolves conflicts by sequencing tasks
subagents: []
```

### 5.4 `signaling/confidence`
- **Purpose:** Add confidence levels to completion signals
- **Used by:** All crews (all targets)
- **Structure:**
```yaml
name: signaling-confidence
description: "Confidence ladder for completion signals"
targets: [all]
prompt: ""
allowed_commands: []
resources: []
hooks: {}
steering: |
  ---
  inclusion: always
  ---
  # Confidence Levels
  
  Every DONE signal MUST include a confidence level:
  
  | Level | Meaning | Evidence Required |
  |-------|---------|-------------------|
  | PERFECT | All automated checks pass | build ✅ test ✅ lint ✅ |
  | VERIFIED | Independent verification passed | verifier confirmed |
  | PARTIAL | Some checks pass, others N/A | list what passed and what's missing |
  | UNVERIFIED | No automated checks available | self-assessment only |
  
  Format:
  ```
  ## DONE [PERFECT]
  - Task: ...
  - Confidence: PERFECT — build, test, lint all pass
  - Evidence: ...
  ```
  
  Orchestrator behavior by confidence:
  - PERFECT → accept immediately
  - VERIFIED → accept
  - PARTIAL → may dispatch verifier
  - UNVERIFIED → always dispatch verifier
subagents: []
```

### 5.5 `safety/pre-tool-hooks`
- **Purpose:** Block dangerous operations before execution
- **Used by:** All crews (worker target)
- **Structure:**
```yaml
name: safety-pre-tool-hooks
description: "preToolUse hooks blocking destructive operations"
targets: [worker]
prompt: ""
allowed_commands: []
resources: []
hooks:
  preToolUse:
    - matcher: "execute_bash"
      command: |
        INPUT="$TOOL_INPUT"
        if echo "$INPUT" | grep -qE "(rm -rf /|rm -rf \.|DROP TABLE|DROP DATABASE|git push --force|git reset --hard|git clean -f|:(){ :|:& };:)"; then
          echo "🛑 BLOCKED: Destructive command detected. Use explicit user permission."
          exit 1
        fi
        exit 0
      timeout_ms: 5000
steering: |
  ---
  inclusion: always
  ---
  # Safety Hooks
  
  A preToolUse hook guards against destructive shell commands.
  If your command is blocked, do NOT attempt to bypass.
  Instead: report BLOCKED with the command you need and why.
  The user will grant explicit permission if appropriate.
subagents: []
```


---

## 6. NEW SKILLS TO CREATE

### 6.1 `progressive-debugging`
- **Triggers:** "debug", "why is this failing", "trace the error", "root cause"
- **Directory:**
```
shared/skills/progressive-debugging/
├── SKILL.md              # Summary: when to use, 5-why methodology pointer
└── detail/
    ├── five-whys.md      # Full 5-why technique with examples
    ├── bisect.md         # Git bisect workflow
    ├── boundary.md       # Boundary diagnostic technique
    └── reduction.md      # Minimal reproduction steps
```
- **SKILL.md outline:**
```markdown
---
triggers: [debug, failing, error, root cause, trace, bisect]
---
# Progressive Debugging

Use when: something is broken and the cause is unclear.

## Quick Reference
1. Reproduce → 2. Isolate → 3. Hypothesize → 4. Verify → 5. Fix

## Methodology Selection
- Known file, unknown line → `@import detail/bisect.md`
- Unknown origin → `@import detail/five-whys.md`
- Works in one env, fails in another → `@import detail/boundary.md`
- Complex failure → `@import detail/reduction.md`
```

### 6.2 `delegation-patterns`
- **Triggers:** "delegate", "dispatch", "break down", "plan tasks", "coordinate"
- **Directory:**
```
shared/skills/delegation-patterns/
├── SKILL.md
└── detail/
    ├── wave-planning.md      # Parallel wave execution
    ├── context-modes.md      # fresh/summary/fork decision tree
    ├── task-sizing.md        # How to size tasks for workers
    └── failure-recovery.md   # What to do when workers fail
```
- **SKILL.md outline:**
```markdown
---
triggers: [delegate, dispatch, plan, coordinate, break down, parallelize]
---
# Delegation Patterns

Use when: you need to dispatch work to sub-agents effectively.

## Decision Tree
- Independent tasks? → Wave execution (`@import detail/wave-planning.md`)
- Worker needs context? → Context modes (`@import detail/context-modes.md`)
- Task too big? → Sizing guide (`@import detail/task-sizing.md`)
- Worker failed? → Recovery (`@import detail/failure-recovery.md`)

## Quick Rules
- Default context mode: fresh
- Max task size: achievable in <20 tool calls
- Always include success criteria in task description
- One concern per worker (don't mix testing + implementation)
```

### 6.3 `token-efficiency`
- **Triggers:** "save tokens", "efficient", "budget", "caveman", "compress"
- **Directory:**
```
shared/skills/token-efficiency/
├── SKILL.md
└── detail/
    ├── caveman-protocol.md   # Full caveman communication rules
    ├── read-patterns.md      # Efficient file reading (targeted lines, not full files)
    └── delegation-cost.md    # When delegation costs more than doing it yourself
```
- **SKILL.md outline:**
```markdown
---
triggers: [tokens, efficient, budget, caveman, compress, cost]
---
# Token Efficiency

Use when: context window is filling up or task is simple enough for compressed communication.

## Quick Wins
- Read specific line ranges, not entire files
- Use grep/code search before reading
- Don't re-read files you've already seen (use .scratch notes)
- Caveman mode for simple tasks (`@import detail/caveman-protocol.md`)

## Cost Awareness
- Delegation overhead: ~2000 tokens per dispatch
- Only delegate if task would take >10 tool calls to do yourself
- Fresh context mode is cheapest; fork is most expensive
```

### 6.4 `grilling-pattern`
- **Triggers:** "review", "challenge", "stress test", "poke holes", "critique"
- **Directory:**
```
shared/skills/grilling-pattern/
├── SKILL.md
└── detail/
    ├── architecture-review.md   # Questions for architecture decisions
    ├── code-review.md           # Questions for code changes
    └── plan-review.md           # Questions for implementation plans
```
- **SKILL.md outline:**
```markdown
---
triggers: [review, challenge, stress test, critique, poke holes, grilling]
---
# Grilling Pattern

Use when: validating decisions, plans, or implementations before committing.

## Process
1. State what you're reviewing and its claimed benefits
2. Ask 3-5 pointed questions (not softballs)
3. For each answer, follow up with "what if X fails?"
4. Rate confidence: HIGH (all answers solid) / MEDIUM (some gaps) / LOW (rethink needed)

## Question Categories
- Failure modes: "What happens when X goes wrong?"
- Scale: "Does this work with 10x the load/data/agents?"
- Alternatives: "Why this over [obvious alternative]?"
- Dependencies: "What breaks if [dependency] changes?"
- Reversibility: "How do we undo this if it's wrong?"
```


---

## 7. CREW IMPROVEMENTS

### 7.1 General Crew (`base/crews/general.yaml`)

| Change | Rationale | Priority |
|--------|-----------|----------|
| Remove `shell` from reviewer tools | Reviewer should report, not fix (High #13) | Week 1 |
| Add `maxDepth: 3` to orchestrator subagent settings | Prevent infinite recursion (Critical #1) | Week 1 |
| Add supervisor loop rules to orchestrator prompt | Detect silent failures (Critical #2) | Week 1 |
| Add confidence level requirement to builder prompt | Enable confidence ladder (High #5) | Week 2 |
| Add wave planning section to orchestrator prompt | Enable parallel dispatch (Medium #25) | Month 1 |

**Orchestrator prompt additions:**
```yaml
# Add to general-lead prompt:
prompt: |
  ...existing content...

  ## Supervisor Protocol
  - Every dispatched worker MUST return a structured signal
  - No signal = FAILED. Re-route to different worker.
  - Same task fails twice with different workers = BLOCKED to user.
  - Track: worker dispatched → signal received → action taken

  ## Delegation Depth
  - You are depth 0. Workers are depth 1. They cannot sub-delegate beyond depth 2.
  - Prefer flat delegation (many depth-1 workers) over deep chains.
```

### 7.2 Bug-Fix Crew (`base/crews/bug-fix.yaml`)

| Change | Rationale | Priority |
|--------|-----------|----------|
| Add iterative review loop to orchestrator | Single-pass misses regressions (High #9) | Week 2 |
| Add `progressive-debugging` skill reference | Workers re-derive debugging methodology (High #7) | Week 2 |
| Remove `shell` from reviewer | Same as general crew | Week 1 |

### 7.3 Infrastructure Crew (`base/crews/infrastructure.yaml`)

| Change | Rationale | Priority |
|--------|-----------|----------|
| Add preToolUse hook for destructive commands | Infra commands are high-risk (High #14) | Week 1 |
| Add plan-review gate before apply | Phase gate enforcement (Critical #3) | Week 1 |

### 7.4 Research Crew (`base/crews/research.yaml`)

| Change | Rationale | Priority |
|--------|-----------|----------|
| Set narration to `evidence` (not `verified`) | Research can't always be deterministically verified | Week 2 |
| Add confidence levels to findings | Distinguish sourced vs inferred claims (High #5) | Week 2 |

### 7.5 All Crews — Universal Changes

| Change | Files | Priority |
|--------|-------|----------|
| Add `file-reservation` component to fleet defaults | `fleet.yaml` | Week 3 |
| Add `delegation/depth-guard` component | `fleet.yaml` | Week 1 |
| Add `supervision/timeout` component | `fleet.yaml` | Week 1 |
| Add `safety/pre-tool-hooks` component | `fleet.yaml` | Week 1 |
| Add `signaling/confidence` component | `fleet.yaml` | Week 2 |

**fleet.yaml changes:**
```yaml
defaults:
  components:
    # ...existing...
    delegation: depth-guard          # NEW
    supervision: timeout             # NEW
    safety: pre-tool-hooks           # NEW
    file_reservation: claim-based    # NEW (week 3)
    signaling: confidence            # REPLACES standard (week 2)
```


---

## 8. GENERATOR/TOOLING IMPROVEMENTS

### 8.1 `generate.py` Changes

| Change | Description | Priority |
|--------|-------------|----------|
| Component dependency validation | Warn if `file-reservation` declared without `task-tracking` | Month 1 |
| Depth guard injection | Auto-add `[depth:0]` to orchestrator prompts when delegation component active | Week 1 |
| Confidence variant merge | When `signaling: confidence` is set, merge confidence steering with standard signaling | Week 2 |
| Hook merging from components | Currently hooks from components aren't merged — fix to deep-merge hooks from all active components | Week 1 |
| Staleness check for new components | Add new component directories to the staleness source list | Week 1 |

**Hook merging fix (generate.py):**
```python
# In build_agent() or component assembly, merge hooks from all components:
def merge_hooks(base_hooks: dict, component_hooks: dict) -> dict:
    """Merge component hooks into base. Same matcher = last wins."""
    result = {k: list(v) for k, v in base_hooks.items()}
    for hook_type, hook_list in component_hooks.items():
        if hook_type not in result:
            result[hook_type] = []
        existing_matchers = {h.get("matcher") for h in result[hook_type]}
        for hook in hook_list:
            if hook.get("matcher") not in existing_matchers:
                result[hook_type].append(hook)
    return result
```

### 8.2 Justfile Additions

```just
# ─── New Recipes ─────────────────────────────────────────────────────────────

# Validate component YAML schema
validate-components:
    #!/usr/bin/env bash
    set -e
    FAIL=0
    for f in shared/components/**/*.yaml; do
      if ! python -c "import yaml; d=yaml.safe_load(open('$f')); assert 'name' in d and 'targets' in d and 'steering' in d, f'Missing required fields in $f'" 2>&1; then
        echo "  ❌ $f"
        FAIL=1
      else
        echo "  ✅ $f"
      fi
    done
    [ $FAIL -eq 0 ] && echo "All components valid" || exit 1

# Show token budget estimate for a project
token-budget project:
    #!/usr/bin/env bash
    echo "Token budget estimate for {{project}}:"
    STEERING=$(find projects/{{project}}/.kiro/steering -name "*.md" -exec wc -w {} + 2>/dev/null | tail -1 | awk '{print $1}')
    PROMPTS=$(find projects/{{project}}/.kiro/prompts -name "*.md" -exec wc -w {} + 2>/dev/null | tail -1 | awk '{print $1}')
    echo "  Steering: ~$((STEERING * 4 / 3)) tokens ($STEERING words)"
    echo "  Prompts:  ~$((PROMPTS * 4 / 3)) tokens ($PROMPTS words)"
    echo "  Total:    ~$(((STEERING + PROMPTS) * 4 / 3)) tokens"

# Diff current output vs regenerated (dry-run check)
diff-check project:
    #!/usr/bin/env bash
    TMPDIR=$(mktemp -d)
    cp -r projects/{{project}}/.kiro "$TMPDIR/before"
    just generate {{project}}
    diff -r "$TMPDIR/before" projects/{{project}}/.kiro || echo "Differences found"
    rm -rf "$TMPDIR"

# List all events from last session
events project:
    #!/usr/bin/env bash
    if [ -f "projects/{{project}}/.scratch/events.jsonl" ]; then
      cat "projects/{{project}}/.scratch/events.jsonl" | python -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    print(f\"{e['ts'][:19]} [{e['agent']:15}] {e['event']}: {json.dumps(e.get('data',''))[:80]}\")
"
    else
      echo "No events file found"
    fi
```

### 8.3 agentSpawn Hook Enhancement

Current hook creates `.scratch/` and checks git. Enhance to:

```yaml
hooks:
  agentSpawn:
    - command: |
        printf '\033]2;%s\033\\' "{{agent_name}}"
        echo "🤖 {{agent_name}} ready"
        mkdir -p .scratch/maps .scratch/messages .scratch/session
        grep -qx '.scratch/' .gitignore 2>/dev/null || echo '.scratch/' >> .gitignore
        # Check for messages
        if [ -f ".scratch/messages/{{agent_name}}.md" ]; then
          echo "📬 You have messages:"
          cat ".scratch/messages/{{agent_name}}.md"
        fi
        # Check for compaction anchor
        if [ -f ".scratch/session/compaction-anchor.md" ]; then
          echo "📌 Resuming from anchor:"
          cat ".scratch/session/compaction-anchor.md"
        fi
        # Git status
        if ! git remote get-url origin >/dev/null 2>&1; then
          echo "⚠️ NO GIT REMOTE. Push disabled."
        fi
        git status --short 2>/dev/null || true
```

### 8.4 postToolUse Auto-Lint Hook

```yaml
# Add to shared/components/verification/gate.yaml hooks section:
hooks:
  postToolUse:
    - matcher: "fs_write"
      command: |
        FILE="$TOOL_OUTPUT_PATH"
        EXT="${FILE##*.}"
        case "$EXT" in
          ts|tsx|js|jsx) npx eslint --fix "$FILE" 2>/dev/null || true ;;
          py) ruff format "$FILE" 2>/dev/null || black "$FILE" 2>/dev/null || true ;;
          rs) rustfmt "$FILE" 2>/dev/null || true ;;
          go) gofmt -w "$FILE" 2>/dev/null || true ;;
        esac
      timeout_ms: 30000
```

### 8.5 Smoke Test Enhancement

Add protocol compliance checks to `scripts/smoke-test.sh`:
- Verify all generated agents have `resources` pointing to existing steering files
- Verify orchestrators have `subagent` in tools and `availableAgents` in toolsSettings
- Verify workers do NOT have `subagent` in tools (except at depth < max)
- Verify no steering file exceeds 200 lines (token budget guard)


---

## 9. DECISION LOG

### Adopted

| # | Decision | Source | Rationale |
|---|----------|--------|-----------|
| D-R01 | Delegation depth guard via steering (not runtime enforcement) | nicobailon/pi-extensions | Kiro CLI doesn't support runtime depth limits; steering-based is achievable now |
| D-R02 | Confidence ladder as separate component (not merged into signaling-standard) | matt-skills | Allows gradual rollout; projects can opt-in without breaking existing signaling |
| D-R03 | File reservation via convention (.scratch file) not filesystem locks | indydevdan | Cross-platform, no tooling dependency, agents can read/write markdown |
| D-R04 | Caveman mode as opt-in variant, not default | matt-skills | 75% token reduction is great but hurts debuggability; use for simple tasks only |
| D-R05 | preToolUse hooks for safety (not deniedCommands expansion) | nicobailon/pi-extensions | Hooks can pattern-match; deniedCommands is exact-match only |
| D-R06 | Iterative review max 3 loops | indydevdan | Diminishing returns after 3; prevents infinite review cycles |
| D-R07 | Events as JSONL in .scratch (not external service) | nicobailon/pi-extensions | Zero infrastructure, works offline, easy to parse |

### NOT Adopted (and why)

| # | Pattern | Source | Why Not |
|---|---------|--------|---------|
| N-R01 | LANGUAGE.md per project | matt-skills | Too much overhead for current scale; vocabulary lives in theme.yaml already |
| N-R02 | Justfile four-layer (dev/ci/deploy/admin) | indydevdan | Current flat structure is fine for 15 recipes; revisit at 30+ |
| N-R03 | Full A2A messaging protocol | nicobailon/pi-extensions | Deferred to month 2; need file reservation and wave execution first |
| N-R04 | Runtime stop hooks for verification | nicobailon/pi-extensions | Kiro CLI doesn't support stop hooks; steering enforcement is our best option |
| N-R05 | Crew YAML size limits (split at 200 lines) | indydevdan | Our largest (general.yaml at 16KB) is manageable; component extraction already reduces inline content |
| N-R06 | Incremental generation (only regenerate changed) | matt-skills | Full generation takes <2s; optimization not needed yet |
| N-R07 | Component schema validation via JSON Schema | indydevdan | Simple Python assertion in justfile recipe is sufficient for now |
| N-R08 | Scripts directory inside skills | matt-skills | Skills are knowledge, not automation; scripts belong in components |

### Deferred (revisit later)

| # | Pattern | Revisit When |
|---|---------|--------------|
| DF-01 | Custom compaction strategy | After observing compaction issues in production sessions |
| DF-02 | Dual-track problem solving | After wave execution is stable and file reservation proven |
| DF-03 | Agent Brief format (structured task handoff) | After context modes are implemented and tested |
| DF-04 | .out-of-scope records | After iterative review loop proves the need for scope tracking |
| DF-05 | Skill catalog (auto-discovery) | After progressive skill disclosure is implemented |

---

## IMPLEMENTATION TIMELINE

```
Week 1 (Immediate):
├── Delegation depth guard (steering)
├── Supervisor timeout (steering)
├── Verification enforcement (strengthen gate.yaml)
├── Remove shell from reviewer
├── preToolUse safety hook
├── Task priority labels
└── Hook merging fix in generate.py

Week 2-3 (Short-term):
├── Confidence ladder component
├── Progressive skill disclosure (refactor existing skills)
├── Context modes component
├── Iterative review loop
├── Token efficiency skill
└── Signaling variant: confidence

Week 4 (Short-term):
├── File reservation component
├── Delegation patterns skill
├── Grilling pattern skill
├── Progressive debugging skill
└── postToolUse auto-lint hook

Month 2 (Medium-term):
├── Observability event system
├── Wave execution model
├── A2A messaging (basic)
├── Custom compaction strategy
├── Smoke test protocol compliance
└── Token budget tooling
```

---

*Generated by crew-analyst on 2026-05-12. Next review: 2026-06-12.*
