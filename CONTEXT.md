# Agent Crews

A system for creating, deploying, and maintaining specialized AI agent teams for coding projects.

## Language

**Crew**:
A group of agents specialized for a domain of work (e.g., bug-fix, research, infrastructure).
_Avoid_: team, squad (unless themed)

**Agent**:
A single AI persona with a defined role, tools, and prompt. The atomic unit of work.
_Avoid_: bot, assistant

**Archetype**:
The behavioral tier an agent belongs to: dispatcher, orchestrator, or worker. Determines tool access and delegation rights.
_Avoid_: type, role, level

**Dispatcher**:
The top-level agent (depth 0) that routes user requests to the appropriate crew lead. Has read + subagent + todo_list only.
_Avoid_: router, coordinator

**Orchestrator**:
A crew lead (depth 1) that plans work and delegates to workers. Cannot target other orchestrators.
_Avoid_: lead (acceptable as shorthand), manager

**Worker**:
An agent (depth 2) that executes tasks and produces artifacts. Cannot delegate via subagent.
_Avoid_: executor, doer

**Component**:
A reusable behavioral concern (e.g., notifications, signaling, verification) that generates steering files and optional subagents at build time.
_Avoid_: plugin, module, extension

**Fleet**:
The collection of all projects managed by agent-crews. Configured in fleet.yaml and fleet.local.yaml.
_Avoid_: registry, catalog

**Steering**:
Markdown files that shape agent behavior via always-loaded context. Organized by archetype tier (universal, orchestrator, worker).
_Avoid_: instructions, system prompt, config

**Skill**:
A markdown file with YAML frontmatter loaded on-demand when relevant. Delivers protocols and reference material without always consuming context budget.
_Avoid_: guide, reference

**Theme**:
A cosmetic overlay that renames agents without changing behavior. Applied at build time.
_Avoid_: skin, flavor

**Build**:
The generation step that transforms source YAML into deployable agent JSON + steering. Running `just build` is mandatory after any source change.
_Avoid_: generate (acceptable as verb), compile

**_lib**:
Internal Python modules that implement generate.py's logic. Not a deployable package — just code organization for maintainability.
_Avoid_: package, library (it's not distributed)

**Grill Session**:
A structured design interrogation that challenges a plan until shared understanding is reached, updating domain docs inline.
_Avoid_: design review, brainstorm

## Relationships

- A **Fleet** contains many projects, each with one or more **Crews**
- A **Crew** contains exactly one **Orchestrator** and one or more **Workers**
- A **Dispatcher** routes to **Orchestrators** across all crews in a project
- A **Component** produces **Steering** files and optional **Agents** (subagents)
- A **Theme** maps generic agent names to themed names within a **Crew**
- A **Skill** is attached to agents via resources and loaded on-demand by the platform
- The meta domain has three crews: **Crew-Builder** (create/modify), **Crew-Maintenance** (diagnose/tune/release), **Crew-Tooling** (fix scripts/generator)

## Flagged Ambiguities

- "lead" is used interchangeably with "orchestrator" — resolved: orchestrator is the archetype, lead is the informal shorthand (acceptable in conversation, not in code/config)
- "generate" vs "build" — resolved: build is the user-facing command (`just build`), generate is the internal verb (what generate.py does)
- "vocabulary" was used for routing intent keywords — resolved: deprecated. Routing data is now injected directly into prompts as routing tables. Domain glossary lives in CONTEXT.md.
- "ops-lead" / "build-lead" / "bugfix-lead" — resolved: renamed to crew-builder-lead, crew-maintenance-lead, crew-tooling-lead. Meta crews follow the same one-lead-per-file structure as base crews.
