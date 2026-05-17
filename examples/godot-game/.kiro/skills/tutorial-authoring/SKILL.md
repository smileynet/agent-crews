---
name: tutorial-authoring
description: "Author hands-on tutorials that take readers from zero to a working result. Use when producing a new tutorial, getting-started guide, onboarding doc, or restructuring docs that drifted from tutorial into reference. Trigger terms: tutorial, getting started, onboarding, step-by-step guide, walkthrough, hands-on, learning guide."
---

# Tutorial Authoring

A tutorial teaches. It holds the reader's attention across many steps, surfaces only what's needed at each step, and leaves the reader with both a working result and a model of why it worked.

A tutorial is not a README (orients in seconds), not a runbook (executed under time pressure), not a reference (looked up). It is a guided learning experience.

## Spine and Reference Split

Every tutorial has two surfaces:

- **Spine modules** — the linear path. One module per logical step, ordered by dependency. Numbered prefixes (`00-mental-model.md`, `01-environment.md`). Each ends with the reader having done something concrete.
- **Reference pages** — lookups needed along the way. Datasets, config fields, troubleshooting. Visited on demand, not read in order.

**Test:** Imagine the reader doing the tutorial a second time. The thing they walk through is the spine. The thing they look up is the reference.

## Module Structure

Every spine module has the same frame:

```markdown
# N. Module Title (the outcome, not the activity)

> [← index](../README.md) · [← prev](NN-prev.md) · [next →](NN-next.md)

**What You'll Learn**: One sentence — the concrete outcome.

## Section heading

Prose. State the goal, then show the action.

\```bash
the-command --flag value
\```

What the command did. What the reader sees now.

⚠️ **Pitfall**: Concrete trap with symptom and recovery.

---

> [← index](../README.md) · [← prev](NN-prev.md) · [next →](NN-next.md)
```

## Required Patterns

**Module sizing.** 80-180 lines. Below 80 → collapse with neighbour. Above 180 → extract a reference page.

**Outcome-named slugs.** Name by what the reader HAS at the end: `02-positive-samples.md` (you have samples), not `02-recording-audio.md` (you did recording).

**Lazy linking via `<details>`.** Collapse additive context at point of mention. Reader mid-action skips it; reader who pauses opens it without losing their place.

```markdown
<details>
<summary>Other paths the script writes to</summary>
See [config-fields.md](../reference/config-fields.md#paths) for the full list.
</details>
```

**Pitfall dual-storage.** Each `⚠️ Pitfall` appears:
1. Inline at the moment of risk in the spine module
2. Mirrored in `reference/troubleshooting.md` indexed by symptom

Two reader populations: first-time linear walker vs. broke-something-now-searching.

**Every step independently verifiable.** Show expected output after each command. The reader must be able to confirm they're on track without proceeding to the next step.

**Prerequisites stated explicitly.** Exact versions, tools, prior knowledge. Never assume without stating.

## Banned Patterns

- **Reference manual masquerading as tutorial** — tables and flag lists in a spine module. Extract to reference.
- **`<details>` hiding required steps** — collapsed blocks are for additive context only. Required steps stay inline.
- **Forward links from module M to module N** — invites reader to leave the spine. Foreshadow with one sentence; don't link.
- **Assuming prior knowledge without stating it** — if the reader needs to know X, say so in prerequisites.
- **Decorative diagrams** — every diagram answers a question the reader has at that point.

## Tutorial vs How-To (Diátaxis Distinction)

| Tutorial | How-To Guide |
|----------|-------------|
## Self-Check

1. Can the reader complete without opening a reference page?
2. Does every step show expected output?
3. Are prerequisites complete and version-specific?
4. Does each module fit one screenful of attention?

