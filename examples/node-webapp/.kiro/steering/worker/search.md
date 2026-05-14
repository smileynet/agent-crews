---
inclusion: always
---
# Search Protocol (Layered)

## Sources (ordered by priority)
local → web

Available sources: local, web

## Resolution Rules
- Search sources in priority order
- Stop when answer is found with sufficient confidence
- If sources conflict: first-authoritative
- Always cite source for every finding

## Source Types
| Source | What it searches | When to use |
|--------|-----------------|-------------|
| local | Project files, code, docs | First — cheapest, most relevant |
| cached-docs | Pre-indexed documentation | Known APIs, frameworks |
| web | Live internet search | Current info, unknown topics |
| internal | Company wikis, repos | Org-specific knowledge |
| mcp | MCP server tools | Specialized data sources |

## Anti-Patterns
- ❌ Searching web before checking local docs
- ❌ Trusting a single source for critical claims
- ❌ Searching without a specific question in mind
- ❌ Long specific queries (start broad, narrow later)

## Output
Every search result must include:
- Source (file path, URL, or tool name)
- Confidence (verified / likely / uncertain)
- Relevance to the original question
