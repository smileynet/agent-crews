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

**Project Config**:
The source inputs under a project, primarily `.crews/crew.yaml`, that define what crew gets deployed.
_Avoid_: runtime, deployed state

**Project Runtime**:
The generated `.kiro/` artifacts that an instantiated crew actually runs with in a project.
_Avoid_: source config, template

**AGENTS.md**:
An owner-managed, portable instruction document outside agent-crews' runtime-context guarantees; agent-crews may expose it, but does not treat it as the canonical source of injected agent context.
_Avoid_: canonical runtime context, required deployment surface


 **Legacy agent-crews project**:
 A repo that already has agent-crews-managed deployment artifacts or source config, so migrations must preserve existing `.kiro/` and `.crews/` behavior.
 _Avoid_: generic brownfield repo

 **External brownfield repo**:
 An existing repo being onboarded to agent-crews for the first time, with no prior agent-crews deployment to preserve.
 _Avoid_: legacy agent-crews project


**_lib**:
Internal Python modules that implement generate.py's logic. Not a deployable package — just code organization for maintainability.
_Avoid_: package, library (it's not distributed)

**Subagent-only worker**:
A worker meant to be reached only through orchestrator delegation, so it can rely on task handoff context instead of being independently user-facing.
_Avoid_: direct entrypoint, user-facing worker

**Directly invocable worker**:
A worker intentionally exposed as a safe user entrypoint in deployed docs or UI, and therefore eligible for its own targeted project facts.
_Avoid_: internal-only worker, arbitrary worker

 **Behavior lever**:
 A small, reusable, user-facing configuration control for a cross-project agent behavior such as verification, writing, memory, or git workflow.
 _Avoid_: implementation detail, one-off tweak
 **Config simplicity**:
 Public config should use the simplest literal mechanism that matches its meaning, with no hidden defaults or special-case semantics.
 _Avoid_: snowflake config rules, implicit inclusion
 **Behavior mapping**:
 The generator's responsibility to map public behavior levers onto the relevant agents and crews without exposing runtime-delivery mechanics in project config.
 _Avoid_: per-agent behavior wiring, user-authored injection rules
**Shared workspace**:
A filesystem area where agents leave artifacts for other agents or later sessions to read on demand instead of relying on conversational memory.
_Avoid_: chat history, implicit context

**Handoff artifact**:
A concise, point-in-time file that records the current state, constraints, decisions, and next steps needed for another agent or session to continue work safely.
_Avoid_: full transcript dump, durable knowledge base

**Workspace contract**:
The agreed directory locations, artifact names, lifecycle rules, and handoff expectations that let agents share information through files instead of conversational memory.
_Avoid_: ad hoc scratch conventions, implicit file discovery

**Scope-aligned skill**:
A skill written for one behavioral scope—project, crew, or agent—so its instructions match the level of shared policy, workspace, and artifact expectations it owns.
_Avoid_: mixed-scope skill, topology drift

**Durable workspace**:
A persistent shared-artifact layer for curated knowledge that remains useful beyond the current handoff, such as decisions, stable references, and promoted summaries.
_Avoid_: transient handoff note, ephemeral scratch

**Currentness marker**:
A small metadata field such as timestamp or base commit that helps agents judge whether a shared artifact may be stale before relying on it.
_Avoid_: hidden freshness assumption

**Handoff key**:
A human-readable workstream slug used to determine which newer handoff supersedes an older one.
_Avoid_: implicit topic inference, crew-only identity

**Base commit**:
The git commit at HEAD when a shared artifact was created, used as a lightweight anchor for reasoning about currentness.
_Avoid_: fake validation marker, source-of-truth commit







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
