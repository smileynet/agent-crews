# ADR 0011: agent-crews owns explicit injected runtime context

Agent runtime behavior should not depend on a project owner maintaining `AGENTS.md` correctly, because `AGENTS.md` is portable, owner-managed, and outside agent-crews' runtime-context guarantees. agent-crews will instead treat explicit injected context as the source of truth for deployed agents: prompt content, targeted resources/steering, and skills are what define each agent's runtime context.
