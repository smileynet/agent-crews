# Troubleshooting

When your agents aren't working as expected.

## Common issues

### Agents aren't loading

**Symptoms:** kiro-cli doesn't recognize agent names, `/agent <name>` fails.

**Check:**
- Is `.kiro/agents/` present in your project? (`ls .kiro/agents/`)
- Did you run `just build` + `just link` after fleet.yaml changes?
- Is the symlink intact? (`file .kiro` — should be a directory or valid symlink)

### Agent does the wrong thing

**Symptoms:** dispatcher routes to wrong agent, worker ignores its scope.

**Consider:**
- Is the input ambiguous? Try being more specific about what you need.
- Run `@crew-sheet` to see which agent handles what.
- Check the crew YAML — does the agent's scope/handles list cover this task?
- Analyze the session: `uv run analyze-session.py <id> --compliance`

### Agent skips verification

**Symptoms:** agent reports done without running build/test/lint.

**Check:**
- Are build/test/lint commands set in fleet.yaml? (null = nothing to run)
- Is the verification component configured? Check `.kiro/steering/worker/verification.md`
- Regenerate: `just build` + `just link`

### Agent won't commit or push

**Symptoms:** work is done but not committed.

**Check:**
- Git component variant — `checkpoint` auto-commits, `manual` doesn't
- Is there a git remote? (agent won't push if no remote exists)
- Check `.kiro/steering/worker/git.md` for the active rules

### Steering files not loading

**Symptoms:** agent ignores behavioral rules that should apply.

**Check:**
- Do steering files exist? `ls .kiro/steering/worker/` and `ls .kiro/steering/universal/`
- Check the agent JSON — does `resources` include the steering globs?
- Regenerate: components may not have been generated for this project

### Theme names not applying

**Symptoms:** agents still use generic names after setting a theme.

**Check:**
- Is `theme:` set in fleet.yaml for this project?
- Did you regenerate? (`just build`)
- Check `.kiro/agents/` — filenames should reflect themed names

## Getting help

- Use `@crew-sheet` for a quick reference of what's deployed
- Use `/agent crew-doctor` in this repo to diagnose issues interactively
- Analyze sessions: `uv run analyze-session.py --project <path>`
- Run evals to check behavioral compliance: `just eval`

## Nuclear option

If everything is broken and you want a fresh start:

```bash
# In your project
rm -rf .kiro/

# In agent-crews
just build
just link <project>
```

This regenerates and redeploys from scratch.
