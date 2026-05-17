# ADR 0013: Standardize ephemeral handoff artifacts

Handoffs are a high-leverage continuity mechanism, but free-form summaries lose decisions, evidence, and next steps too easily. agent-crews will treat handoff as a standardized ephemeral artifact: minimal YAML frontmatter (`created_at`, `base_commit`, `handoff_key`), a required semi-structured body (objective, constraints, prior decisions, current state, next steps), optional evidence pointers, and supersession by `handoff_key`; prompts and skills should point to artifacts rather than dumping logs or transcripts.
