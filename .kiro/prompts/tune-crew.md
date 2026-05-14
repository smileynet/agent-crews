---
description: "Analyze recent sessions, identify crew issues, and apply fixes — the full tuning loop"
---

# Tune Crew

Run the observe → diagnose → fix → validate loop for a deployed crew.

## Steps

1. **Analyze recent sessions** (2-3 most recent for the target project)
   ```bash
   uv run analyze-session.py --project <name>
   uv run analyze-session.py <session-id> --stats
   ```
   Look for:
   - Agent utilization (are orchestrators being used as general-purpose?)
   - Cross-crew delegation (orchestrators spawning wrong crew's agents)
   - Tool usage patterns (shell-heavy? missing tools?)
   - Cheatsheet invocations (routing confusion signal)
   - Secrets pasted in prompts

2. **Check structural invariants**
   ```bash
   python3 -c "..." # (see crew-structural-rules skill)
   ```

3. **Check steering budget**
   ```bash
   wc -l base/steering/*.md | sort -rn
   ```
   Total should be < 250 lines.

4. **Identify fixes** — classify each issue:
   - Scope violation → add redirect guidance to orchestrator prompt
   - Tool misuse → fix archetype tool list in crew YAML
   - Context waste → move content from steering to skill
   - Missing routing → update crew-routing.md steering
   - Behavioral gap → add/update steering file

5. **Apply fixes** — edit crew YAML, steering, or skills

6. **Validate**
   ```bash
   just build
   just smoke-test <target-path>  # behavioral signal check
   ```

7. **Deploy**
   ```bash
   just deploy <project> <target-path>
   ```

## What to look for in sessions

| Signal | Indicates | Fix |
|--------|-----------|-----|
| 18/20 sessions use `default` | Users don't know which agent to pick | Improve routing steering |
| Orchestrator spawns wrong crew | Missing availableAgents scoping | Fix crew YAML + regenerate |
| Cheatsheet invoked 3x | Routing confusion | Add crew-routing.md steering |
| Secret pasted in prompt | No secret handling | Add to session-completion steering |
| Worker spawns subagent | Tool list leak | Remove subagent from global tools |
| Orchestrator runs shell | Tool list too broad | Restrict orchestrator archetype tools |
