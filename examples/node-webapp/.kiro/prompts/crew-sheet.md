# Crew Sheet

All available agents and crews for this project.

## Bug-Fix

| Agent | Role | Command |
|-------|------|---------|
| bugfix-lead | Orchestrator — assigns bugs, tracks fixes, reports results | `/agent bugfix-lead` or `ctrl+shift+h` |
| triager | Triager — prioritizes bugs, defines fix criteria | `/agent triager` |
| investigator | Investigator — root cause analysis, five whys, git blame | `/agent investigator` |
| practices-advisor | Practices advisor — how others solved this class of bug | `/agent practices-advisor` |
| reproducer | Reproducer — creates minimal repro, isolates with failing test | `/agent reproducer` |
| fixer | Fixer — applies minimal targeted code fix | `/agent fixer` |
| verifier | Verifier — runs test suite, checks for regressions | `/agent verifier` |
| documenter | Documenter — PR description, changelog, commit message | `/agent documenter` |

## Content

| Agent | Role | Command |
|-------|------|---------|
| content-lead | Orchestrator — plans content structure, assigns roles | `/agent content-lead` or `ctrl+shift+b` |
| narrative-writer | Narrative writer — slides, rhetoric, storytelling | `/agent narrative-writer` |
| content-researcher | Researcher — fact-checking, citations, technical accuracy | `/agent content-researcher` |
| tutorial-writer | Tutorial writer — workshops, step-by-step guides | `/agent tutorial-writer` |
| content-reviewer | Reviewer — accessibility, tone, consistency, polish | `/agent content-reviewer` |
| publisher | Publisher — formatting, export, MARP, handouts | `/agent publisher` |

## General

| Agent | Role | Command |
|-------|------|---------|
| general-lead | Orchestrator — assigns tasks, tracks progress, reports results | `/agent general-lead` or `ctrl+shift+p` |
| planner | Planner — breaks work into sequenced tasks with criteria | `/agent planner` |
| explorer | Code explorer — searches local code, wikis, documentation | `/agent explorer` |
| researcher | Deep researcher — recursive investigation until full understanding | `/agent researcher` |
| challenger | Blind spot finder — zooms out, challenges assumptions | `/agent challenger` |
| advisor | Best practices advisor — prior art, anti-patterns, standards | `/agent advisor` |
| architect | Architect — designs solutions, makes structure decisions | `/agent architect` |
| builder | Builder — writes code and runs builds | `/agent builder` |
| tester | Tester — writes and runs tests, validates | `/agent tester` |
| committer | Git ops — commits, branches, PRs | `/agent committer` |
| reviewer | Reviewer — verifies claims against evidence | `/agent reviewer` |
| advocate | Customer advocate — JTBD lens, validates the right problem | `/agent advocate` |

## Hygiene

| Agent | Role | Command |
|-------|------|---------|
| hygiene-lead | Orchestrator — runs maintenance audits, prioritizes fixes | `/agent hygiene-lead` or `ctrl+shift+g` |
| doc-checker | Doc freshness — README, AGENTS.md accuracy | `/agent doc-checker` |
| deps-checker | Deps & config — dependencies, env vars, task runners | `/agent deps-checker` |
| structure-checker | Structure & conventions — layout, patterns, standards | `/agent structure-checker` |
| link-checker | Link & reference checker — broken links, stale TODOs, dead refs | `/agent link-checker` |
| fix-verifier | Verifier — validates fixes pass CI and links resolve | `/agent fix-verifier` |

## Infrastructure

| Agent | Role | Command |
|-------|------|---------|
| infrastructure-lead | Orchestrator — plans missions, manages checkpoints | `/agent infrastructure-lead` or `ctrl+shift+c` |
| deploy-planner | Planner — deployment sequence, dependencies, rollback | `/agent deploy-planner` |
| infra-advisor | Advisor — IaC best practices, known pitfalls | `/agent infra-advisor` |
| provisioner | Builder — terraform/cdk/cfn apply, docker build | `/agent provisioner` |
| monitor | Monitor — health checks, resource state verification | `/agent monitor` |
| security-reviewer | Security — SGs, IAM, compliance checks | `/agent security-reviewer` |
| cleanup | Cleanup — terraform destroy, scale-to-zero | `/agent cleanup` |

