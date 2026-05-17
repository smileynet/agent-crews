# Component Architecture — Terminology

Canonical definitions for all terms used in the component system. Use these consistently across all documentation, code, and conversations.

---

## Architecture Layers

| Term | Definition |
|---|---|
| **Component** | A named, swappable behavioral building block that defines a cross-cutting concern (e.g., how to verify, how to commit, how to narrate). Declared as a structured YAML file. |
| **Variant** | A specific implementation of a component (e.g., `signaling/standard` vs `signaling/minimal`). Selected per-project. |
| **Steering file** | A markdown file in `.kiro/steering/` with `inclusion: always` frontmatter. Auto-loaded into all agents including subagents. |
| **Skill** | A markdown file with name/description frontmatter. Loaded on-demand when the agent determines it's relevant. |
| **Crew** | A named collection of agents (orchestrator + workers) with a declared scope. Defined in `base/crews/*.yaml`. |
| **Fleet** | The inventory of all projects and their configurations. Defined in `fleet.yaml` (committed) + `fleet.local.yaml` (per-machine, gitignored). |
| **Persona** | The context separation layer (personal vs sa). Determines which steering subdirectory is synced. |

## Agent Roles

| Term | Definition |
|---|---|
| **Orchestrator** | The main agent the user talks to. Coordinates work by dispatching to workers. Has `subagent` tool. Does NOT write code directly. |
| **Worker** | A subagent dispatched by the orchestrator. Runs in fresh context. Has `read`/`write`/`shell` tools. Does the actual work. |
| **Verifier** | A special subagent (fresh context) that confirms claims are true. Sees original task + final output, NOT the worker's reasoning. |
| **Editor** | A special subagent (fresh context) that reviews prose quality. Sees document + style rules, NOT the drafting agent's reasoning. |
| **Planner** | A worker variant that breaks tasks into steps. Has `read` + `todo_list` but NOT `write`/`shell`. |

## Component System

| Term | Definition |
|---|---|
| **Target** | Which agent type a component applies to: `worker`, `orchestrator`, or `all`. |
| **Prompt fragment** | The markdown text from a component's `prompt:` field that gets injected into an agent's prompt. |
| **Allowed commands** | Shell commands a component whitelists (merged into `toolsSettings.execute_bash.allowedCommands`). |
| **Steering field** | The `steering:` section of a component YAML — written as a separate `.md` file for subagent inheritance. |
| **Subagent definition** | The `subagents:` section — generates additional agent JSON files (verifier, editor). |
| **Compositional component** | A component where the user configures elements (e.g., search sources, handoff elements, notification channels). Uses `{{placeholder}}` substitution. |
| **Preset** | A named shorthand for a common configuration (e.g., `handoff: standard` = 5 specific elements). |

## Workflow Terms

| Term | Definition |
|---|---|
| **Gate workflow** | The verification sequence: identify → run → read → verify → claim. Mandatory before any completion claim. |
| **Iron rule** | An invariant that cannot be overridden: "no fixes without investigation" (troubleshooting), "no claims without evidence" (verification). |
| **Escalation** | Moving up the recovery hierarchy when current approach fails. same-approach×2 → change strategy; 3 strategies → ask-user. |
| **Grounding** | How narration claims are confirmed: `verified` (verifier agent), `evidence` (deterministic checks), `self-report` (no verification). |
| **Handoff** | The completion report that carries context across sessions. Compositional — user picks which elements to include. |
| **Completion sequence** | The order components fire at task end: verification → git → signaling → followups → handoff → notifications → memory. |
| **Checkpoint** (git) | The solo workflow: commit frequently, push immediately, work on current branch. |

## Signaling

| Term | Definition |
|---|---|
| **DONE** | Task completed successfully. All verification passed. Evidence included. |
| **PARTIAL** | Some work completed but task not fully done. Remaining items listed. |
| **BLOCKED** | Cannot proceed. Reason stated. Needs external input or resolution. |
| **FAILED** | Attempted and could not complete after exhausting strategies. What was tried is documented. |

## Handoff Elements

| Term | Definition |
|---|---|
| **asked-delivered** | What was requested vs what was done (sanity check). |
| **state-change** | Before → After (what changed in the system). |
| **files** | Artifacts created/modified with line counts. |
| **problems** | Problems encountered + how they were resolved. |
| **wrong-turns** | What was tried and rejected, and WHY. Prevents next session repeating rejected approaches. |
| **decisions** | Choices made with rationale (not just outcomes). |
| **issues-filed** | Follow-up tasks created with IDs and destinations. |
| **next-steps** | What to do next, remaining tasks, suggested commands. |
| **context** | Anything the next session needs that isn't in the code ("context landmines"). |
| **verification** | What was verified and how (evidence summary). |

## Troubleshooting Phases

| Term | Definition |
|---|---|
| **Phase 1: Investigate** | Read error, reproduce, trace root cause. Techniques: five-whys, call-chain tracing, boundary diagnostics, binary search, diff-against-working. |
| **Phase 2: Pattern Analysis** | Find working example, compare differences. Techniques: good-vs-bad comparison, reference implementation, evidence ladder, reduction, bug category triage. |
| **Phase 3: Hypothesis** | Form single hypothesis with evidence, test one variable, predict-then-verify. |
| **Phase 4: Fix** | Failing test first, single fix only, verify all tests pass. |

## File Locations

| Term | Path | Purpose |
|---|---|---|
| **Components** | `shared/components/<name>/<variant>.yaml` | Component declarations |
| **Steering** | `shared/steering/{universal,sa,personal}/*.md` | Persona-split behavioral rules |
| **Skills** | `shared/skills/<name>/SKILL.md` | On-demand knowledge |
| **Crews** | `base/crews/*.yaml` | Base crew templates |
| **Project config** | `<project>/.crews/crew.yaml` | Source inputs that define which crews/components get deployed |
| **Project runtime** | `<project>/.kiro/` | Generated agents, prompts, skills, and local steering for one deployed project |
| **Decisions** | `.scratch/session-decisions.md` | Decision log |
| **Implementation plan** | `.scratch/implementation-plan.md` | This plan |
