# Spec: Project Context in Fleet Config

## Problem

The component system generates behavioral steering (how agents work) but has no mechanism for project-specific context (what agents are working on). Projects need a `project.md` with domain context — stack, layout, conventions, DO NOTs — that agents read at runtime.

## Design Decisions

| # | Decision | Rationale |
|---|----------|----------|
| 1 | Slack channel ID lives in `components.notifications.slack_channel` only | Single source of truth; notifications steering is `inclusion: always` so all agents see it |
| 2 | `project.md` is never synchronized from fleet.yaml after initial creation | It's an in-project file for local behavior modification without adjusting crew config |
| 3 | No `meta:` section in fleet.yaml — skeleton is a blank template with TODO markers | fleet.yaml is for config that affects generation; project context is runtime-only |
| 4 | Skeleton includes 6 sections: description, stack, layout, conventions, DO NOT, key references | Prompts users to fill in high-impact context; template is a checklist disguised as a file |
| 5 | Skeleton generated during `just build` — idempotent, no-op if file exists | No extra step needed; every project gets a project.md after generation automatically |
| 6 | Old project.md files copied for projects that had them; skeleton for new ones | Preserves existing high-quality domain context |
| 7 | Unconfigured slack_channel renders as empty string | Simple; agents won't try Slack if it's not in the channels list |
| 8 | No routing section in project.md — handoff component handles routing | project.md focuses on domain context, not agent mechanics |

## Changes

### 1. Fleet.yaml: `slack_channel` in notifications config

```yaml
projects:
  my-project:
    components:
      notifications:
        channels: [toast, slack]
        slack_channel: "C0B2K7E5ZTJ"
        slack_channel_name: "#my-channel"
```

### 2. Notifications component template

Added placeholder line to `shared/components/notifications/channels.yaml`:
```
Active channels: {{notifications.channels}}
Slack channel: {{notifications.slack_channel_name}} (ID: {{notifications.slack_channel}})
```

### 3. Skeleton generator in `generate.py`

`generate_project_md_skeleton(kiro_dir)` — creates `steering/project.md` with 6 TODO sections if file doesn't exist. Called from `generate_all()` after steering sync.

### 4. Bug fix: `load_all_components` placeholder resolution

Fixed pre-existing bug where `load_all_components` built a flat dict with dotted keys but `substitute_placeholders` walks nested dicts. Changed to pass the component config as a nested dict.

## What `project.md` is for

It's the in-project space to modify agent behavior without adjusting crew config. Agents discover it via the `file://.kiro/steering/**/*.md` resource glob. It contains:

1. **What the project is** — domain context
2. **Stack** — languages, frameworks, dependencies
3. **Layout** — key directories
4. **Conventions** — project-specific patterns
5. **DO NOT** — safety constraints
6. **Key references** — important files to know about

## What `project.md` is NOT for

- Agent routing (handled by handoff component + crew-sheet)
- Notification config (handled by notifications component)
- Verification commands (handled by verification component)
- Git workflow (handled by git component)
- Any behavioral rule that applies across projects (belongs in components)
