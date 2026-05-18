# Spec: Project Context in Fleet Config

## Problem

The component system generates behavioral steering (how agents work) and targeted prompts/skills, but projects still need a small always-loaded context file describing what agents are working on. `project.md` carries that runtime context and must stay sparse so it does not compete with more precise instructions.

## Design Decisions

| # | Decision | Rationale |
|---|----------|----------|
| 1 | Slack channel ID lives in `components.notifications.slack_channel` only | Single source of truth; notification behavior belongs in component config, not project context |
| 2 | `project.md` is never synchronized from fleet.yaml after initial creation | It's an in-project file for local runtime context without adjusting crew config |
| 3 | No `meta:` section in fleet.yaml — skeleton is a blank template with TODO markers | fleet config affects generation; project context is runtime-only |
| 4 | Skeleton includes a short "scope of this file" section plus runtime-boundary guidance before the project facts | Makes sparse context and source/runtime separation explicit |
| 5 | Skeleton generated during `just build` — create if missing, auto-upgrade untouched legacy skeletons | New and example projects converge without overwriting customized context |
| 6 | Old project.md files copied for projects that had them; skeleton for new ones | Preserves existing high-quality domain context |
| 7 | Unconfigured slack_channel renders as empty string | Simple; agents won't try Slack if it's not in the channels list |
| 8 | No routing section in project.md — handoff component handles routing | project.md focuses on project/runtime context, not agent mechanics |

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

`generate_project_md_skeleton(kiro_dir)` creates `steering/project.md` with sparse-context guidance, a `.kiro/` vs `.crews/` runtime boundary, and the core project-facts sections. It writes the file if missing and upgrades the untouched legacy skeleton in place.

### 4. Bug fix: `load_all_components` placeholder resolution

Fixed pre-existing bug where `load_all_components` built a flat dict with dotted keys but `substitute_placeholders` walks nested dicts. Changed to pass the component config as a nested dict.

## What `project.md` is for

It's the always-loaded runtime context for a deployed project. It should contain:

1. **Only facts most deployed agents need on most turns**
2. **A clear runtime boundary** — what `.kiro/` artifacts are deployed here versus which source/config files define them
3. **What the project is** — domain context
4. **Stack** — languages, frameworks, dependencies
5. **Layout** — key directories
6. **Conventions** — project-specific patterns
7. **DO NOT** — safety constraints
8. **Key references** — important files to know about

## What `project.md` is NOT for

- Agent routing (handled by handoff component + crew-sheet)
- Notification config (handled by notifications component)
- Verification commands (handled by verification component)
- Git workflow (handled by git component)
- Any behavioral rule that applies across projects (belongs in components, skills, or prompts)
- A design memo or implementation guide for the crew generator itself