# Fleet Configuration

fleet.yaml is where you register projects and configure how agents behave. It's the single source of truth for what gets deployed where.

## Why fleet.yaml exists

Without it, you'd configure each project's agents individually. Set defaults once, override per-project where needed.

## Structure

```yaml
defaults:          # baseline for all projects
  crews: [general]
  components: ...

projects:          # per-project overrides
  my-project:
    crews: [general, research]
    components:
      verification:
        checks:
          build: "npm run build"
```

Projects inherit everything from `defaults` and only override what's different.

## Key decisions

### Which crews?

General is always included. Add specialized crews only when the work benefits from domain-specific agents. More crews = more agents to manage. Start minimal.

### Build/test/lint commands

These are critical — agents use them to verify their own work. If you don't set them, agents can't confirm their changes are correct.

```yaml
components:
  verification:
    checks:
      build: "cargo check"    # fast compilation check
      test: "cargo test"      # run test suite
      lint: "cargo clippy"    # static analysis
```

Set to `null` if your project doesn't have one of these.

### Git workflow

- `checkpoint` — commit frequently, push immediately (solo/personal projects)
- `pr-based` — branch, commit, open PR (team projects)

### Notifications

Where agents tell you they're done:

```yaml
components:
  notifications:
    channels: [toast]           # OS notification
    # channels: [toast, slack]  # + Slack webhook
    policy: completions         # only on task completion
```

### Themes

Cosmetic only — rename agents to fit your project's vibe. See [Themed Crews Guide](themed-crews-guide.md).

## Files

- `fleet.example.yaml` — committed reference showing the format and all options
- `fleet.yaml` — your actual config (gitignored, copy from example)
- `fleet.local.yaml` — deployment paths mapping project names to filesystem locations (gitignored)

## fleet.local.yaml

Maps project names to where they live on your machine:

```yaml
deployments:
  my-project: /home/user/code/my-project
  other-project: /home/user/code/other-project
```

Used by `just link <project>` to know where to deploy.
