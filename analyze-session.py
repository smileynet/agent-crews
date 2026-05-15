#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Analyze session transcripts for agent team improvement.

Usage:
    uv run analyze-session.py                              # list recent sessions
    uv run analyze-session.py <session-id>                 # analyze specific session
    uv run analyze-session.py --project <path>             # sessions for a project dir
    uv run analyze-session.py <session-id> --transcript    # readable transcript
    uv run analyze-session.py <session-id> --stats         # tool/agent statistics
    uv run analyze-session.py <session-id> --validate      # check live testing compliance
    uv run analyze-session.py <session-id> --compliance    # crew behavioral rules check
    uv run analyze-session.py <session-id> --antipatterns  # detect measurable anti-patterns
    uv run analyze-session.py --normalized <file.jsonl>    # analyze normalized multi-tool data
    uv run analyze-session.py --compare <project-path>     # cross-tool performance comparison
    uv run analyze-session.py --agent-distribution <name>  # agent usage breakdown
    uv run analyze-session.py --bypass-report <name>       # detect crew bypass patterns
    uv run analyze-session.py --clusters <name>            # workflow clusters by timestamp
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime

SESSIONS_DIR = Path.home() / ".kiro" / "sessions" / "cli"

# Anti-pattern thresholds
FILE_READ_THRESHOLD = 3
SHELL_RETRY_THRESHOLD = 3


def list_sessions(project_filter=None, limit=20):
    """List recent sessions, optionally filtered by project directory."""
    if not SESSIONS_DIR.exists():
        sys.exit(f"Sessions directory not found: {SESSIONS_DIR}")

    sessions = []
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            with open(f) as fh:
                meta = json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue
        if project_filter and project_filter not in meta.get("cwd", ""):
            continue
        sessions.append(meta)

    sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    print(f"{'ID':<38} {'Updated':<20} {'Agent':<12} {'Dir':<20} Title")
    print("-" * 120)
    for s in sessions[:limit]:
        sid = s.get("session_id", "?")[:36]
        updated = s.get("updated_at", "")[:19].replace("T", " ")
        cwd = s.get("cwd", "")
        cwd_short = cwd.split("/")[-1] if cwd else "?"
        agent = s.get("session_state", {}).get("agent_name", None) or "default"
        title = (s.get("title") or "")[:40]
        print(f"{sid}  {updated}  {agent:<12} {cwd_short:<20} {title}")


def parse_session(session_id):
    """Parse a session JSONL into structured entries."""
    jsonl_path = SESSIONS_DIR / f"{session_id}.jsonl"
    if not jsonl_path.exists():
        sys.exit(f"Not found: {jsonl_path}")

    entries = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def _parse_content(data):
    """Safely parse content field from AssistantMessage data."""
    content = data.get("content", [])
    if isinstance(content, list):
        return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return [{"kind": "text", "data": content}]
    return []


def extract_transcript(entries):
    """Extract a human-readable transcript from session entries."""
    lines = []
    for entry in entries:
        kind = entry.get("kind")
        data = entry.get("data", {})

        if kind == "Prompt":
            content = data.get("content", [])
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except (json.JSONDecodeError, ValueError):
                    content = [{"kind": "text", "data": content}]
            for item in content:
                if isinstance(item, dict) and item.get("kind") == "text":
                    text = item.get("data", "").strip()
                    if text:
                        lines.append(f"\n## USER\n{text}\n")

        elif kind == "AssistantMessage":
            content = _parse_content(data)
            for item in content:
                if isinstance(item, dict):
                    if item.get("kind") == "text" and item.get("data", "").strip():
                        lines.append(f"\n**AGENT:** {item['data'].strip()}\n")
                    elif item.get("kind") == "toolUse":
                        td = item.get("data", {})
                        name = td.get("name", "?")
                        purpose = td.get("input", {}).get("__tool_use_purpose", "")
                        lines.append(f"  → `{name}`: {purpose}")

    return "\n".join(lines)


