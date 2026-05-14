# Decisions Log — Scriptorium & Architecture Redesign Session

**Date:** 2026-05-10
**Session:** Documentation crew design → persona separation → fleet management → component architecture

---

## Architecture Decisions

### D-001: Documentation taxonomy uses audience × content-type (two-dimensional)
- **Context:** Pure Diátaxis (4 content types) doesn't account for different audiences
- **Decision:** Primary axis is audience (agents/users/maintainers), secondary is content mode (learning/doing/looking-up/understanding)
- **Alternatives rejected:** Pure Diátaxis (single-audience assumption), audience-only (loses content-type value)
- **Status:** Accepted, implemented in diataxis-classification skill

### D-002: All crew definitions live in agent-crews repo (single source of truth)
- **Context:** ferris-tracker-agentic diverged by accident, creating two sources
- **Decision:** agent-crews owns all crew definitions. No exceptions.
- **Alternatives rejected:** External source repos, split ownership
- **Status:** Accepted, ferris-tracker-agentic crews moved back

### D-003: Symlink is the default deploy method
- **Context:** Need to get crews from agent-crews to target projects
- **Decision:** Target project's `.kiro/` is a symlink to `agent-crews/projects/<name>/.kiro/`. Changes are immediately live.
- **Alternatives rejected:** Copy (requires explicit deploy step, creates drift)
- **Status:** Accepted, ferris-tracker using symlink

