# ADR-003: Eight Themed Crews with Scope Boundaries

**Status:** Accepted  
**Date:** 2026-05-07  
**Sources:** Session analysis (6 sessions showing distinct work modes)

## Context

Session history revealed distinct work modes (bug fixing, infrastructure, research, features, hygiene, content, writing) that benefit from different team compositions and mental models.

## Decision

Eight crews, each with a game theme for memorability and a declared scope:

| Crew | Scope | Refuses |
|------|-------|---------|
| Raid Party (WoW) | Features, mixed work | Bug-fixing, infra |
| Bug Hunt (Monster Hunter) | Bugs, testing, debugging | Features, infra, research |
| Deploy Squad (StarCraft) | Infrastructure, CI/CD | Features, bugs |
| Lore Guild (Final Fantasy) | Research, documentation | Features, bugs, infra |
| Recon Squad (Dark Souls) | Brownfield onboarding | Features, bugs, deployment |
| Pit Crew (F1) | Project hygiene, tech debt | Features, bugs, infra |
| Content Crew (BG3/D&D) | Presentations, tutorials | Code, bugs, infra |
| Scriptorium (Medieval) | Writing, editing, prose | Code, bugs, infra |

### Why themes?

- Memorable agent names (raid-leader vs "orchestrator-1")
- Consistent mental model within a crew
- Fun — reduces friction in daily use

### Why scope boundaries?

- Prevents crews from absorbing work they're not designed for
- Enables automatic handoff routing (generator builds routing tables from scope declarations)
- Each crew stays focused on what it does best

## Consequences

- Each crew YAML declares `scope: { handles, refuses }`
- Generator produces handoff routing tables for orchestrators
- Users switch crews when work type changes (not mid-task)
- Adding a new crew = define scope + agents + run generator