def compute_stats(entries):
    """Compute statistics about tool usage, agent behavior, session shape."""
    tools_used = {}
    user_prompts = 0
    assistant_messages = 0
    tool_calls = 0
    subagent_calls = 0

    for entry in entries:
        kind = entry.get("kind")
        data = entry.get("data", {})

        if kind == "Prompt":
            user_prompts += 1

        elif kind == "AssistantMessage":
            assistant_messages += 1
            content = _parse_content(data)
            for item in content:
                if isinstance(item, dict) and item.get("kind") == "toolUse":
                    tool_calls += 1
                    td = item.get("data", {})
                    name = td.get("name", "?")
                    tools_used[name] = tools_used.get(name, 0) + 1
                    if name == "subagent":
                        subagent_calls += 1

    print(f"User prompts:      {user_prompts}")
    print(f"Assistant messages: {assistant_messages}")
    print(f"Tool calls:        {tool_calls}")
    print(f"Subagent calls:    {subagent_calls}")
    print(f"Turns ratio:       {assistant_messages / max(user_prompts, 1):.1f} assistant msgs per user prompt")
    print(f"\nTool usage:")
    for tool, count in sorted(tools_used.items(), key=lambda x: -x[1]):
        print(f"  {tool:<40} {count}")


def validate_testing(entries):
    """Check if builder ran live tests. Flags sessions that skipped validation."""
    test_indicators = re.compile(
        r'terraform (validate|plan|apply)|pytest|npm test|cargo test|'
        r'go test|jest|vitest|make test|just test|mise run test|'
        r'cdk (synth|diff|deploy)|sam (build|validate)|'
        r'python -m (pytest|unittest)|npx (jest|vitest|mocha)',
        re.IGNORECASE
    )
    blocked_indicators = re.compile(r'⚠️ BLOCKED|BLOCKED.*credential|credential.*BLOCKED', re.IGNORECASE)
    wrote_tests = re.compile(r'(wrote|added|created|implemented).{0,20}test', re.IGNORECASE)

    shell_commands = []
    blocked = False
    evidence_of_tests_written = False
    evidence_of_tests_run = False

    for entry in entries:
        kind = entry.get("kind")
        data = entry.get("data", {})

        if kind == "AssistantMessage":
            content = _parse_content(data)
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("kind") == "text":
                    text = item.get("data", "")
                    if blocked_indicators.search(text):
                        blocked = True
                    if wrote_tests.search(text):
                        evidence_of_tests_written = True
                elif item.get("kind") == "toolUse":
                    td = item.get("data", {})
                    if td.get("name") == "shell":
                        cmd = td.get("input", {}).get("command", "")
                        shell_commands.append(cmd)
                        if test_indicators.search(cmd):
                            evidence_of_tests_run = True

        elif kind == "ToolResults":
            results = data if isinstance(data, list) else [data]
            for r in results:
                output = str(r.get("data", ""))
                if re.search(r'(\d+ passed|PASS|OK|tests? (passed|succeeded))', output):
                    evidence_of_tests_run = True

    print("## Live Testing Compliance\n")

    if evidence_of_tests_run:
        print("✅ PASS — Evidence of live test execution found")
        matching = [c for c in shell_commands if test_indicators.search(c)]
        for cmd in matching[:5]:
            print(f"   ran: {cmd[:100]}")
    elif blocked:
        print("⚠️  BLOCKED — Agent signaled it couldn't test (credentials/env)")
        print("   This is acceptable IF the blocker was communicated to the user.")
    elif evidence_of_tests_written:
        print("❌ FAIL — Tests were written but NOT executed")
        print("   Builder claimed to write tests but no test command was run.")
        print("   Reviewer should have caught this.")
    else:
        print("❌ FAIL — No evidence of live testing")
        print(f"   Shell commands executed: {len(shell_commands)}")
        print("   None matched known test patterns.")

    print(f"\n   Total shell commands: {len(shell_commands)}")
    print(f"   Tests written (claimed): {evidence_of_tests_written}")
    print(f"   Tests run (confirmed): {evidence_of_tests_run}")
    print(f"   Blocked signal: {blocked}")