### D-004: fleet.yaml (shared) + fleet.local.yaml (per-machine, gitignored)
- **Context:** Need to track what's deployed where across multiple machines
- **Decision:** fleet.yaml declares all projects and their properties (committed). fleet.local.yaml declares what's deployed on THIS machine (gitignored). Flat map: project → target path.
- **Alternatives rejected:** Single file with deployment state (can't share across machines), no inventory (can't tell what's deployed)
- **Status:** Accepted, not yet implemented

### D-005: Persona separation (sa vs personal)
- **Context:** Organization-specific assumptions (internal auth, Slack, internal search tools) were polluting personal projects
- **Decision:** Steering split into universal/ + sa/ + personal/. Generator reads persona from fleet.yaml. Projects declare their persona.
- **Alternatives rejected:** Single steering set with conditionals, per-project steering only
- **Status:** Accepted, implemented

### D-006: All projects on this machine are personal persona
- **Context:** The 5 "reference projects" (taskflow-ui, pixel-dungeon, etc.) don't exist on disk — they're reference configs
- **Decision:** Set all to personal. SA projects are reference-only (maintained for consistency, not deployed locally).
- **Status:** Accepted, implemented

### D-007: Base crews are persona-agnostic capability templates
- **Context:** SA assumptions were baked into crew YAML prompts
- **Decision:** Remove all persona-specific content from base crews (internal tools, Slack, organization-specific MCP servers). Persona-specific behavior comes from steering, not crew prompts.
- **Status:** Accepted, implemented

### D-008: Simplified commands aligned to JTBD
- **Context:** Too many commands (generate, deploy, ship, ship-validated, sync-steering)
- **Decision:** `just build` (generate), `just link <project>` (create symlink), `just status` (inventory), `just check` (validate), `just bootstrap` (setup all from fleet.local.yaml)
- **Status:** Accepted, not yet implemented

---

## Component Architecture Decisions

### D-009: Crews are composed from swappable components
- **Context:** Cross-cutting concerns (signaling, sanity gate, search, etc.) are copy-pasted across every crew
- **Decision:** Extract into named components. Each project declares which implementation of each concern it uses. Generator assembles them into agent prompts.
- **Alternatives rejected:** Monolithic crews (current, causes drift), inheritance (complex merge logic)
- **Status:** Accepted, design in progress

### D-010: Components are explicit and swappable, nothing is "universal"
- **Context:** We assumed some things (sanity gate, signaling) were universal
- **Decision:** Every behavioral choice is a named slot with a named implementation. Even if there's only one option today, it's explicit so it can be documented and swapped later.
- **Status:** Accepted

### D-011: Search sources are additive layers, each with a dedicated agent
- **Context:** Different projects need different search capabilities (local, cached docs, MCP servers, web, internal)
- **Decision:** Projects declare their search sources as an ordered list. Each source type maps to a dedicated search agent. Sources are additive (local + cached + web, not one-of).
- **Status:** Accepted, template designed

### D-012: Sanity gate uses assumption register (grill-me pattern)
- **Context:** Current sanity gate is a silent checklist agents claim to check
- **Decision:** Generate questions upfront, track which are answered vs assumed. Surface assumptions in DONE signal. Unconfirmed decisions are explicitly marked as assumptions.
- **Status:** Accepted

### D-013: Memory has four tiers (working/session/episodic/semantic)
- **Context:** Current memory is ad-hoc (scratch/ files, no persistence model)
- **Decision:** Four tiers with different lifetimes, enforcement mechanisms, and aging rules. ADRs, research artifacts, steering files are all forms of semantic memory.
- **Status:** Accepted, design in progress

### D-014: Memory includes discovery mechanism for scattered knowledge
- **Context:** Real projects have knowledge in commits, comments, TODOs, threads — not just canonical locations
- **Decision:** Memory component includes scan patterns for finding scattered knowledge, capture rules for proposing where it should live, and a schedule for when to run discovery.
- **Status:** Accepted

### D-015: Two-tier crew model (themed base crews vs fully custom)
- **Context:** Some projects need custom workflows, most just need themed versions of base capabilities
- **Decision:** "Themed" tier uses base crews with cosmetic overlay + project-specific additions. "Custom" tier has fully independent crews with structural linting for drift detection.
- **Status:** Accepted, not yet implemented

---

## Signaling Component Decisions

### D-016: Four statuses (DONE/PARTIAL/BLOCKED/FAILED) + structured fields
- **Context:** Current signaling varies across crews and lacks structured data
- **Decision:** Standard signal has status enum + Task/Result/Evidence/Remaining/Assumptions fields
- **Segmentation:** standard (most projects), minimal (hobby), tracked (with issue IDs)
- **Status:** Accepted

---

## Component Architecture Decisions (Deep Dive)

### D-017: Signaling uses 4 statuses + structured fields including Assumptions
- **Decision:** DONE/PARTIAL/BLOCKED/FAILED + Task/Result/Evidence/Remaining/Assumptions fields
- **Segmentation:** standard (most), minimal (hobby), tracked (with issue IDs)
- **Status:** Accepted

### D-018: Sanity gate uses assumption register, not silent checklist
- **Decision:** Generate questions upfront, track answered vs assumed. Surface assumptions in DONE signal. Unconfirmed decisions explicitly marked. Rubber-stamp guard (pause after 3 consecutive agent-suggested decisions).
- **Informed by:** grill-me skill pattern (matt-skills)
- **Status:** Accepted

### D-019: Search sources are additive layers with dedicated agents
- **Decision:** Projects declare search sources as an ordered list. Each source type can map to a dedicated search agent. Sources are additive (local + cached + web), not one-of.
- **Status:** Accepted

### D-020: Search uses declarative search.yaml with priority-based resolution
- **Decision:** Each project declares sources, priority order, and conflict resolution rules in a search config. Generator reads this and wires tools/instructions into search agents.
- **Status:** Accepted

### D-021: Memory has 4 tiers (working/session/episodic/semantic)
- **Decision:** Working (.scratch/maps/), Session (.scratch/session/), Episodic (.kiro/memory/lessons.md), Semantic (ADRs, steering, research). Each tier has different lifetime, enforcement, and aging rules.
- **Status:** Accepted

### D-022: Knowledge artifacts (ADRs, research, steering) are forms of semantic memory
- **Decision:** The distinction between "memory" and "documentation" dissolves at the semantic tier. ADRs, steering files, and AGENTS.md are all persistent memory with different write triggers and enforcement mechanisms.
- **Status:** Accepted

### D-023: Memory includes discovery mechanism for scattered knowledge
- **Decision:** Memory component includes scan patterns for finding knowledge in non-standard places (commits, comments, TODOs, threads), capture rules for proposing where it should live, and a schedule for when to run discovery.
- **Status:** Accepted

### D-024: Use .scratch/ not scratch/ for agent working directories
- **Decision:** Aligns with dotfile conventions (.docs/, .kiro/, .claude/). All references updated.
- **Status:** Accepted, implemented

### D-025: Notifications are additive channels with toast as personal default
- **Decision:** Channels are additive (toast + discord, not one-of). Toast (OS-native) is the best default for personal projects — zero setup, works when in another app. Policy determines when to fire (completions/verbose/silent).
- **Status:** Accepted

### D-026: Task tracking has soft planning + hard tracking
- **Decision:** Two parts: soft (thinking modes, facilitation stance, decision capture, scope control) and hard (todo-list/beads/github-issues for persistence). Soft produces inputs that hard consumes.
- **Status:** Accepted

### D-027: Soft planning adapts patterns from Line Cook, doesn't adopt wholesale
- **Decision:** Extract patterns (separate creative/execution, coverage gates, decision capture, scope anchoring, rubber-stamp guard, simulation-as-validation) as capabilities. Don't prescribe the mise cycle sequence. Agent has modes available in any order.
- **Informed by:** Line Cook mise cycle, game-spice simulation guide
- **Status:** Accepted

### D-028: Decisions use progressive formalization (capture → log → ADR)
- **Decision:** Always capture (assumption register). Persist significant ones (decision log). Promote to ADR when signals present (constrains future work, required research, affects multiple components, explained twice). Never block work for missing formality.
- **Status:** Accepted

### D-029: Spec process available but never mandatory
- **Decision:** Agent can suggest/draft specs when complexity warrants. Format is lightweight (problem + scenarios + requirements + assumptions + success criteria). Never gates work. Nudge, don't enforce.
- **Informed by:** spec-kit (GitHub Spec Kit), progressive PRD research
- **Status:** Accepted

### D-030: Handoff routing auto-generated from crew scope declarations
- **Decision:** Generator reads each crew's declared scope (handles + refuses) and produces routing table + refusal rules. No subjective "mode" or "threshold" — boundaries are structural, defined at crew design time.
- **Alternatives rejected:** soft/strict mode (subjective), threshold (unreliable agent judgment)
- **Status:** Accepted

### D-031: Narration is a component with tiered grounding (verified default)
- **Decision:** Narration fires at plan/transitions/completion. Grounding determines how claims are confirmed: `verified` (default, independent verifier agent in fresh context sees original task + final output, not worker's reasoning), `evidence` (deterministic checks only — build/test/lint), `self-report` (no verification, for research/planning). Verified is default because narration without proof is the hallucinated success anti-pattern.
- **Rules:** verified = artifacts that could be wrong; evidence = deterministic checks suffice; self-report = no verifiable side-effects.
- **Warden split:** Current warden conflates verification (→ verifier role, narration component), editing (→ writing component), and assumption challenging (→ sanity gate component). Warden becomes the verifier with narrower mandate.
- **Informed by:** Anthropic Generator-Verifier pattern (Apr 2026), Augment CIV pattern / VeriMAP (EACL 2026), Claude Forge GAN-style adversarial (Mar 2026), Tian Pan "Hallucinated Success" (Apr 2026), Smashing Magazine "Transparency Moments" (Apr 2026)
- **Status:** Accepted

### D-032: Troubleshooting uses systematic four-phase methodology with escalation policy
- **Decision:** Four-phase debugging methodology (Investigate → Pattern Analysis → Hypothesis → Fix) with iron rule: no fixes without root cause investigation first. Techniques per phase are the content of the methodology, not config knobs. Escalation: same approach fails 2x → change strategy; 3 strategies fail → question architecture or ask user.
- **Phase 1 techniques:** five-whys, call-chain tracing, boundary diagnostics, binary search (git bisect), diff-against-working
- **Phase 2 techniques:** good-vs-bad comparison, reference implementation comparison, evidence ladder (cheap→expensive), reduction, bug category triage (logic/state/environment)
- **Phase 3 techniques:** single hypothesis with evidence, minimal test (one variable), predict-then-verify
- **Phase 4 techniques:** failing test first, single fix only, verify all tests pass
- **Red flags (return to Phase 1):** "try changing this, see if it works", proposing fix before reading error, "try fix again" after 2+ failures, "I don't fully understand but this should work"
- **Informed by:** Superpowers "Systematic Debugging" (obra, 2026), SurePrompts "Agent Debugging Prompts" (Apr 2026), Microsoft AgentRx nine-category failure taxonomy (Mar 2026), Jeff Bailey "Fundamentals of Software Debugging" (Dec 2025), KindaTechnical "Error Recovery and Retries in Agentic Workflows" (Apr 2026), Tian Pan "Retry Amplification" (Apr 2026)
- **Status:** Accepted

### D-033: Writing component has style skill, independent editor, and structured theme specification
- **Decision:** Writing component declares: style reference (default: standard writing-style skill), independent editor agent (fresh context, fires on triggers: new-document, significant-revision >5 lines, user-facing artifacts), and optional theme specification. Theme is a structured spec requiring: name, domain (metaphor world), vocabulary (use/avoid lists), tone (one sentence), 3+ examples showing voice in action, 2+ anti-examples showing what to avoid. Theme applies only to narration/notifications/handoff/welcome messages — committed artifacts always use standard style. Without examples, voice drifts within 15 messages.
- **Editor properties:** Independent agent in fresh context (same principle as verifier). Sees document + style rules, NOT drafting agent's reasoning. Returns specific edits or "clean". Max 1 pass.
- **Informed by:** Gradient Works "How to Make Agents Write Good" actor-critic model (May 2026), RoboRhythms Character AI definition template research (Apr 2026) — six sections needed for voice to hold, sample dialogue most critical, Salesforce agent communication guide (May 2026), D-031 warden split (editor role)
- **Status:** Accepted

### D-034: Verification uses universal gate workflow with task-type-specific checks
- **Decision:** Gate workflow (identify → run → read → verify → claim) is mandatory for ALL task types. What counts as evidence varies by task type. 14 task types identified: code (build/test/lint/scope), infrastructure (plan-review before apply), config (build/smoke), writing (editor/style-check/links/accuracy), research (sources/traceability/completeness), product_design (walkthrough/completeness/coherence/jtbd-alignment), architecture (assumptions/alternatives/consequences), ui_ux (spec-compliance/accessibility/responsive/states), deployment (health/smoke/logs), data_migration (integrity/before-after/rollback), testing (coverage/edge-cases/red-green), refactoring (behavior-preservation), planning (completeness/actionability/dependencies), security (threat-model/owasp/secrets/permissions). Scope check (git diff limited to task) always applies.
- **Iron rule:** No completion claims without fresh verification evidence. "Should pass" / "looks fine" / "agent reported success" are all violations.
- **Product design verification:** walkthrough test (narrate step-by-step without "magic happens"), completeness (all paths have beginning/middle/end, error/empty/first-time states), JTBD alignment (flows map to stated jobs), coherence (consistent terminology/mental model), testability (observable criteria per step).
- **Informed by:** Superpowers "Evidence First" / verification-before-completion skill (obra, 2026), Martin Fowler on agent verification (Apr 2026), OpenAI "Harness Engineering" (Apr 2026), Microsoft Azure infrastructure validation (May 2026), Terraform production patterns (Apr 2026), Jackson Hedden "Design Validation" (Apr 2026), existing verification-checklist steering (agent-crews)
- **Status:** Accepted

### D-035: Git uses workflow presets (checkpoint/pr-based/manual) + optional worktrees
- **Decision:** Three workflow presets cover all cases: `checkpoint` (solo — commit frequently, push immediately, direct to branch), `pr-based` (team — feature branch, PR to merge, never touch main), `manual` (user controls — commit locally, never push). Worktrees are orthogonal (isolation for parallel agent work, any workflow). Commit timing rules are always true regardless of workflow: before risky ops, after working states, only after verification passes. Messages must be meaningful. Stage explicit files. Never force-push without permission.
- **Default:** `workflow: checkpoint, worktrees: false`
- **Invariants (not config):** meaningful commit messages, commit before risky ops, commit after working states, only commit after verification, explicit staging, no force-push without permission
- **Informed by:** Jozefiak "How to Use Git When Building with AI" (May 2026), Plain English "Git Setup for AI Agents" / worktrees (Apr 2026), OpenAI "Harness Engineering" (Apr 2026), existing session-completion steering (agent-crews)
- **Status:** Accepted

### D-036: Completion is a sequence of components + compositional handoff
- **Decision:** Completion defines the sequence in which components fire at task end: verification → git → signaling → followups → handoff → notifications → memory. Followups default to file-issues. Handoff is compositional — user picks which elements to include from 10 available: asked-delivered, state-change, files, problems, wrong-turns, decisions, issues-filed, next-steps, context, verification. Presets for convenience: minimal (asked-delivered/files/next-steps), standard (default — asked-delivered/state-change/files/issues-filed/next-steps), full (all 10).
- **Key elements from research:** `wrong-turns` (what was tried/rejected and WHY — prevents next session re-deriving same rejected approaches), `decisions` (choices with rationale, not just outcomes), `context` (anything next session needs that isn't in the code — "context landmines").
- **Anti-patterns:** "Done!" with no handoff (34% failure rate for implicit context sharing per Athenic), handoff without wrong-turns (next session repeats rejected approaches), handoff without decision rationale (decisions get reversed without understanding why).
- **Informed by:** Blake Crosley "The Handoff Document: Agent Memory Across Sessions" (Mar 2026), davila7/session-handoff skill (explainx.ai), Anthropic long-running agent guidance, Addy Osmani "Long-running Agents" (Apr 2026), Line Cook tidy phase SESSION SUMMARY (smileynet/line-cook), Athenic handoff patterns case study, existing session-completion steering (agent-crews)
- **Status:** Accepted

---

## Open Questions (not yet decided)

- **Subagent resource inheritance:** Confirm that when orchestrator dispatches a named subagent, the subagent loads its OWN .json resources, not the parent's. Docs strongly imply this but needs testing post-implementation.

---

## Implementation Interview Decisions

### I-001: Component delivery mechanism — steering files with targeted resource globs
- **Decision:** Components deliver behavioral rules via steering files in `.kiro/steering/{universal,orchestrator,worker}/`. Each generated agent JSON explicitly declares which subdirectories it loads via resources. Orchestrators load universal + orchestrator. Workers load universal + worker. No context pollution — each agent type sees only relevant rules.
- **Confirmed by:** Kiro-cli docs (custom agents must explicitly declare resources), DACS paper (irrelevant context degrades performance from 96.7% to 21%)
- **Status:** Accepted

### I-002: Orchestrator prompt content — identity + delegation + routing + theme only
- **Decision:** Agent prompt field contains ONLY: identity, scope/refuses, delegation rules, routing table (handoff), theme voice. All behavioral rules (verification, git, completion, etc.) go in steering files.
- **Status:** Accepted

### I-003: Prompt fragment ordering for orchestrators
- **Decision:** Identity + scope → Delegation rules → Handoff routing → Task tracking + decisions → Narration → Completion sequence. Identity at top (highest attention), completion at bottom (recency bias for "how to finish").
- **Status:** Accepted

### I-004: Verifier/editor dispatch — part of completion sequence
- **Decision:** Completion component's steering tells the orchestrator: "Step 1: dispatch verifier. Step 2: if writing produced, dispatch editor. Step 3: emit DONE signal." No hooks needed.
- **Status:** Accepted

### I-005: All agents generated as .json — single standardized format
- **Decision:** Orchestrators, workers, verifier, editor — all generated as .json files. Same format, same generation pipeline. Verifier/editor are just simpler (fewer tools, no steering resources intentionally).
- **Status:** Accepted

### I-006: Generator produces file:// prompt URIs, not inline prompts
- **Decision:** Generator writes assembled prompts as separate .md files in `.kiro/prompts/`, referenced via `"prompt": "file://.kiro/prompts/<agent>.md"` in the JSON. Readable, diffable, grep-able.
- **Status:** Accepted

### I-007: Defaults live in fleet.yaml, pointing to component variant files
- **Decision:** `fleet.yaml` defaults section declares which variant of each component is default. Actual content lives in `shared/components/<name>/<variant>.yaml`. Resolution: fleet defaults → project crew.yaml overrides → component file content.
- **Status:** Accepted

### I-008: Search default always includes web; memory is composable tiers; decisions are selectable
- **Decision:** Search: `sources: [local, web]` always. Memory: composable `tiers: [working, session]` default, add episodic/semantic when earned. Decisions: selectable (progressive/upfront/minimal).
- **Status:** Accepted

### I-009: Task tracking — fixed methodology, selectable backend
- **Decision:** Soft planning methodology is invariant (patterns available in any order). Backend is selectable: todo-tool (default), beads, github-issues, flat-file.
- **Status:** Accepted

### I-010: Scope declarations live in crew YAML
- **Decision:** Each crew YAML declares `scope: { handles: [...], refuses: [...] }`. Generator reads all crews in a project, builds routing table for each orchestrator.
- **Status:** Accepted

### I-011: Migration via diff-based validation, no legacy support
- **Decision:** Implement components, generate output, diff against current. Fix semantic differences. No parallel old/new paths needed at this project phase.
- **Status:** Accepted

### I-012: Regeneration — manual with staleness check
- **Decision:** `just build` regenerates all. `just check` reports stale projects (source newer than output). Post-change rule extends to component files.
- **Status:** Accepted

### I-013: Component dependencies — convention-based, implicit from structure
- **Decision:** No explicit dependency graph. Component YAML's `subagents:`, `resources:`, `allowed_commands:` fields ARE the dependency declarations. Generator reads them and acts. Explicit `requires:` only added if we hit a case where implicit doesn't work (Terraform's "last resort" principle).
- **Informed by:** Terraform implicit reference-based dependencies (preferred), Ansible meta/main.yml (explicit, known problems with deep chains)
- **Status:** Accepted

### I-014: Safety settings — deniedCommands and deniedPaths for workers
- **Decision:** Workers get `deniedCommands: ["rm -rf *", "git push --force*", "git reset --hard*", "git clean -f*"]` and `deniedPaths: [".kiro/agents/**", ".kiro/steering/**", ".kiro/settings/**"]`. Workers shouldn't modify agent infrastructure or force-push.
- **Status:** Accepted

### I-015: Structured component declarations (YAML, not pure .md)
- **Decision:** Each component is a YAML file declaring: name, description, targets, prompt fragment, allowed_commands, resources, hooks, steering content, and subagent definitions. Generator reads these and merges into agent JSON.
- **Status:** Accepted

### I-016: Kiro-cli compliance confirmed
- **Decision:** Plan is fully compliant with kiro-cli idiomatic syntax. All features used (resources, tools, toolsSettings, hooks, file:// URIs, glob patterns) are documented and supported.
- **Status:** Confirmed

- How does the theme manifest work mechanically? (fleet.yaml theme field → generator renames agents?)
- Should components be YAML fragments or markdown files?
- How does structural linting for custom crew drift work?
- What's the full list of components? (We've covered signaling, sanity-gate, search, memory — still need notifications, task-tracking, decisions, handoff, narration, troubleshooting, writing, verification, git, completion)
- How do we handle the transition from current monolithic crews to component-based composition?

---

## Implementation Status

| Item | Status |
|------|--------|
| Scriptorium crew created | ✅ Done |
| 6 new skills created | ✅ Done |
| Persona separation (steering) | ✅ Done |
| SA assumptions removed from base crews | ✅ Done |
| All projects set to personal | ✅ Done |
| ferris-tracker crews moved back | ✅ Done |
| taskflow-ui cleaned of SA crews | ✅ Done |
| fleet.yaml created | ❌ Not yet |
| fleet.local.yaml + .gitignore | ❌ Not yet |
| Generator reads from fleet.yaml | ❌ Not yet |
| Simplified justfile commands | ❌ Not yet |
| Component extraction | ❌ Not yet (design phase) |
| Theme manifest | ❌ Not yet |
| best_practices documentation-taxonomy | ✅ Done |
| best_practices BPAPPA research | ✅ Done |
