# Proposal: Address Deployment Pipeline Gaps

**Date:** 2026-05-16
**Status:** Resolved (2026-05-17) — Gap 1 implemented, Gap 2 implemented, Gap 3 deferred with mitigation documented.
**Context:** Pipeline validation revealed three gaps where configured behavior isn't reaching agents at runtime.

---

## Gap 1: `allowed_commands` not merged into agent toolsSettings

**Problem:** Components declare `allowed_commands` (e.g., verification declares `git *`, `cargo check`). These are substituted with project values but never written to agent JSON. Workers have no `execute_bash.allowedCommands` in their toolsSettings, meaning kiro-cli can't enforce command allowlists.

**Impact:** Medium. Without allowedCommands, workers can run any command. The steering *suggests* which commands to use, but doesn't *enforce* it. This violates the "enforcement over suggestion" principle (ADR-001).

**Proposed fix:**

In `_lib/components.py`, after `write_steering_files`, collect all `allowed_commands` from worker-targeted components and merge them into every worker agent's `toolsSettings.execute_bash.allowedCommands`:

```python
def merge_allowed_commands(components: list[dict], kiro_dir: Path):
    """Merge component allowed_commands into worker agent toolsSettings."""
    commands = []
    for comp in components:
        if "worker" in comp.get("targets", []) or "all" in comp.get("targets", []):
            commands.extend(comp.get("allowed_commands", []))
    commands = [c for c in commands if c]  # filter empty from null placeholders
    if not commands:
        return
    agents_dir = kiro_dir / "agents"
    for agent_file in agents_dir.glob("*.json"):
        data = json.loads(agent_file.read_text())
        if "subagent" in data.get("tools", []):
            continue  # orchestrators don't run commands
        ts = data.setdefault("toolsSettings", {})
        bash = ts.setdefault("execute_bash", {})
        existing = bash.get("allowedCommands", [])
        merged = list(dict.fromkeys(existing + commands))  # dedup, preserve order
        bash["allowedCommands"] = merged
        agent_file.write_text(json.dumps(data, indent=2) + "\n")
```

**Effort:** Small (1 function + call site in `generate_components_for_project`).  
**Risk:** Low. Additive — only adds allowedCommands where none existed.  
**Test:** Update `test_allowed_commands_not_in_agent_json` to assert commands ARE present.

---

## Gap 2: Skills synced but unreferenced by any agent

**Problem:** 28 skills are synced to every project but only 13 are explicitly referenced via `skill://` in agent JSON. The remaining 15 are available for kiro-cli's on-demand loading (user types `@skill-name`) but no agent proactively loads them.

**Impact:** Low. Unreferenced skills still work — kiro-cli can load them when a user or agent mentions them. The cost is disk space (~50KB) and potential confusion about what's "active."

**Options:**

| Option | Tradeoff |
|--------|----------|
| A. Do nothing | Skills are available on-demand. No harm. |
| B. Trim to referenced-only | Saves disk, but removes skills users might want to invoke manually |
| C. Add skill references to relevant agents | More context loaded per agent, but skills are targeted |
| D. Categorize: "agent skills" vs "user skills" | Sync both, but only reference agent skills in JSON |

**Recommendation:** Option D. Add a `shared/skills/manifest.yaml` that categorizes skills:

```yaml
# Skills loaded automatically by agents (referenced in JSON)
agent_skills:
  - verification-protocol
  - git-protocol
  - troubleshooting-protocol
  - completion-protocol

# Skills available for user invocation (@skill-name) but not auto-loaded
user_skills:
  - adr-authoring
  - diagrams
  - presentation-writing
  - tutorial-authoring
  # ... etc
```

Generator reads this manifest. Agent skills get `skill://` references. User skills are synced but not referenced. This makes the distinction explicit and testable.

**Effort:** Small (manifest file + generator reads it for resource injection).  
**Risk:** Low. Purely organizational.

---

## Gap 3: No steering isolation between agent types

**Problem:** kiro-cli loads ALL `.kiro/steering/**/*.md` files with `inclusion: always` into every agent's context, regardless of subdirectory. Workers see orchestrator rules (narration, delegation, memory). Orchestrators see worker rules (verification, troubleshooting). This wastes context tokens and can confuse agents with irrelevant instructions.

**Impact:** Medium. Measured at ~19 steering files × ~200 tokens avg = ~3,800 tokens of steering per agent. Workers receive ~1,500 tokens of orchestrator-only content they'll never use. At scale (14 agents), this is ~21K wasted tokens per session.

**Options:**

| Option | Tradeoff |
|--------|----------|
| A. Do nothing | Accept context bloat. Agents mostly ignore irrelevant steering. |
| B. Use `inclusion: agent_match` | Requires kiro-cli to support per-agent steering filtering (not available) |
| C. Flatten into single steering file per agent type | Lose modularity. One giant file per role. |
| D. Move role-specific steering into agent prompts | Increases prompt size but ensures isolation |
| E. Use `inclusion: conditional` with agent name patterns | Requires kiro-cli feature (not available) |

**Recommendation:** Option A (short-term) + file a kiro-cli feature request for Option B.

Rationale: The current bloat (~1,500 extra tokens per agent) is within acceptable bounds. Agents already handle mixed instructions well — they follow what's relevant to their role. The real fix requires kiro-cli to support `inclusion: agent_match` or similar filtering. Until then, the subdirectory structure serves as documentation for humans even if it doesn't provide runtime isolation.

**If context pressure becomes measurable** (agents hitting limits, degraded performance), implement Option D as a stopgap: move the 4-5 most critical role-specific steering sections into the agent's `prompt` field directly, and remove them from steering files.

**Effort:** None (short-term). Feature request (medium-term).  
**Risk:** None.

---

## Implementation Priority

| Gap | Priority | Effort | When |
|-----|----------|--------|------|
| 1. allowed_commands | P1 | Small | Next session — enforcement principle violated |
| 2. Skill manifest | P3 | Small | When adding new skills — organizational improvement |
| 3. Steering isolation | P4 | None/External | File feature request, revisit if context pressure observed |

---

## Success Criteria

- [x] Gap 1: `test_allowed_commands_in_worker_agents` asserts commands ARE present (c31b48c)
- [x] Gap 1: Workers in component-enabled projects have `execute_bash.allowedCommands`
- [x] Gap 2: `shared/skills/manifest.yaml` exists; generator reads it for archetype injection
- [x] Gap 2: `test_manifest_classifies_all_skills` enforces every skill on disk is classified
- [ ] Gap 3: Feature request filed for kiro-cli steering filtering (external — track in upstream tracker)