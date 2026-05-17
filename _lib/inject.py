"""Dispatcher synthesis and subagent injection."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from _lib import get_architypes


def synthesize_dispatcher(
    crew_files: list[Path],
    shared_agents: list[str],
    kiro_dir: Path,
    dispatcher_config: dict | None = None,
    dry_run: bool = False,
) -> str:
    """Auto-generate a project dispatcher from crew composition (ADR-008)."""
    dispatcher_config = dispatcher_config or {}

    leads = []
    for cf in crew_files:
        try:
            crew = yaml.safe_load(cf.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        for archetype in get_architypes(crew or {}):
            if archetype.get("type") != "orchestrator":
                continue
            for agent in archetype.get("agents", []):
                leads.append({
                    "name": agent["name"],
                    "description": agent.get("description", ""),
                    "routes": agent.get("routes", ""),
                })

    if not leads:
        return ""

    routing_lines = ["| Crew Lead | Send work when... |",
                     "|-----------|-------------------|"]
    for lead in leads:
        routing_lines.append(f"| {lead['name']} | {lead['routes']} |")
    routing_table = "\n".join(routing_lines)

    if shared_agents:
        shared_lines_parts = []
        for name in shared_agents:
            routes_hint = ""
            for cf in crew_files:
                try:
                    crew_data = yaml.safe_load(cf.read_text(encoding="utf-8"))
                except (yaml.YAMLError, OSError):
                    continue
                for arch in get_architypes(crew_data or {}):
                    for ag in arch.get("agents", []):
                        if ag["name"] == name and ag.get("routes"):
                            routes_hint = ag["routes"]
                            break
            if routes_hint:
                shared_lines_parts.append(f"- {name} → {routes_hint}")
            else:
                shared_lines_parts.append(f"- {name}")
        shared_lines = "\n".join(shared_lines_parts)
    else:
        shared_lines = "(none configured)"

    prompt_suffix = dispatcher_config.get("prompt_suffix", "")
    prompt = f"""You are dispatcher — the project orchestrator.

## Routing Principle

Route based on INTENT, not completeness. If you know which lead handles it, delegate immediately — even if details are missing. Workers gather their own details. Only ask when you genuinely cannot determine which lead to route to.

Do NOT ask clarifying questions about task details (what kind of agent, which file, etc.) — delegate with whatever context the user provided and let the specialist ask if needed.

## Routing Decision (MANDATORY — before ANY tool call)

Classify the request FIRST. Do not read files to "understand" the request before routing.

| Request type | Action |
|-------------|--------|
| Simple read (list a directory, show a known file) | Self-execute with read tool |
| Needs investigation, creation, modification, or diagnosis | DELEGATE to crew lead |
| Cannot determine which lead handles this | Ask one clarifying question |

You have only: read, subagent, todo_list. You CANNOT write, execute commands, search, or grep.
Any task requiring those capabilities MUST be delegated.

## Routing Table

{routing_table}

## Shared Utilities
Dispatch directly (no lead needed) for one-shot tasks:
{shared_lines}

Route to these when the request matches their domain — don't attempt the work yourself.

## Delegation Format
Always include:
- agentName: exact agent name
- task: clear description of what to achieve
- context: relevant details from user request

## Rules
- Simple read (file you know the path to) → answer directly
- Everything else → DELEGATE to the appropriate crew lead
- Multi-crew work → plan the sequence with todo_list, dispatch leads in order
- Never investigate a problem yourself — you lack the tools for it
- Always narrate: "Delegating to X because Y"
- When in doubt → DELEGATE (false delegation is cheap, false self-execution fails)
{prompt_suffix}"""

    welcome_lines = ["🎯 Dispatcher ready. What are we working on?\n",
                     "Available crews:"]
    for lead in leads:
        short_desc = lead["routes"][:60] if lead["routes"] else lead["description"][:60]
        welcome_lines.append(f"- {short_desc} → {lead['name']}")
    welcome_lines.append("")
    if shared_agents:
        welcome_lines.append(f"Utilities: {', '.join(shared_agents)}")
        welcome_lines.append("")
    welcome_lines.append("Or just tell me what to do — simple tasks I'll handle directly.")
    welcome_message = "\n".join(welcome_lines)

    available = [lead["name"] for lead in leads] + shared_agents
    shortcut = dispatcher_config.get("keyboard_shortcut", "ctrl+shift+d")

    agent_json = {
        "name": "dispatcher",
        "description": "Project orchestrator — plans work, routes to crew leads, reads context",
        "tools": ["read", "subagent", "todo_list"],
        "allowedTools": ["read", "subagent", "todo_list"],
        "toolsSettings": {
            "subagent": {
                "availableAgents": available,
                "trustedAgents": available,
            },
        },
        "prompt": prompt,
        "welcomeMessage": welcome_message,
        "keyboardShortcut": shortcut,
    }

    resources = []
    agents_md = kiro_dir.parent / "AGENTS.md"
    if agents_md.exists():
        resources.append("file://AGENTS.md")
    if resources:
        agent_json["resources"] = resources

    out_path = kiro_dir / "agents" / "dispatcher.json"
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(agent_json, f, indent=2)
            f.write("\n")

    return "dispatcher"