def _extract_session_signals(entries):
    """Extract structured signals from session entries for compliance/antipattern checks."""
    shell_commands = []
    shell_by_agent = Counter()
    file_reads = Counter()
    subagent_calls = 0
    all_text = []
    tool_uses = []
    current_agent = "lead"  # assume top-level is orchestrator/lead

    for entry in entries:
        kind = entry.get("kind")
        data = entry.get("data", {})

        if kind == "AgentSwitch":
            current_agent = data.get("agent_name", "unknown")

        elif kind == "AssistantMessage":
            content = _parse_content(data)
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("kind") == "text":
                    all_text.append(item.get("data", ""))
                elif item.get("kind") == "toolUse":
                    td = item.get("data", {})
                    name = td.get("name", "?")
                    inp = td.get("input", {})
                    tool_uses.append({"name": name, "input": inp, "agent": current_agent})

                    if name == "shell":
                        cmd = inp.get("command", "")
                        shell_commands.append(cmd)
                        shell_by_agent[current_agent] += 1
                    elif name == "subagent":
                        subagent_calls += 1
                    elif name == "read":
                        # Track file reads by path
                        path = inp.get("path", "")
                        ops = inp.get("operations", [])
                        if path:
                            file_reads[Path(path).name] += 1
                        for op in ops:
                            p = op.get("path", "")
                            if p:
                                file_reads[Path(p).name] += 1

    full_text = "\n".join(all_text)
    return {
        "shell_commands": shell_commands,
        "shell_by_agent": shell_by_agent,
        "file_reads": file_reads,
        "subagent_calls": subagent_calls,
        "all_text": all_text,
        "full_text": full_text,
        "tool_uses": tool_uses,
        "current_agent": current_agent,
    }


