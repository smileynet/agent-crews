#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Analyze kiro-cli session transcripts for agent team improvement.

Usage:
    uv run analyze-session.py                          # list recent sessions
    uv run analyze-session.py <session-id>             # analyze specific session
    uv run analyze-session.py --project <path>         # sessions for a project dir
    uv run analyze-session.py <session-id> --transcript  # readable transcript
    uv run analyze-session.py <session-id> --stats     # tool/agent statistics
    uv run analyze-session.py <session-id> --validate  # check live testing compliance
    uv run analyze-session.py <session-id> --compliance # crew behavioral rules check
    uv run analyze-session.py <session-id> --antipatterns # detect measurable anti-patterns
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


def main():
    args = sys.argv[1:]

    if not args:
        list_sessions()
        return

    if args[0] == "--project":
        list_sessions(project_filter=args[1] if len(args) > 1 else None)
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
