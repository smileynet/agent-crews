# Proposal: Address Deployment Pipeline Gaps

**Date:** 2026-05-16
**Status:** Resolved (2026-05-17) — Gap 1 implemented, Gap 2 implemented, Gap 3 reframed around sparse runtime context and implemented via `project.md` guidance + skeleton upgrade.

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

## Gap 3: Project context is too broad and blurs runtime vs build-time surfaces

**Problem:** Generated agents already get targeted instructions through prompt injection, tool permissions, and archetype-loaded skills. The remaining context risk is the always-loaded project context itself: `project.md` can grow into a general design memo, and in self-hosted repos it can blur what is deployed here (`.kiro/`) versus the source/config that defines the deployment (`.crews/`, templates, generator code).

**Impact:** Medium. Agents waste attention on build-system detail that does not matter for most turns, and they are more likely to edit generated output or describe the wrong surface in handoffs.

**Approach:**

| Step | Change |
|------|--------|
| 1 | Keep `project.md` explicitly sparse — facts most deployed agents need on most turns |
| 2 | Add a runtime-boundary section that distinguishes `.kiro/` deployed artifacts from `.crews/` and other build inputs |
| 3 | Auto-upgrade untouched legacy skeletons so examples and fresh projects converge on the clarified template |
| 4 | Keep reusable behavior in prompts, components, and skills instead of repeating it in always-loaded project context |

**Recommendation:** Implement the sparse-boundary template now. Treat further steering filtering as an optional future optimization, not the primary fix.

**Rationale:** We already have precise delivery for agent-specific behavior. The load-bearing fix is to make the always-loaded context small and unambiguous, especially in repos like `agent-crews` that contain both the deployed crew and the machinery that builds it.

**Effort:** Small.
**Risk:** Low — template/guidance change with a safe migration path for untouched skeletons.

---

## Implementation Priority

| Gap | Priority | Effort | When |
|-----|----------|--------|------|
| 1. allowed_commands | P1 | Small | Next session — enforcement principle violated |
| 2. Skill manifest | P3 | Small | When adding new skills — organizational improvement |
| 3. Sparse project context | P2 | Small | Now — prevents runtime/source confusion |

---

## Success Criteria

- [x] Gap 1: `test_allowed_commands_in_worker_agents` asserts commands ARE present (c31b48c)
- [x] Gap 1: Workers in component-enabled projects have `execute_bash.allowedCommands`
- [x] Gap 2: `shared/skills/manifest.yaml` exists; generator reads it for archetype injection
- [x] Gap 2: `test_manifest_classifies_all_skills` enforces every skill on disk is classified
- [x] Gap 3: Generated `project.md` skeleton stays sparse and explicitly distinguishes `.kiro/` runtime artifacts from `.crews/` config inputs
- [x] Gap 3: Untouched legacy `project.md` skeletons auto-upgrade on rebuild