def detect_antipatterns(entries):
    """Detect measurable anti-patterns and report with severity levels."""
    signals = _extract_session_signals(entries)
    issues_critical = 0
    issues_warning = 0

    print("## Anti-Pattern Analysis\n")

    # --- Token Waste: repeated file reads ---
    print("### Token Waste")
    repeated = {f: c for f, c in signals["file_reads"].items() if c > FILE_READ_THRESHOLD}
    if repeated:
        for fname, count in sorted(repeated.items(), key=lambda x: -x[1]):
            print(f"⚠️  {fname} read {count} times (threshold: {FILE_READ_THRESHOLD})")
            issues_warning += 1
    else:
        print("✅  No excessive file re-reads detected")
    print()

    # --- Protocol Gaps ---
    print("### Protocol Gaps")
    full_text = signals["full_text"]

    # Sanity gate: DONE signal or Asked/Delivered/Match
    has_done = bool(re.search(r'## DONE|## BLOCKED|## FAILED', full_text))
    has_sanity = bool(re.search(r'Asked:.*\nDelivered:.*\nMatch:', full_text, re.MULTILINE))
    if has_done or has_sanity:
        print("✅  Structured DONE/sanity signal found")
    else:
        print("❌  No structured DONE signal found")
        issues_critical += 1

    # Slack notification
    has_slack = any(
        "slack" in tu["input"].get("command", "").lower()
        for tu in signals["tool_uses"] if tu["name"] == "shell"
    ) or "slack-notify" in full_text.lower() or "slack_notify" in full_text.lower()
    if has_slack:
        print("✅  Slack notification sent")
    else:
        print("❌  No Slack notification sent")
        issues_critical += 1

    # Git push
    has_push = any(
        "git push" in cmd for cmd in signals["shell_commands"]
    )
    has_push_blocked = bool(re.search(r'BLOCKED.{0,80}(push|remote|upstream)', full_text, re.IGNORECASE))
    if has_push or has_push_blocked:
        print("✅  Git push attempted (or BLOCKED reported)")
    else:
        print("❌  No push attempt — session ends without git push or BLOCKED signal")
        issues_critical += 1
    print()

    # --- Role Violations ---
    print("### Role Violations")

    # Orchestrator shell usage (lead/orchestrator should not run shell)
    orchestrator_names = {"lead", "orchestrator", "unknown"}
    orch_shells = sum(
        count for agent, count in signals["shell_by_agent"].items()
        if agent.lower() in orchestrator_names
    )
    if orch_shells == 0:
        print("✅  No orchestrator shell commands")
    else:
        print(f"❌  Orchestrator ran {orch_shells} shell commands (should be 0)")
        issues_critical += 1

    # Subagent tool confusion: subagent (non-lead) using grep/glob/code tools
    confused_tools = {"grep", "glob", "code"}
    confusion_count = sum(
        1 for tu in signals["tool_uses"]
        if tu["name"] in confused_tools and tu["agent"].lower() not in orchestrator_names
    )
    if confusion_count == 0:
        print("✅  No subagent tool confusion detected")
    else:
        print(f"⚠️  Subagent used grep/glob/code {confusion_count} time(s) (may fail)")
        issues_warning += 1
    print()

    # --- Retry Loops ---
    print("### Retry Loops")
    cmd_counts = Counter(signals["shell_commands"])
    retries = {cmd: c for cmd, c in cmd_counts.items() if c >= SHELL_RETRY_THRESHOLD}
    if retries:
        for cmd, count in sorted(retries.items(), key=lambda x: -x[1]):
            print(f"⚠️  `{cmd[:80]}` retried {count} times (threshold: {SHELL_RETRY_THRESHOLD})")
            issues_warning += 1
    else:
        print("✅  No shell retry loops detected")
    print()

    # --- Summary ---
    total = issues_critical + issues_warning
    print(f"## Summary: {total} issues found ({issues_critical} ❌ critical, {issues_warning} ⚠️ warning)")
    return total


def check_compliance(entries):
    """Check session compliance with crew behavioral rules (includes anti-pattern checks)."""
    signals = _extract_session_signals(entries)
    full_text = signals["full_text"]

    print("## Crew Compliance Check\n")

    # --- Orchestrator behavior ---
    orchestrator_names = {"lead", "orchestrator", "unknown"}
    lead_shells = sum(
        count for agent, count in signals["shell_by_agent"].items()
        if agent.lower() in orchestrator_names
    )
    if lead_shells == 0:
        print("✅ Lead: No shell commands (delegation-only)")
    else:
        print(f"❌ Lead: Ran {lead_shells} shell commands (should be 0)")

    if signals["subagent_calls"] > 0:
        print(f"✅ Lead: Used subagent {signals['subagent_calls']} time(s)")
    else:
        print("⚠️  Lead: No subagent calls (may be simple task or direct agent use)")

    # Narration
    has_plan = bool(re.search(r'## Plan|⏳', full_text))
    has_narration = bool(re.search(r'✅.*complete|⏳.*Delegat|## Summary', full_text))
    if has_plan or has_narration:
        print("✅ Lead: Narration detected")
    else:
        print("⚠️  Lead: No narration detected")

    # Structured signals
    has_done = bool(re.search(r'## DONE|## BLOCKED|## FAILED', full_text))
    if has_done:
        print("✅ Workers: Structured signals (DONE/BLOCKED/FAILED)")
    else:
        print("❌ Workers: No structured signals found")

    # --- Anti-pattern integration ---
    print("\n### Anti-Pattern Summary")

    # Repeated reads
    repeated = {f: c for f, c in signals["file_reads"].items() if c > FILE_READ_THRESHOLD}
    if repeated:
        for fname, count in sorted(repeated.items(), key=lambda x: -x[1])[:3]:
            print(f"  ⚠️  {fname} read {count}x (>{FILE_READ_THRESHOLD})")

    # Retry loops
    cmd_counts = Counter(signals["shell_commands"])
    retries = {cmd: c for cmd, c in cmd_counts.items() if c >= SHELL_RETRY_THRESHOLD}
    if retries:
        for cmd, count in sorted(retries.items(), key=lambda x: -x[1])[:3]:
            print(f"  ⚠️  `{cmd[:60]}` retried {count}x")

    # Push check
    has_push = any("git push" in cmd for cmd in signals["shell_commands"])
    has_push_blocked = bool(re.search(r'BLOCKED.{0,80}(push|remote|upstream)', full_text, re.IGNORECASE))
    if not has_push and not has_push_blocked:
        print("  ❌ No git push or BLOCKED signal about remote")

    # Slack
    has_slack = any(
        "slack" in tu["input"].get("command", "").lower()
        for tu in signals["tool_uses"] if tu["name"] == "shell"
    ) or "slack-notify" in full_text.lower()
    if not has_slack:
        print("  ❌ No Slack notification sent")

    if not repeated and not retries and (has_push or has_push_blocked) and has_slack:
        print("  ✅ No anti-patterns detected")

    print(f"\n   Shell by agent: {dict(signals['shell_by_agent'])}")
    print(f"   Subagent calls: {signals['subagent_calls']}")


