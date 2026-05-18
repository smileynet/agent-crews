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
| linter | Linter — runs eslint and reports code quality issues | `/agent linter` |
| deployer | Deployer — orchestrates deployments, delegates pre/post tasks | `/agent deployer` |

## Rust

| Agent | Role | Command |
|-------|------|---------|
| rust-lead | Orchestrator — assigns Rust tasks, tracks progress, reports results | `/agent rust-lead` or `ctrl+shift+r` |
| rust-linter | Linter — clippy, cargo fmt, deny lints, code quality enforcement | `/agent rust-linter` |
| rust-builder | Builder — implements Rust features, modules, and crates | `/agent rust-builder` |
| rust-tester | Tester — writes and runs tests, checks coverage | `/agent rust-tester` |

