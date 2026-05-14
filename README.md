# Agent Crews

You don't need a bigger context window, you need a crew.

Agent Crews for [kiro-cli](https://github.com/kiro-cli) projects. Each crew is specialized — unique agents built for a specific purpose. A lead plans the work and delegates to the right specialist. Use the general crew as your everyday default, or deploy a specialized crew when you're deep in bugs, infrastructure, research, or writing.

## Out of the box

The **general** crew handles everyday work — features, small fixes, quick questions. It's your default. Specialized crews exist for work that benefits from dedicated agents with domain-specific protocols:

| Crew | When to use | Why specialized |
|------|-------------|-----------------|
| General | Features, mixed work, anything routine | Default — covers most tasks |
| Bug Fix | Reproducing and fixing bugs | Systematic root-cause analysis, regression testing, minimal-fix discipline |
| Infrastructure | Provisioning, deploying, IaC | Health checks, rollback planning, blast-radius awareness |
| Research | Investigation, documentation | Source triangulation, fact-checking, citation tracking |
| Onboarding | Understanding a new codebase | Architecture scanning, dependency tracing, guide generation |
| Hygiene | Keeping the project accurate and organized | Docs reflect reality, instructions stay current, dead code gets removed |
| Content | Presentations, tutorials, demos | Structured for visual/slide formats, audience targeting, narrative arc |
| Writing | Prose, editing, long-form docs | Style enforcement, editor review loops, structural coherence |

Content is for things with slides, visuals, or a live audience. Writing is for documents people read — READMEs, ADRs, blog posts, technical guides.

Start with general. Switch to a specialist when the work is complex enough to benefit from agents that think differently about the problem.

## Getting started

```bash
git clone https://github.com/smileynet/agent-crews.git
cd agent-crews
kiro-cli chat -A --agent dispatcher
```

The dispatcher will walk you through setup — configuring your project, picking crews, and deploying agents.

Once deployed, use `@crew-sheet` in your project for a quick reference of available agents and commands. See the [Use Case Guide](docs/use-case-guide.md) for workflows.

## What to commit in your project

Commit the deployed `.kiro/` directory to your project repo. The generated files are self-contained — no dependency on agent-crews at runtime. Skip this if you prefer to regenerate on demand.

## How it works

You define crews and configure behavior. The generator assembles everything into agents you can deploy anywhere — update once here, refresh crews across all your projects.

- [Components](docs/component-architecture/spec.md) — reusable instructions that make it easy to deploy and maintain consistent behavioral preferences across projects
- [Themes](docs/themed-crews-guide.md) — give your crews some character without losing performance
- [Examples](examples/) — check out samples before deploying to your project

## Commands

| Task | Command |
|------|--------|
| Generate all | `just build` |
| Deploy to project | `just link <project>` |
| Fleet status | `just status` |
| Validate | `just check` |

---

[Report a bug](../../issues/new?template=bug_report.yml) · [Request a feature](../../issues/new?template=feature_request.yml)

Your agents can file these too — [bug template](.github/ISSUE_TEMPLATE/bug_report.md), [feature template](.github/ISSUE_TEMPLATE/feature_request.md).