def analyze_normalized(filepath):
    """Analyze pre-normalized JSONL from session-ingest.py."""
    events = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not events:
        sys.exit("No events found in normalized file.")

    sessions = set(e["session_id"] for e in events)
    tools = Counter(e["tool"] for e in events)
    user_msgs = [e for e in events if e["role"] == "user"]
    tool_calls = [e for e in events if e["role"] == "assistant" and e.get("tool_name")]
    tool_results = [e for e in events if e["role"] == "tool_result"]
    tokens_in = sum(e.get("tokens_in") or 0 for e in events)
    tokens_out = sum(e.get("tokens_out") or 0 for e in events)
    total_tokens = tokens_in + tokens_out

    # Tool usage
    tool_usage = Counter(e["tool_name"] for e in tool_calls if e.get("tool_name"))

    # Failure detection
    failures = sum(1 for e in tool_results if e.get("tool_output") and "error" in (e["tool_output"] or "").lower())
    failure_rate = failures / len(tool_results) if tool_results else 0

    # Models
    models = Counter(e["model"] for e in events if e.get("model"))

    print(f"=== NORMALIZED ANALYSIS ===")
    print(f"")
    print(f"Sessions: {len(sessions)}")
    print(f"Events: {len(events)}")
    print(f"Sources: {dict(tools)}")
    print(f"")
    print(f"Tokens: {total_tokens:,} (in: {tokens_in:,}, out: {tokens_out:,})")
    print(f"Tokens/session: {total_tokens // max(len(sessions), 1):,}")
    print(f"")
    print(f"User messages: {len(user_msgs)}")
    print(f"Tool calls: {len(tool_calls)}")
    print(f"Tool results: {len(tool_results)}")
    print(f"Failure rate: {failure_rate:.1%}")
    print(f"")
    print(f"Top tools:")
    for name, count in tool_usage.most_common(10):
        print(f"  {name:<20} {count}")
    print(f"")
    print(f"Models:")
    for model, count in models.most_common(5):
        print(f"  {model:<30} {count}")


