"""Type definitions for agent-crews generator."""

from __future__ import annotations

from typing import TypedDict


class AgentJSON(TypedDict, total=False):
    """Output shape written to .kiro/agents/*.json."""

    name: str
    description: str
    prompt: str
    tools: list[str]
    allowedTools: list[str]
    toolsSettings: dict[str, dict]
    resources: list[str]
    hooks: dict
    mcpServers: dict
    keyboardShortcut: str
    welcomeMessage: str


class CrewConfig(TypedDict, total=False):
    """Shape of a crew YAML file (base/crews/*.yaml)."""

    architypes: list[dict]
    archetypes: list[dict]
    extends: str
    tools: list[str]
    allowedTools: list[str]
    toolsSettings: dict[str, dict]
    resources: list[str]
    hooks: dict
    mcpServers: dict
    welcomeMessageSuffix: str


class FleetProject(TypedDict, total=False):
    """Per-project entry in fleet config."""

    path: str
    crews: list[str]
    behavior: dict
    persona: str


class FleetConfig(TypedDict, total=False):
    """Shape of fleet.yaml / fleet.example.yaml."""

    defaults: dict
    projects: dict[str, FleetProject]