## Meta

| Agent | Role | Command |
|-------|------|---------|
| build-lead | Build crew lead — plans and delegates crew creation/modification | `/agent build-lead` |
| ops-lead | Ops crew lead — plans and delegates analysis, diagnosis, validation | `/agent ops-lead` |
| crew-creator | Crew Creator — creates agent teams for new projects | `/agent crew-creator` |
| crew-augmenter | Crew Augmenter — adds agents/features to existing crews | `/agent crew-augmenter` |
| crew-doctor | Crew Doctor — diagnoses and fixes agent team issues | `/agent crew-doctor` |
| crew-analyst | Crew Analyst — analyzes sessions, finds performance issues | `/agent crew-analyst` |
| crew-researcher | Crew Researcher — deep investigation, patterns, best practices | `/agent crew-researcher` |
| kiro-helper | Kiro Helper — CLI troubleshooting, MCP config, tool naming | `/agent kiro-helper` |
| crew-validator | Crew Validator — proactive post-change verification, changelog enforcement | `/agent crew-validator` |
| crew-releaser | Crew Releaser — release pipeline orchestration, changelog curation, version management | `/agent crew-releaser` |
| project-hygiene | Project Hygiene — data separation, doc accuracy, sanitization | `/agent project-hygiene` |
| bugfix-lead | Bug-fix orchestrator — systematic debugging of agent-crews tooling | `/agent bugfix-lead` |
| meta-debugger | Debugger — root-cause analysis on agent-crews tooling | `/agent meta-debugger` |
| meta-tester | Tester — evals, smoke tests, regression checks | `/agent meta-tester` |

## Onboarding

| Agent | Role | Command |
|-------|------|---------|
| onboarding-lead | Orchestrator — maps unknown codebases, produces onboarding guides | `/agent onboarding-lead` or `ctrl+shift+e` |
| mapper | Mapper — repo structure, languages, build system | `/agent mapper` |
| analyst | Analyst — architecture, data flow, dependencies | `/agent analyst` |
| auditor | Auditor — quality gaps, what exists vs missing | `/agent auditor` |
| restorer | Restorer — creates missing README, tests, docs | `/agent restorer` |
| guide-writer | Guide writer — onboarding document for next developer | `/agent guide-writer` |

## Research

| Agent | Role | Command |
|-------|------|---------|
| research-lead | Orchestrator — sequences research, ensures quality | `/agent research-lead` or `ctrl+shift+s` |
| outliner | Outliner — defines scope, plans structure | `/agent outliner` |
| internal-researcher | Internal researcher — local code, wikis, internal docs | `/agent internal-researcher` |
| external-researcher | External researcher — web, official docs, GitHub | `/agent external-researcher` |
| writer | Writer — structured markdown, every claim sourced | `/agent writer` |
| fact-checker | Fact-checker — verifies every claim against sources | `/agent fact-checker` |
| editor | Editor — formatting, cross-references, consistency | `/agent editor` |

## Rust

| Agent | Role | Command |
|-------|------|---------|
| rust-lead | Orchestrator — assigns Rust tasks, tracks progress, reports results | `/agent rust-lead` or `ctrl+shift+r` |
| rust-linter | Linter — clippy, cargo fmt, deny lints, code quality enforcement | `/agent rust-linter` |
| rust-builder | Builder — implements Rust features, modules, and crates | `/agent rust-builder` |
| rust-tester | Tester — writes and runs tests, checks coverage | `/agent rust-tester` |

## Writing

| Agent | Role | Command |
|-------|------|---------|
| writing-lead | Orchestrator — sequences doc audit, planning, writing, verification | `/agent writing-lead` or `ctrl+shift+w` |
| doc-auditor | Auditor — D.O.C.S. audit, gap analysis, maturity assessment | `/agent doc-auditor` |
| doc-architect | Architect — Diátaxis classification, doc structure planning | `/agent doc-architect` |
| doc-writer | Writer — README, architecture, reference, explanation docs | `/agent doc-writer` |
| tutorial-author | Tutorial author — getting-started, tutorials, onboarding guides | `/agent tutorial-author` |
| doc-verifier | Verifier — link checking, accuracy, formatting, consistency | `/agent doc-verifier` |

