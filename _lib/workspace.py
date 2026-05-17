"""Workspace contract: ephemeral + durable roots, contract steering, prompt substitution.

The workspace is the project-scoped filesystem surface where agents leave artifacts:
- `ephemeral` root holds disposable working state (current handoff, scratch notes).
  Lifecycle: ≤ one handoff cycle. Newer handoff with the same `handoff_key` supersedes
  the older one.
- `durable` root holds curated knowledge that should survive across sessions
  (decisions, references, distilled findings). Promotion from ephemeral to durable is
  explicit and bounded; no auto-promotion.

Generator scope (per ADR 0013 + design decisions):
- Pre-create the two roots inside each project.
- Emit `.kiro/steering/universal/workspace.md` describing the contract with the
  resolved paths so every agent sees them.
- Substitute `{{workspace.ephemeral}}` and `{{workspace.durable}}` in synced prompts.
- NEVER populate ephemeral/durable content. The generator owns topology, not artifacts.
"""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_EPHEMERAL = ".scratch"
DEFAULT_DURABLE = ".memory"


def resolve_workspace(crew_cfg: dict, source: str = "<crew.yaml>") -> dict:
    """Return {'ephemeral': str, 'durable': str} from crew config or defaults.

    If `workspace:` is present in the config, both `ephemeral` and `durable` MUST be
    declared — partial overrides are rejected to keep the public contract literal
    (ADR 0012). When omitted entirely, product defaults apply.
    """
    ws = crew_cfg.get("workspace")
    if ws is None:
        return {"ephemeral": DEFAULT_EPHEMERAL, "durable": DEFAULT_DURABLE}
    if not isinstance(ws, dict):
        sys.exit(f"  ❌ {source}: 'workspace:' must be a mapping with 'ephemeral' and 'durable' keys")
    ephemeral = ws.get("ephemeral")
    durable = ws.get("durable")
    if not ephemeral or not durable:
        sys.exit(
            f"  ❌ {source}: 'workspace:' requires both 'ephemeral:' and 'durable:' paths "
            "(omit the whole block to accept defaults)"
        )
    return {"ephemeral": str(ephemeral), "durable": str(durable)}


def stage_workspace(proj_dir: Path, kiro_dir: Path, workspace: dict):
    """Create the workspace directories and the universal contract steering file."""
    eph = proj_dir / workspace["ephemeral"]
    dur = proj_dir / workspace["durable"]
    eph.mkdir(parents=True, exist_ok=True)
    dur.mkdir(parents=True, exist_ok=True)

    steering_dir = kiro_dir / "steering" / "universal"
    steering_dir.mkdir(parents=True, exist_ok=True)
    (steering_dir / "workspace.md").write_text(
        _workspace_steering(workspace),
        encoding="utf-8",
    )


def substitute_workspace_placeholders(text: str, workspace: dict) -> str:
    """Replace `{{workspace.ephemeral}}` / `{{workspace.durable}}` in a string."""
    return (
        text.replace("{{workspace.ephemeral}}", workspace["ephemeral"])
        .replace("{{workspace.durable}}", workspace["durable"])
    )


def _workspace_steering(workspace: dict) -> str:
    eph = workspace["ephemeral"]
    dur = workspace["durable"]
    return f"""---
inclusion: always
---

# Workspace

Two project-scoped roots define where agents leave artifacts. Both are pre-created
during build; the contract is intentionally minimal.

| Root | Path | Lifecycle | Use for |
|------|------|-----------|---------|
| Ephemeral | `{eph}/` | ≤ one handoff cycle (newer handoff supersedes older) | Current handoff, scratch notes, draft artifacts |
| Durable | `{dur}/` | Persists across sessions; promotion is explicit | Curated decisions, distilled findings, references worth keeping |

## Rules

- The standardized handoff lives at `{eph}/HANDOFF.md` (see `@handoff` / `@read-handoff`).
- Never write durable artifacts from inside the ephemeral root; promote intentionally.
- Treat ephemeral content as expendable — do not link to it from durable docs.
- All shared artifacts (anything another agent or future session may read) MUST start
  with a YAML frontmatter `created_at:` and `base_commit:`; handoffs additionally
  carry `handoff_key:`. Private scratch you alone will read is exempt.
"""
