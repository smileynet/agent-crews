# Fleet Configuration

## Project Registry

`fleet.local.yaml` is the project registry — a name→path mapping of all projects managed by agent-crews. It's gitignored (machine-specific paths).

```yaml
# fleet.local.yaml
projects:
  agent-crews: ~/code/agent-crews
  pidev-crafter: ~/code/pidev-crafter
  craft-mmo: ~/code/craft-mmo
```

## Auto-discovery

```bash
just scan ~/code    # finds all dirs with .crews/crew.yaml, updates fleet.local.yaml
```

## Project Configuration

Each project's config lives in `.crews/crew.yaml` — self-contained, no inheritance:

```yaml
# ~/code/my-project/.crews/crew.yaml
persona: personal
crews: [general, research]
behavior:
  verification:
    variant: gate
    checks:
      build: "cargo check"
      test: "cargo test"
      lint: "cargo clippy"
  git:
    variant: checkpoint
workspace:
  ephemeral: .scratch
  durable: .memory
```

### Key fields

| Field | Purpose |
|-------|--------|
| `persona` | personal or team identifier |
| `crews` | Which base crews to include (literal list; required, non-empty) |
| `behavior` | Behavioral configuration (verification, git, notifications, etc.) |
| `workspace` | Optional `{ephemeral, durable}` root paths; both required when present (defaults: `.scratch`, `.memory`). See [docs/workspace.md](workspace.md) |

### Build/test/lint commands

Critical — agents use these to verify their own work:

```yaml
behavior:
  verification:
    checks:
      build: "npm run build"   # fast compilation check
      test: "npm test"         # run test suite
      lint: "npx eslint ."    # static analysis
```

Set to `null` if your project doesn't have one.

### Git workflow

- `checkpoint` — commit frequently, push immediately (solo/personal)
- `pr-based` — branch, commit, open PR (team)

## Commands

| Task | Command |
|------|---------|
| Build one project | `just build <name>` |
| Build all | `just build --all` |
| Build current dir | `just build .` |
| Fleet status | `just status` |
| Scan for projects | `just scan ~/code` |
