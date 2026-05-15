#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Ingest session logs from 5 AI coding tools and normalize to a common format."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator


@dataclass
class NormalizedEvent:
    session_id: str
    tool: str
    project_path: str
    timestamp: str
    role: str
    content: str | None
    tool_name: str | None
    tool_input: str | None
    tool_output: str | None
    model: str | None
    provider: str | None
    tokens_in: int | None
    tokens_out: int | None
    tokens_cache_read: int | None
    tokens_cache_write: int | None
    cost: float | None
    duration_ms: int | None


@dataclass
class SessionMeta:
    session_id: str
    tool: str
    project_path: str
    timestamp: str
    title: str | None
    model: str | None


def truncate(s: str | None, max_len: int = 500) -> str | None:
    if s is None:
        return None
    return s[:max_len] if len(s) > max_len else s


def parse_since(since: str) -> datetime:
    m = re.match(r"^(\d+)([dhm])$", since)
    if not m:
        raise ValueError(f"Invalid --since format: {since}. Use e.g. 7d, 24h, 30m")
    val, unit = int(m.group(1)), m.group(2)
    delta = {"d": timedelta(days=val), "h": timedelta(hours=val), "m": timedelta(minutes=val)}[unit]
    return datetime.now(timezone.utc) - delta


def parse_iso(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.min.replace(tzinfo=timezone.utc)


def ms_to_iso(ms: int | float) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def matches_project(session_path: str, target: str) -> bool:
    if not target:
        return True
    return Path(session_path).resolve() == Path(target).resolve()


# --- oh-my-pi adapter ---

def omp_sessions_dir() -> Path:
    return Path.home() / ".omp" / "agent" / "sessions"


def omp_list_sessions(project: str | None, since: datetime | None) -> Iterator[SessionMeta]:
    base = omp_sessions_dir()
    if not base.exists():
        return
    for dir_entry in sorted(base.iterdir()):
        if not dir_entry.is_dir():
            continue
        for f in sorted(dir_entry.glob("*.jsonl")):
            try:
                with open(f) as fh:
                    header = json.loads(fh.readline())
            except (json.JSONDecodeError, OSError):
                continue
            if header.get("type") != "session":
                continue
            cwd = header.get("cwd", "")
            if project and not matches_project(cwd, project):
                continue
            ts = header.get("timestamp", "")
            if since and parse_iso(ts) < since:
                continue
            yield SessionMeta(
                session_id=header.get("id", f.stem),
                tool="oh-my-pi",
                project_path=cwd,
                timestamp=ts,
                title=header.get("title"),
                model=None,
            )


def omp_ingest_session(filepath: Path) -> Iterator[NormalizedEvent]:
    session_id = ""
    project_path = ""
    with open(filepath) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = entry.get("type")
            if etype == "session":
                session_id = entry.get("id", filepath.stem)
                project_path = entry.get("cwd", "")
                continue
            if etype in ("compaction", "custom_message"):
                continue
            if etype != "message":
                continue
            msg = entry.get("message", {})
            role = msg.get("role", "")
            usage = msg.get("usage", {})
            tokens_in = usage.get("input")
            tokens_out = usage.get("output")
            cache_read = usage.get("cacheRead")
            cache_write = usage.get("cacheWrite")
            cost_obj = usage.get("cost", {})
            cost = cost_obj.get("total") if isinstance(cost_obj, dict) else None
            model = msg.get("model")
            provider = msg.get("provider")
            duration = msg.get("duration")
            ts = entry.get("timestamp", "")

            if role == "user":
                texts = [c.get("text", "") for c in msg.get("content", []) if c.get("type") == "text"]
                yield NormalizedEvent(
                    session_id=session_id, tool="oh-my-pi", project_path=project_path,
                    timestamp=ts, role="user", content="\n".join(texts) or None,
                    tool_name=None, tool_input=None, tool_output=None,
                    model=model, provider=provider, tokens_in=tokens_in, tokens_out=tokens_out,
                    tokens_cache_read=cache_read, tokens_cache_write=cache_write,
                    cost=cost, duration_ms=duration,
                )
            elif role == "assistant":
                texts = []
                for c in msg.get("content", []):
                    if c.get("type") == "text":
                        texts.append(c.get("text", ""))
                    elif c.get("type") == "toolCall":
                        yield NormalizedEvent(
                            session_id=session_id, tool="oh-my-pi", project_path=project_path,
                            timestamp=ts, role="assistant", content=None,
                            tool_name=c.get("name"), tool_input=json.dumps(c.get("arguments")),
                            tool_output=None, model=model, provider=provider,
                            tokens_in=tokens_in, tokens_out=tokens_out,
                            tokens_cache_read=cache_read, tokens_cache_write=cache_write,
                            cost=cost, duration_ms=duration,
                        )
                if texts:
                    yield NormalizedEvent(
                        session_id=session_id, tool="oh-my-pi", project_path=project_path,
                        timestamp=ts, role="assistant", content="\n".join(texts),
                        tool_name=None, tool_input=None, tool_output=None,
                        model=model, provider=provider, tokens_in=tokens_in, tokens_out=tokens_out,
                        tokens_cache_read=cache_read, tokens_cache_write=cache_write,
                        cost=cost, duration_ms=duration,
                    )
            elif role == "toolResult":
                output_parts = msg.get("content", [])
                output_text = output_parts[0].get("text", "") if output_parts else ""
                yield NormalizedEvent(
                    session_id=session_id, tool="oh-my-pi", project_path=project_path,
                    timestamp=ts, role="tool_result", content=None,
                    tool_name=msg.get("toolName"), tool_input=None,
                    tool_output=truncate(output_text), model=None, provider=None,
                    tokens_in=None, tokens_out=None, tokens_cache_read=None,
                    tokens_cache_write=None, cost=None, duration_ms=None,
                )


def omp_ingest_all(project: str | None, since: datetime | None) -> Iterator[NormalizedEvent]:
    base = omp_sessions_dir()
    if not base.exists():
        return
    for dir_entry in sorted(base.iterdir()):
        if not dir_entry.is_dir():
            continue
        for f in sorted(dir_entry.glob("*.jsonl")):
            try:
                with open(f) as fh:
                    header = json.loads(fh.readline())
            except (json.JSONDecodeError, OSError):
                continue
            if header.get("type") != "session":
                continue
            cwd = header.get("cwd", "")
            if project and not matches_project(cwd, project):
                continue
            ts = header.get("timestamp", "")
            if since and parse_iso(ts) < since:
                continue
            yield from omp_ingest_session(f)


# --- Codex adapter ---

def codex_sessions_dir() -> Path:
    return Path.home() / ".codex" / "sessions"


def codex_list_sessions(project: str | None, since: datetime | None) -> Iterator[SessionMeta]:
    base = codex_sessions_dir()
    if not base.exists():
        return
    for f in sorted(base.rglob("rollout-*.jsonl")):
        meta = None
        try:
            with open(f) as fh:
                for line in fh:
                    entry = json.loads(line.strip())
                    if entry.get("type") == "session_meta":
                        meta = entry.get("payload", {})
                        break
        except (json.JSONDecodeError, OSError):
            continue
        if not meta:
            continue
        cwd = meta.get("cwd", "")
        if project and not matches_project(cwd, project):
            continue
        ts = meta.get("timestamp", entry.get("timestamp", ""))
        if since and parse_iso(ts) < since:
            continue
        yield SessionMeta(
            session_id=meta.get("id", f.stem),
            tool="codex",
            project_path=cwd,
            timestamp=ts,
            title=None,
            model=meta.get("model"),
        )


def codex_ingest_all(project: str | None, since: datetime | None) -> Iterator[NormalizedEvent]:
    base = codex_sessions_dir()
    if not base.exists():
        return
    for f in sorted(base.rglob("rollout-*.jsonl")):
        session_id = ""
        project_path = ""
        model = None
        skip = False
        events: list[NormalizedEvent] = []
        call_map: dict[str, NormalizedEvent] = {}
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    etype = entry.get("type")
                    payload = entry.get("payload", {})
                    ts = entry.get("timestamp", "")

                    if etype == "session_meta":
                        session_id = payload.get("id", f.stem)
                        project_path = payload.get("cwd", "")
                        model = payload.get("model")
                        if project and not matches_project(project_path, project):
                            skip = True
                            break
                        if since and parse_iso(ts) < since:
                            skip = True
                            break
                    elif etype == "response_item":
                        if payload.get("type") == "message":
                            role = payload.get("role", "")
                            content_list = payload.get("content", [])
                            text = content_list[0].get("text", "") if content_list else ""
                            events.append(NormalizedEvent(
                                session_id=session_id, tool="codex", project_path=project_path,
                                timestamp=ts, role=role, content=text or None,
                                tool_name=None, tool_input=None, tool_output=None,
                                model=model, provider=None, tokens_in=None, tokens_out=None,
                                tokens_cache_read=None, tokens_cache_write=None,
                                cost=None, duration_ms=None,
                            ))
                        elif payload.get("type") == "function_call":
                            ev = NormalizedEvent(
                                session_id=session_id, tool="codex", project_path=project_path,
                                timestamp=ts, role="assistant", content=None,
                                tool_name=payload.get("name"), tool_input=payload.get("arguments"),
                                tool_output=None, model=model, provider=None,
                                tokens_in=None, tokens_out=None,
                                tokens_cache_read=None, tokens_cache_write=None,
                                cost=None, duration_ms=None,
                            )
                            events.append(ev)
                            call_id = payload.get("call_id")
                            if call_id:
                                call_map[call_id] = ev
                    elif etype == "event_msg":
                        if payload.get("type") == "exec_command_end":
                            call_id = payload.get("call_id")
                            output = truncate(payload.get("aggregated_output"))
                            duration = payload.get("duration")
                            dur_ms = None
                            if isinstance(duration, (int, float)):
                                dur_ms = int(duration)
                            events.append(NormalizedEvent(
                                session_id=session_id, tool="codex", project_path=project_path,
                                timestamp=ts, role="tool_result", content=None,
                                tool_name=None, tool_input=None, tool_output=output,
                                model=None, provider=None, tokens_in=None, tokens_out=None,
                                tokens_cache_read=None, tokens_cache_write=None,
                                cost=None, duration_ms=dur_ms,
                            ))
        except (json.JSONDecodeError, OSError):
            continue
        if not skip:
            yield from events


# --- kiro-cli adapter ---

def kiro_sessions_dir() -> Path:
    return Path.home() / ".kiro" / "sessions" / "cli"


def kiro_list_sessions(project: str | None, since: datetime | None) -> Iterator[SessionMeta]:
    base = kiro_sessions_dir()
    if not base.exists():
        return
    for meta_file in sorted(base.glob("*.json")):
        try:
            meta = json.loads(meta_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        cwd = meta.get("cwd", "")
        if project and not matches_project(cwd, project):
            continue
        sid = meta.get("session_id", meta_file.stem)
        ts = meta.get("timestamp", "")
        if since and parse_iso(ts) < since:
            continue
        agent = None
        state = meta.get("session_state", {})
        if state:
            agent = state.get("agent_name")
        yield SessionMeta(
            session_id=sid, tool="kiro-cli", project_path=cwd,
            timestamp=ts, title=agent, model=None,
        )


def kiro_ingest_all(project: str | None, since: datetime | None) -> Iterator[NormalizedEvent]:
    base = kiro_sessions_dir()
    if not base.exists():
        return
    for meta_file in sorted(base.glob("*.json")):
        try:
            meta = json.loads(meta_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        cwd = meta.get("cwd", "")
        if project and not matches_project(cwd, project):
            continue
        sid = meta.get("session_id", meta_file.stem)
        ts = meta.get("timestamp", "")
        if since and parse_iso(ts) < since:
            continue
        jsonl_file = meta_file.with_suffix(".jsonl")
        if not jsonl_file.exists():
            continue
        try:
            with open(jsonl_file) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    kind = entry.get("kind")
                    data = entry.get("data", {})

                    if kind == "Prompt":
                        texts = [c.get("text", "") for c in data.get("content", []) if c.get("kind") == "text"]
                        yield NormalizedEvent(
                            session_id=sid, tool="kiro-cli", project_path=cwd,
                            timestamp=ts, role="user", content="\n".join(texts) or None,
                            tool_name=None, tool_input=None, tool_output=None,
                            model=None, provider=None, tokens_in=None, tokens_out=None,
                            tokens_cache_read=None, tokens_cache_write=None,
                            cost=None, duration_ms=None,
                        )
                    elif kind == "AssistantMessage":
                        for c in data.get("content", []):
                            if c.get("kind") == "text":
                                yield NormalizedEvent(
                                    session_id=sid, tool="kiro-cli", project_path=cwd,
                                    timestamp=ts, role="assistant", content=c.get("text"),
                                    tool_name=None, tool_input=None, tool_output=None,
                                    model=None, provider=None, tokens_in=None, tokens_out=None,
                                    tokens_cache_read=None, tokens_cache_write=None,
                                    cost=None, duration_ms=None,
                                )
                            elif c.get("kind") == "toolUse":
                                yield NormalizedEvent(
                                    session_id=sid, tool="kiro-cli", project_path=cwd,
                                    timestamp=ts, role="assistant", content=None,
                                    tool_name=c.get("name"), tool_input=json.dumps(c.get("input")),
                                    tool_output=None, model=None, provider=None,
                                    tokens_in=None, tokens_out=None,
                                    tokens_cache_read=None, tokens_cache_write=None,
                                    cost=None, duration_ms=None,
                                )
                    elif kind == "ToolResults":
                        for c in data.get("content", []):
                            if c.get("kind") == "toolResult":
                                result_data = ""
                                try:
                                    result_data = c["data"]["content"][0]["data"]
                                except (KeyError, IndexError, TypeError):
                                    pass
                                yield NormalizedEvent(
                                    session_id=sid, tool="kiro-cli", project_path=cwd,
                                    timestamp=ts, role="tool_result", content=None,
                                    tool_name=None, tool_input=None,
                                    tool_output=truncate(str(result_data)),
                                    model=None, provider=None, tokens_in=None, tokens_out=None,
                                    tokens_cache_read=None, tokens_cache_write=None,
                                    cost=None, duration_ms=None,
                                )
        except (json.JSONDecodeError, OSError):
            continue


# --- Claude Code adapter ---

def claude_transcripts_dir() -> Path:
    return Path.home() / ".claude" / "transcripts"


def claude_history_file() -> Path:
    return Path.home() / ".claude" / "history.jsonl"


def _claude_project_map() -> dict[str, str]:
    """Build timestamp→project mapping from history."""
    mapping: dict[str, str] = {}
    hf = claude_history_file()
    if not hf.exists():
        return mapping
    try:
        with open(hf) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                proj = entry.get("project", "")
                ts = entry.get("timestamp", "")
                if proj and ts:
                    # Normalize timestamp to string
                    if isinstance(ts, (int, float)):
                        ts = ms_to_iso(ts) if ts > 1e12 else datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                    mapping[str(ts)] = proj
    except (json.JSONDecodeError, OSError):
        pass
    return mapping


def claude_list_sessions(project: str | None, since: datetime | None) -> Iterator[SessionMeta]:
    base = claude_transcripts_dir()
    if not base.exists():
        return
    proj_map = _claude_project_map()
    for f in sorted(base.glob("*.jsonl")):
        first_ts = ""
        session_project = ""
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    first_ts = entry.get("timestamp", "")
                    break
        except (json.JSONDecodeError, OSError):
            continue
        # Match project from history by finding closest timestamp
        if proj_map:
            for hist_ts, proj in proj_map.items():
                if hist_ts.startswith(first_ts[:10]):
                    session_project = proj
                    break
        if project and not matches_project(session_project, project):
            continue
        if since and parse_iso(first_ts) < since:
            continue
        yield SessionMeta(
            session_id=f.stem, tool="claude-code", project_path=session_project,
            timestamp=first_ts, title=None, model=None,
        )


def claude_ingest_all(project: str | None, since: datetime | None) -> Iterator[NormalizedEvent]:
    base = claude_transcripts_dir()
    if not base.exists():
        return
    proj_map = _claude_project_map()
    for f in sorted(base.glob("*.jsonl")):
        session_id = f.stem
        session_project = ""
        events: list[NormalizedEvent] = []
        skip = False
        try:
            with open(f) as fh:
                first = True
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    ts = entry.get("timestamp", "")
                    if first:
                        first = False
                        if proj_map:
                            for hist_ts, proj in proj_map.items():
                                if hist_ts.startswith(ts[:10]):
                                    session_project = proj
                                    break
                        if project and not matches_project(session_project, project):
                            skip = True
                            break
                        if since and parse_iso(ts) < since:
                            skip = True
                            break
                    etype = entry.get("type", "")
                    if etype == "user":
                        content = entry.get("content", "")
                        if isinstance(content, list):
                            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                        events.append(NormalizedEvent(
                            session_id=session_id, tool="claude-code", project_path=session_project,
                            timestamp=ts, role="user", content=content or None,
                            tool_name=None, tool_input=None, tool_output=None,
                            model=None, provider=None, tokens_in=None, tokens_out=None,
                            tokens_cache_read=None, tokens_cache_write=None,
                            cost=None, duration_ms=None,
                        ))
                    elif etype == "tool_use":
                        events.append(NormalizedEvent(
                            session_id=session_id, tool="claude-code", project_path=session_project,
                            timestamp=ts, role="assistant", content=None,
                            tool_name=entry.get("tool_name"), tool_input=json.dumps(entry.get("tool_input")),
                            tool_output=None, model=None, provider=None,
                            tokens_in=None, tokens_out=None,
                            tokens_cache_read=None, tokens_cache_write=None,
                            cost=None, duration_ms=None,
                        ))
                    elif etype == "tool_result":
                        output = entry.get("tool_output", {})
                        out_text = output.get("output", "") if isinstance(output, dict) else str(output)
                        events.append(NormalizedEvent(
                            session_id=session_id, tool="claude-code", project_path=session_project,
                            timestamp=ts, role="tool_result", content=None,
                            tool_name=entry.get("tool_name"), tool_input=None,
                            tool_output=truncate(out_text), model=None, provider=None,
                            tokens_in=None, tokens_out=None,
                            tokens_cache_read=None, tokens_cache_write=None,
                            cost=None, duration_ms=None,
                        ))
        except (json.JSONDecodeError, OSError):
            continue
        if not skip:
            yield from events


# --- opencode adapter ---

def opencode_db_path() -> Path:
    return Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def opencode_list_sessions(project: str | None, since: datetime | None) -> Iterator[SessionMeta]:
    db = opencode_db_path()
    if not db.exists():
        return
    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        if project:
            rows = conn.execute(
                "SELECT s.id, s.title, p.worktree, s.time_created FROM session s "
                "JOIN project p ON s.project_id = p.id WHERE p.worktree LIKE ?",
                (f"%{Path(project).name}%",)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT s.id, s.title, p.worktree, s.time_created FROM session s "
                "JOIN project p ON s.project_id = p.id"
            ).fetchall()
        for row in rows:
            ts = ms_to_iso(row["time_created"])
            if since and parse_iso(ts) < since:
                continue
            yield SessionMeta(
                session_id=row["id"], tool="opencode",
                project_path=row["worktree"] or "",
                timestamp=ts, title=row["title"], model=None,
            )
        conn.close()
    except (sqlite3.Error, OSError):
        return


def opencode_ingest_all(project: str | None, since: datetime | None) -> Iterator[NormalizedEvent]:
    db = opencode_db_path()
    if not db.exists():
        return
    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        if project:
            sessions = conn.execute(
                "SELECT s.id, p.worktree, s.time_created FROM session s "
                "JOIN project p ON s.project_id = p.id WHERE p.worktree LIKE ?",
                (f"%{Path(project).name}%",)
            ).fetchall()
        else:
            sessions = conn.execute(
                "SELECT s.id, p.worktree, s.time_created FROM session s "
                "JOIN project p ON s.project_id = p.id"
            ).fetchall()
        for sess in sessions:
            sid = sess["id"]
            worktree = sess["worktree"] or ""
            sess_ts = ms_to_iso(sess["time_created"])
            if since and parse_iso(sess_ts) < since:
                continue
            messages = conn.execute(
                "SELECT id, data, time_created FROM message WHERE session_id = ? ORDER BY time_created",
                (sid,)
            ).fetchall()
            for msg_row in messages:
                msg_data = json.loads(msg_row["data"]) if msg_row["data"] else {}
                role = msg_data.get("role", "user")
                model = msg_data.get("modelID")
                provider = msg_data.get("providerID")
                msg_tokens = msg_data.get("tokens", {})
                msg_cost = msg_data.get("cost")
                time_info = msg_data.get("time", {})
                msg_ts = ms_to_iso(msg_row["time_created"])

                parts = conn.execute(
                    "SELECT data, time_created FROM part WHERE message_id = ? ORDER BY time_created",
                    (msg_row["id"],)
                ).fetchall()
                for part_row in parts:
                    part_data = json.loads(part_row["data"]) if part_row["data"] else {}
                    ptype = part_data.get("type", "")
                    part_ts = ms_to_iso(part_row["time_created"])

                    if ptype == "text":
                        yield NormalizedEvent(
                            session_id=sid, tool="opencode", project_path=worktree,
                            timestamp=part_ts, role=role, content=part_data.get("text"),
                            tool_name=None, tool_input=None, tool_output=None,
                            model=model, provider=provider,
                            tokens_in=msg_tokens.get("input") if isinstance(msg_tokens, dict) else None,
                            tokens_out=msg_tokens.get("output") if isinstance(msg_tokens, dict) else None,
                            tokens_cache_read=None, tokens_cache_write=None,
                            cost=msg_cost, duration_ms=None,
                        )
                    elif ptype == "tool":
                        state = part_data.get("state", {})
                        yield NormalizedEvent(
                            session_id=sid, tool="opencode", project_path=worktree,
                            timestamp=part_ts, role="tool_result",
                            content=None,
                            tool_name=part_data.get("tool"),
                            tool_input=json.dumps(state.get("input")) if state.get("input") else None,
                            tool_output=truncate(str(state.get("output", ""))),
                            model=model, provider=provider,
                            tokens_in=None, tokens_out=None,
                            tokens_cache_read=None, tokens_cache_write=None,
                            cost=None, duration_ms=None,
                        )
                    elif ptype == "step-finish":
                        step_tokens = part_data.get("tokens", {})
                        step_cost = part_data.get("cost")
                        if step_tokens or step_cost:
                            yield NormalizedEvent(
                                session_id=sid, tool="opencode", project_path=worktree,
                                timestamp=part_ts, role="assistant", content=None,
                                tool_name=None, tool_input=None, tool_output=None,
                                model=model, provider=provider,
                                tokens_in=step_tokens.get("input") if isinstance(step_tokens, dict) else None,
                                tokens_out=step_tokens.get("output") if isinstance(step_tokens, dict) else None,
                                tokens_cache_read=None, tokens_cache_write=None,
                                cost=step_cost, duration_ms=None,
                            )
        conn.close()
    except (sqlite3.Error, OSError, json.JSONDecodeError):
        return


# --- Unified collection ---

TOOLS = ["oh-my-pi", "codex", "kiro-cli", "claude-code", "opencode"]


def collect_sessions(project: str | None, tool: str | None, since: datetime | None) -> list[SessionMeta]:
    adapters = {
        "oh-my-pi": omp_list_sessions,
        "codex": codex_list_sessions,
        "kiro-cli": kiro_list_sessions,
        "claude-code": claude_list_sessions,
        "opencode": opencode_list_sessions,
    }
    results: list[SessionMeta] = []
    tools = [tool] if tool else TOOLS
    for t in tools:
        if t in adapters:
            results.extend(adapters[t](project, since))
    results.sort(key=lambda s: s.timestamp or "")
    return results


def collect_events(project: str | None, tool: str | None, since: datetime | None) -> Iterator[NormalizedEvent]:
    adapters = {
        "oh-my-pi": omp_ingest_all,
        "codex": codex_ingest_all,
        "kiro-cli": kiro_ingest_all,
        "claude-code": claude_ingest_all,
        "opencode": opencode_ingest_all,
    }
    all_events: list[NormalizedEvent] = []
    tools = [tool] if tool else TOOLS
    for t in tools:
        if t in adapters:
            all_events.extend(adapters[t](project, since))
    all_events.sort(key=lambda e: e.timestamp or "")
    return iter(all_events)


# --- Summary ---

INTENT_KEYWORDS = {
    "bugs": ["error", "bug", "fix", "broken", "failing", "crash", "exception", "debug"],
    "features": ["add", "implement", "create", "build", "new", "feature"],
    "refactoring": ["refactor", "rename", "move", "extract", "clean up", "restructure"],
    "testing": ["test", "spec", "coverage", "assert", "mock"],
    "infrastructure": ["deploy", "terraform", "docker", "k8s", "ci", "cd", "pipeline", "aws", "gcp"],
    "research": ["research", "investigate", "compare", "analyze", "evaluate", "survey"],
    "documentation": ["doc", "readme", "comment", "explain", "document"],
}

INTENT_TO_CREW = {
    "bugs": "bug-fix",
    "features": "general",
    "refactoring": "general",
    "testing": "bug-fix",
    "infrastructure": "infrastructure",
    "research": "research",
    "documentation": "research",
}


def classify_intent(text: str) -> str:
    text_lower = text.lower()
    scores: Counter[str] = Counter()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[intent] += 1
    if scores:
        return scores.most_common(1)[0][0]
    return "mixed-work"


def summarize(events: list[NormalizedEvent]) -> dict:
    intent_dist: Counter[str] = Counter()
    tool_usage: Counter[str] = Counter()
    total_results = 0
    error_results = 0
    cost_total = 0.0
    tokens_total = 0
    sessions_by_tool: dict[str, set[str]] = {}
    session_times: dict[str, list[str]] = {}
    model_counter: Counter[str] = Counter()

    for ev in events:
        # Track sessions
        sessions_by_tool.setdefault(ev.tool, set()).add(ev.session_id)
        session_times.setdefault(ev.session_id, []).append(ev.timestamp)

        if ev.role == "user" and ev.content:
            intent_dist[classify_intent(ev.content)] += 1
        if ev.tool_name and ev.role == "assistant":
            tool_usage[ev.tool_name] += 1
        if ev.role == "tool_result":
            total_results += 1
            if ev.tool_output and "error" in (ev.tool_output or "").lower():
                error_results += 1
        if ev.cost:
            cost_total += ev.cost
        if ev.tokens_in:
            tokens_total += ev.tokens_in
        if ev.tokens_out:
            tokens_total += ev.tokens_out
        if ev.model:
            model_counter[ev.model] += 1

    # Avg session duration
    durations: list[float] = []
    for sid, times in session_times.items():
        sorted_times = sorted(t for t in times if t)
        if len(sorted_times) >= 2:
            start = parse_iso(sorted_times[0])
            end = parse_iso(sorted_times[-1])
            dur = (end - start).total_seconds()
            if dur > 0:
                durations.append(dur)
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Recommendations
    recommendations: list[str] = []
    if intent_dist:
        top_intent = intent_dist.most_common(1)[0][0]
        crew = INTENT_TO_CREW.get(top_intent, "general")
        recommendations.append(f"Primary intent is '{top_intent}' → consider '{crew}' crew")
    if error_results > 0 and total_results > 0:
        rate = error_results / total_results
        if rate > 0.3:
            recommendations.append(f"High failure rate ({rate:.0%}) → consider bug-fix crew")

    return {
        "intent_distribution": dict(intent_dist.most_common()),
        "tool_usage": dict(tool_usage.most_common(20)),
        "failure_rate": error_results / total_results if total_results else 0,
        "cost_total": round(cost_total, 4),
        "tokens_total": tokens_total,
        "sessions_by_tool": {k: len(v) for k, v in sessions_by_tool.items()},
        "avg_session_duration_seconds": round(avg_duration, 1),
        "top_models": dict(model_counter.most_common(10)),
        "recommendations": recommendations,
    }


# --- Output formatting ---

def output_list(sessions: list[SessionMeta]) -> None:
    if not sessions:
        print("No sessions found.")
        return
    # Aggregate by tool
    by_tool: dict[str, list[SessionMeta]] = {}
    for s in sessions:
        by_tool.setdefault(s.tool, []).append(s)

    print(f"{'Tool':<14}{'Sessions':<10}{'Latest':<22}{'Project'}")
    print("-" * 70)
    for tool_name in TOOLS:
        if tool_name not in by_tool:
            continue
        tool_sessions = by_tool[tool_name]
        latest = max(s.timestamp for s in tool_sessions) if tool_sessions else ""
        # Format timestamp
        latest_fmt = latest[:16].replace("T", " ") if latest else "unknown"
        # Get most common project
        projects: Counter[str] = Counter()
        for s in tool_sessions:
            proj = Path(s.project_path).name if s.project_path else "unknown"
            projects[proj] += 1
        top_proj = projects.most_common(1)[0][0] if projects else "unknown"
        print(f"{tool_name:<14}{len(tool_sessions):<10}{latest_fmt:<22}{top_proj}")


def output_jsonl(events: Iterator[NormalizedEvent]) -> None:
    for ev in events:
        print(json.dumps(asdict(ev)))


def output_summary(events: list[NormalizedEvent]) -> None:
    stats = summarize(events)
    print("=== Session Ingest Summary ===\n")
    print(f"Sessions by tool:")
    for tool_name, count in stats["sessions_by_tool"].items():
        print(f"  {tool_name}: {count}")
    print(f"\nTotal tokens: {stats['tokens_total']:,}")
    sessions_count = sum(stats["sessions_by_tool"].values())
    if sessions_count > 0:
        print(f"Tokens/session: {stats['tokens_total'] // sessions_count:,}")
    print(f"Cost (derived): ${stats['cost_total']:.4f}")
    print(f"Avg session duration: {stats['avg_session_duration_seconds']:.0f}s")
    print(f"Tool failure rate: {stats['failure_rate']:.1%}")
    print(f"\nIntent distribution:")
    for intent, count in stats["intent_distribution"].items():
        print(f"  {intent}: {count}")
    print(f"\nTop tool calls:")
    for name, count in list(stats["tool_usage"].items())[:10]:
        print(f"  {name}: {count}")
    print(f"\nTop models:")
    for model, count in stats["top_models"].items():
        print(f"  {model}: {count}")
    if stats["recommendations"]:
        print(f"\nRecommendations:")
        for rec in stats["recommendations"]:
            print(f"  • {rec}")


def do_ingest(project_path: str, project: str | None, tool: str | None, since: datetime | None) -> None:
    resolved = Path(project_path).expanduser().resolve()
    project_name = resolved.name
    out_dir = Path("scratch/sessions") / project_name
    out_dir.mkdir(parents=True, exist_ok=True)

    events = list(collect_events(str(resolved), tool, since))
    # Write all.jsonl
    with open(out_dir / "all.jsonl", "w") as fh:
        for ev in events:
            fh.write(json.dumps(asdict(ev)) + "\n")
    # Write summary.json
    stats = summarize(events)
    with open(out_dir / "summary.json", "w") as fh:
        json.dump(stats, fh, indent=2)
    print(f"Ingested {len(events)} events → {out_dir}/")
    print(f"  all.jsonl: {len(events)} events")
    print(f"  summary.json: {len(stats['sessions_by_tool'])} tools, {stats['tokens_total']:,} tokens")


# --- CLI ---

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest session logs from AI coding tools")
    parser.add_argument("--project", help="Filter to sessions for this project path")
    parser.add_argument("--tool", choices=TOOLS, help="Only ingest from this tool")
    parser.add_argument("--since", help="Only sessions since (e.g. 7d, 24h, 30m)")
    parser.add_argument("--output", choices=["list", "jsonl", "summary"], default="list",
                        help="Output format (default: list)")
    parser.add_argument("--ingest", metavar="PATH", help="Write normalized data to scratch/sessions/<project>/")
    args = parser.parse_args()

    since = parse_since(args.since) if args.since else None
    project = str(Path(args.project).expanduser().resolve()) if args.project else None

    if args.ingest:
        do_ingest(args.ingest, project, args.tool, since)
        return

    if args.output == "list":
        sessions = collect_sessions(project, args.tool, since)
        output_list(sessions)
    elif args.output == "jsonl":
        events = collect_events(project, args.tool, since)
        output_jsonl(events)
    elif args.output == "summary":
        events = list(collect_events(project, args.tool, since))
        output_summary(events)


if __name__ == "__main__":
    main()
