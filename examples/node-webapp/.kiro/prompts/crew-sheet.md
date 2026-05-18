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

