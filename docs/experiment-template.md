# Experiment Template — Agent Behavior Validation

Use this template when testing new agent-crews features or platform capabilities.

## When to Run Experiments

- Testing platform capabilities (e.g., can subagents nest?)
- Validating information flow between agents
- Testing new crew patterns before deploying to real projects
- Verifying depth guards, signaling, or handoff mechanisms

## Setup

### Isolation
Create experiments in a separate `~/code/<experiment-name>/` folder:
- Keeps agent-crews repo clean
- No interference with `just build` or .crews/crew.yaml
- Easy teardown (delete the folder)
- Can run kiro-cli independently

### Minimal Structure
```
~/code/<experiment-name>/
  .kiro/
    agents/       ← Hand-written JSON (not generated)
    steering/
      project.md  ← Minimal context
  scratch/        ← Output landing zone
  README.md       ← What this tests + how to run
  .gitignore      ← scratch/
```

### Agent Design Principles
- Minimal prompts (test one thing, not everything)
- Clear tool boundaries (who has what)
- Explicit output locations (so success is checkable)
- Structured reporting (DONE/BLOCKED/FAILED)

## Execution

### Headless (automated)
```bash
cd ~/code/<experiment-name>
kiro-cli chat --no-interactive --trust-all-tools --agent <entry-agent> "<task>"
echo "Exit: $?"
```

### Key Flags
| Flag | Purpose |
|------|---------|
| `--no-interactive` | No user input needed |
| `--trust-all-tools` / `-a` | Auto-approve tool calls |
| `--agent <name>` | Start with specific agent |
| Positional arg | Initial task/message |

### Interactive (for debugging)
```bash
cd ~/code/<experiment-name>
kiro-cli chat --agent <entry-agent>
```
Then type the task manually. Use `ctrl+g` to monitor subagent sessions.

## Validation Checklist

After execution, verify:

1. **Exit code** — 0 = success
2. **Output files exist** — Check expected paths in scratch/
3. **Content quality** — Output references actual data (not hallucinated)
4. **Timing** — Sequential steps happened in order
5. **No errors** — No "tool not available" or permission errors
6. **Session logs** — `kiro-cli chat --list-sessions` shows the run

## Documenting Results

Write an EXPERIMENT.md in the experiment folder with:
- Hypothesis
- Architecture diagram
- Command used
- Success criteria table (✅/❌)
- Agent invocation evidence
- Implications for agent-crews
- How to reproduce

## Session Log Access

- List sessions: `kiro-cli chat --list-sessions` (in the experiment dir)
- Session data: `C:\Users\<user>\AppData\Local\Kiro-Cli\data.sqlite3`
- analyze-session.py: `uv run analyze-session.py --list` (from agent-crews)

## Common Experiment Patterns

### Depth Test
Test whether subagents can spawn subagents.
- 3 agents: coordinator → manager → worker
- Task: create a file through the full chain
- Success: file exists with correct content

### Information Flow Test
Test research-then-build handoff.
- 5 agents: coordinator → researcher → analyst + builder → implementer
- Task: research something, then produce output based on findings
- Success: output file references actual research findings

### Signal Propagation Test
Test BLOCKED/FAILED bubbling up.
- Give worker an impossible task
- Verify crew lead retries once, then reports BLOCKED to dispatcher
- Success: dispatcher reports the blockage to user (not silent failure)

### Parallel Dispatch Test
Test multiple workers at same depth.
- Orchestrator spawns 2+ workers simultaneously
- Success: both complete, results aggregated

## Prior Experiments

| Date | Name | Location | Result |
|------|------|----------|--------|
| 2026-05-15 | 3-Level Depth Test | ~/code/depth-test/ | ✅ SUCCESS — confirmed depth-2 nesting works |