def compare_tools(project_path):
    """Cross-tool comparison for a project. Runs session-ingest and compares."""
    import subprocess
    resolved = str(Path(project_path).expanduser().resolve())
    project_name = Path(resolved).name

    # Run session-ingest to get data
    result = subprocess.run(
        ["uv", "run", "session-ingest.py", "--project", resolved, "--since", "30d", "--output", "jsonl"],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        sys.exit(f"session-ingest failed: {result.stderr}")

    events = []
    for line in result.stdout.strip().split("\n"):
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not events:
        sys.exit(f"No sessions found for {project_name}")

    # Group by tool
    by_tool = {}
    for e in events:
        by_tool.setdefault(e["tool"], []).append(e)

    print(f"=== CROSS-TOOL COMPARISON: {project_name} (last 30 days) ===")
    print(f"")
    print(f"{'Tool':<14}{'Sessions':<10}{'Tokens':<12}{'Tok/Sess':<12}{'Tools':<8}{'Failures':<10}{'Top Model'}")
    print("-" * 85)

    for tool_name in ["oh-my-pi", "codex", "kiro-cli", "claude-code", "opencode"]:
        if tool_name not in by_tool:
            continue
        tool_events = by_tool[tool_name]
        sessions = set(e["session_id"] for e in tool_events)
        tokens = sum((e.get("tokens_in") or 0) + (e.get("tokens_out") or 0) for e in tool_events)
        tok_per_sess = tokens // max(len(sessions), 1)
        tool_calls = sum(1 for e in tool_events if e["role"] == "assistant" and e.get("tool_name"))
        results = [e for e in tool_events if e["role"] == "tool_result"]
        failures = sum(1 for e in results if e.get("tool_output") and "error" in (e["tool_output"] or "").lower())
        fail_pct = f"{failures}/{len(results)}" if results else "0/0"
        models = Counter(e["model"] for e in tool_events if e.get("model"))
        top_model = models.most_common(1)[0][0] if models else "-"
        # Truncate model name
        top_model = top_model[:20] if len(top_model) > 20 else top_model

        tok_str = f"{tokens // 1000}K" if tokens > 0 else "-"
        tps_str = f"{tok_per_sess // 1000}K" if tok_per_sess > 0 else "-"

        print(f"{tool_name:<14}{len(sessions):<10}{tok_str:<12}{tps_str:<12}{tool_calls:<8}{fail_pct:<10}{top_model}")

    # Intent comparison
    print(f"")
    print(f"Intent by tool:")
    intent_keywords = {
        "bugs": ["error", "bug", "fix", "broken", "failing", "crash", "debug"],
        "features": ["add", "implement", "create", "build", "new", "feature"],
        "refactoring": ["refactor", "rename", "move", "extract", "restructure"],
        "testing": ["test", "spec", "coverage", "assert"],
        "research": ["research", "investigate", "compare", "analyze", "survey"],
    }
    for tool_name in ["oh-my-pi", "codex", "kiro-cli", "claude-code", "opencode"]:
        if tool_name not in by_tool:
            continue
        user_msgs = [e["content"] for e in by_tool[tool_name] if e["role"] == "user" and e.get("content")]
        intents = Counter()
        for msg in user_msgs:
            msg_lower = msg.lower()
            matched = False
            for intent, kws in intent_keywords.items():
                if any(kw in msg_lower for kw in kws):
                    intents[intent] += 1
                    matched = True
                    break
            if not matched:
                intents["other"] += 1
        if intents:
            top = ", ".join(f"{k}:{v}" for k, v in intents.most_common(3))
            print(f"  {tool_name:<14}{top}")


def _load_project_sessions(project_filter):
    """Load all session metadata for a project."""
    sessions = []
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            with open(f) as fh:
                d = json.load(fh)
            if project_filter and project_filter not in d.get("cwd", ""):
                continue
            sessions.append(d)
        except (json.JSONDecodeError, OSError):
            continue
    sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return sessions


def agent_distribution(project_filter):
    """Show which agents handle sessions for a project."""
    sessions = _load_project_sessions(project_filter)
    if not sessions:
        sys.exit(f"No sessions found for: {project_filter}")

    agents = Counter()
    for s in sessions:
        agent = s.get("session_state", {}).get("agent_name", None) or "default"
        agents[agent] += 1

    total = sum(agents.values())
    print(f"=== Agent Distribution: {project_filter} ({total} sessions) ===\n")
    for agent, count in agents.most_common():
        pct = count / total * 100
        bar = "█" * round(pct / 5)
        print(f"  {agent:<20} {count:>4} ({pct:4.1f}%) {bar}")


def bypass_report(project_filter):
    """Detect work that should route through crew but used default agent."""
    sessions = _load_project_sessions(project_filter)
    if not sessions:
        sys.exit(f"No sessions found for: {project_filter}")

    # Intent-to-crew mapping
    intent_crew_map = {
        "create": "build-lead",
        "build": "build-lead",
        "generate": "build-lead",
        "research": "build-lead",
        "add ": "build-lead",
        "implement": "build-lead",
        "phase": "build-lead",
        "analyze": "ops-lead",
        "review": "ops-lead",
        "session": "ops-lead",
        "tune": "ops-lead",
        "validate": "ops-lead",
        "verify": "ops-lead",
        "check": "ops-lead",
        "consistency": "ops-lead",
        "fix": "bugfix-lead",
        "debug": "bugfix-lead",
        "error": "bugfix-lead",
        "broken": "bugfix-lead",
        "release": "crew-releaser",
        "version": "crew-releaser",
        "changelog": "crew-releaser",
        "tag": "crew-releaser",
        "push": "crew-releaser",
    }

    # Routing table patterns (from dispatcher)
    routing_patterns = {
        "crew for": "build-lead",
        "agent": "build-lead",
        "feature": "build-lead",
        "best practice": "build-lead",
        "pattern": "build-lead",
        "diagnose": "ops-lead",
        "health": "ops-lead",
        "performance": "ops-lead",
        "drift": "ops-lead",
        "kiro": "kiro-helper",
        "mcp": "kiro-helper",
        "cli": "kiro-helper",
    }

    bypassed = Counter()
    direct_exec = 0
    uncategorized = 0
    total_default = 0

    for s in sessions:
        agent = s.get("session_state", {}).get("agent_name", None) or "default"
        if agent != "default":
            continue
        total_default += 1
        title = (s.get("title") or "").lower()

        # Check if it's a direct command (appropriate bypass)
        if any(title.startswith(p) for p in ["run ", "1. ", "```", "git "]) or "write the file" in title:
            direct_exec += 1
            continue

        # Check intent mapping
        intent_match = None
        for keyword, crew in intent_crew_map.items():
            if keyword in title:
                intent_match = crew
                break

        # Check routing patterns
        routing_match = None
        for pattern, crew in routing_patterns.items():
            if pattern in title:
                routing_match = crew
                break

        # Combine signals
        if intent_match and routing_match and intent_match == routing_match:
            bypassed[intent_match] += 1  # high confidence
        elif intent_match:
            bypassed[intent_match] += 1  # intent signal alone
        elif routing_match:
            bypassed[routing_match] += 1  # routing signal alone
        else:
            uncategorized += 1

    total = len(sessions)
    crew_sessions = total - total_default
    bypass_total = sum(bypassed.values())

    print(f"=== Crew Bypass Report: {project_filter} ===\n")
    print(f"Sessions using crew agents: {crew_sessions}/{total} ({crew_sessions/total*100:.0f}%)")
    print(f"Sessions bypassing crew:    {bypass_total}/{total} ({bypass_total/total*100:.0f}%)")
    print()
    print("Work that should route to:")
    for crew, count in bypassed.most_common():
        print(f"  {crew:<20} {count:>3} sessions")
    print()
    print(f"Direct execution (appropriate bypass): {direct_exec} sessions")
    print(f"Uncategorized: {uncategorized} sessions")

    if bypass_total > total * 0.3:
        print(f"\n⚠️  High bypass rate ({bypass_total/total*100:.0f}%). Reduce routing friction.")


def clusters(project_filter):
    """Group sessions into workflow clusters by timestamp proximity."""
    sessions = _load_project_sessions(project_filter)
    if not sessions:
        sys.exit(f"No sessions found for: {project_filter}")

    # Parse timestamps and cluster (5-min gap = new cluster)
    clustered = []
    current_cluster = []

    for s in sessions:
        updated = s.get("updated_at", "")
        try:
            t = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

        agent = s.get("session_state", {}).get("agent_name", None) or "default"
        title = (s.get("title") or "")[:60]

        if current_cluster:
            prev_time = current_cluster[-1][0]
            if (prev_time - t).total_seconds() > 300:
                clustered.append(current_cluster)
                current_cluster = []

        current_cluster.append((t, agent, title))

    if current_cluster:
        clustered.append(current_cluster)

    # Show clusters with >1 session
    print(f"=== Workflow Clusters: {project_filter} (recent) ===\n")
    shown = 0
    for cluster in clustered:
        if len(cluster) < 2:
            continue
        shown += 1
        if shown > 10:
            break

        span = (cluster[0][0] - cluster[-1][0]).total_seconds()
        span_fmt = f"{span/3600:.1f}h" if span >= 3600 else f"{span/60:.0f}min"
        agents = Counter(a for _, a, _ in cluster)
        agents_str = ", ".join(f"{a}({c})" for a, c in agents.most_common())

        print(f"Cluster {shown} ({len(cluster)} sessions, {span_fmt} span):")
        print(f"  Agents: {agents_str}")
        for _, agent, title in cluster[:5]:
            print(f"    [{agent}] {title}")
        if len(cluster) > 5:
            print(f"    ... +{len(cluster)-5} more")
        print()


def main():
    args = sys.argv[1:]

    if not args:
        list_sessions()
        return

    if args[0] == "--project":
        list_sessions(project_filter=args[1] if len(args) > 1 else None)
        return

    if args[0] == "--agent-distribution":
        if len(args) < 2:
            sys.exit("Usage: analyze-session.py --agent-distribution <project-name>")
        agent_distribution(args[1])
        return

    if args[0] == "--bypass-report":
        if len(args) < 2:
            sys.exit("Usage: analyze-session.py --bypass-report <project-name>")
        bypass_report(args[1])
        return

    if args[0] == "--clusters":
        if len(args) < 2:
            sys.exit("Usage: analyze-session.py --clusters <project-name>")
        clusters(args[1])
        return

    if args[0] == "--normalized":
        if len(args) < 2:
            sys.exit("Usage: analyze-session.py --normalized <file.jsonl>")
        analyze_normalized(args[1])
        return

    if args[0] == "--compare":
        if len(args) < 2:
            sys.exit("Usage: analyze-session.py --compare <project-path>")
        compare_tools(args[1])
        return

    session_id = args[0]
    # Allow partial ID match
    if len(session_id) < 36:
        matches = list(SESSIONS_DIR.glob(f"{session_id}*.json"))
        if not matches:
            sys.exit(f"No session matching: {session_id}")
        session_id = matches[0].stem

    entries = parse_session(session_id)

    if "--transcript" in args:
        print(extract_transcript(entries))
    elif "--stats" in args:
        compute_stats(entries)
    elif "--validate" in args:
        validate_testing(entries)
    elif "--compliance" in args:
        check_compliance(entries)
    elif "--antipatterns" in args:
        detect_antipatterns(entries)
    else:
        # Default: show both summary stats and brief transcript
        meta_path = SESSIONS_DIR / f"{session_id}.json"
        if meta_path.exists():
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                print(f"Session: {meta.get('session_id')}")
                print(f"Project: {meta.get('cwd')}")
                print(f"Created: {meta.get('created_at', '')[:19]}")
                print(f"Updated: {meta.get('updated_at', '')[:19]}")
                print(f"Title:   {meta.get('title', '(none)')}")
                print()
            except (json.JSONDecodeError, OSError):
                pass

        compute_stats(entries)


if __name__ == "__main__":
    main()
