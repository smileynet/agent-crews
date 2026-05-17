# ADR 0012: Public config prefers literal mechanisms over hidden defaults

agent-crews is still shaping its public configuration model, so we should optimize for a clean mental model rather than convenience hacks. Public config should use the simplest literal mechanism that matches its meaning, with no hidden defaults or special-case semantics, because consistency is more valuable than shaving a repeated list item or adding magical inclusion rules.
