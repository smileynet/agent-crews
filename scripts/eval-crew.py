#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Model-based crew evaluation runner.

Usage:
    uv run scripts/eval-crew.py              # run all evals
    uv run scripts/eval-crew.py --tag routing  # filter by tag
    uv run scripts/eval-crew.py --name dispatcher-routes-augment  # single eval
    uv run scripts/eval-crew.py --threshold 4  # override pass threshold
    uv run scripts/eval-crew.py --dry-run      # show what would run
    uv run scripts/eval-crew.py --verbose      # show full output
    uv run scripts/eval-crew.py --timeout 600   # longer timeout
    uv run scripts/eval-crew.py --intent-only    # check delegation intent only (30s timeout)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
DEFAULT_FIXTURE = ROOT / "tests" / "crew-evals.yaml"


def discover_fixture() -> Path:
    """Find .crews/evals.yaml by walking up from cwd."""
    cwd = Path.cwd()
    while cwd != cwd.parent:
        candidate = cwd / ".crews" / "evals.yaml"
        if candidate.exists():
            return candidate
        cwd = cwd.parent
    return DEFAULT_FIXTURE


DEFAULT_THRESHOLD = 3
DEFAULT_TIMEOUT = 300
PROJECT = "agent-crews"

JUDGE_PROMPT = """You are evaluating an AI agent from a multi-agent crew system. Agents have specific roles: orchestrators route work to specialists, workers execute tasks within their scope.

## Evaluation Task
Rate how well the agent output satisfies the criteria.

## Criteria
{criteria}

{ideal_section}

## Agent Output
{output}

## Scoring Rubric
5 = Excellent — fully meets all criteria, clear and well-executed
4 = Good — meets all criteria with minor imperfections (e.g., slightly verbose, minor omission)
3 = Acceptable — meets the core intent but with notable gaps (e.g., correct routing but no narration)
2 = Poor — partially addresses criteria but misses key requirements (e.g., does the work itself instead of delegating)
1 = Fail — does not meet criteria (e.g., wrong agent, ignores scope, hallucinates)

Respond with exactly two lines:
SCORE: <number>
REASON: <one sentence explanation>"""


def strip_ansi(text: str) -> str:
    return re.sub(r'\x1B\[[0-9;]*[a-zA-Z]', '', text)


def invoke_agent(agent: str, prompt: str, cwd: str = ".", timeout: int = DEFAULT_TIMEOUT, intent_only: bool = False) -> tuple[str, bool]:
    """Invoke kiro-cli agent. Returns (output, success)."""
    cmd = ["kiro-cli", "chat", "--no-interactive", "-a", "--wrap", "never"]
    if agent:
        cmd.extend(["--agent", agent])
    cmd.append(prompt)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=os.path.expanduser(cwd)
        )
        output = strip_ansi(result.stdout + result.stderr)
        if not output.strip():
            return "", False
        return output, True
    except subprocess.TimeoutExpired as e:
        # In intent-only mode, partial output is fine — we just want the first response
        if intent_only:
            output = strip_ansi((e.stdout or "") + (e.stderr or ""))
            if output.strip():
                return output, True
        return "", False
    except Exception as e:
        return str(e), False


def invoke_judge(criteria: str, output: str, ideal: str | None = None) -> tuple[int | None, str]:
    """Invoke judge (bare kiro-cli). Returns (score, reason)."""
    ideal_section = ""
    if ideal:
        ideal_section = f"## Reference (ideal response)\n{ideal}\nNote: The agent does not need to match this exactly. Use it as a reference for what correct behavior looks like."

    prompt = JUDGE_PROMPT.format(criteria=criteria, ideal_section=ideal_section, output=output)
    cmd = ["kiro-cli", "chat", "--no-interactive", "-a", "--wrap", "never", prompt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        text = strip_ansi(result.stdout + result.stderr)
        return parse_judge_response(text)
    except Exception as e:
        return None, f"Judge error: {e}"


def parse_judge_response(text: str) -> tuple[int | None, str]:
    """Parse SCORE: N and REASON: ... from judge output."""
    score = None
    reason = ""
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("SCORE:"):
            try:
                score = int(line.split(":", 1)[1].strip().split()[0])
                score = max(1, min(5, score))
            except (ValueError, IndexError):
                pass
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
    if score is None:
        # Try to find a bare number
        numbers = re.findall(r'\b([1-5])\b', text)
        if numbers:
            score = int(numbers[0])
            reason = reason or text.strip()[:100]
    return score, reason


def run_eval(ev: dict, verbose: bool = False, global_timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run a single eval. Returns result dict."""
    name = ev["name"]
    agent = ev["agent"]
    input_text = ev["input"]
    criteria = ev["criteria"]
    ideal = ev.get("ideal")
    cwd = ev.get("cwd", ".")
    timeout = ev.get("timeout", global_timeout)

    start = time.time()

    # Invoke agent (with retry)
    intent_only = ev.get("intent_only", False) or getattr(run_eval, '_intent_only', False)
    output, success = invoke_agent(agent, input_text, cwd, timeout, intent_only)
    if not success:
        output, success = invoke_agent(agent, input_text, cwd, timeout, intent_only)

    if not success:
        duration = time.time() - start
        return {
            "name": name,
            "score": None,
            "status": "error",
            "error": "timeout" if not output else "empty",
            "reason": f"Agent failed on both attempts ({duration:.0f}s)",
            "duration_s": round(duration, 1),
        }

    if verbose:
        print(f"\n  --- Agent output ({name}) ---")
        print(f"  {output[:500]}")
        print(f"  ---")

    # Invoke judge
    score, reason = invoke_judge(criteria, output, ideal)

    duration = time.time() - start

    if score is None:
        return {
            "name": name,
            "score": None,
            "status": "error",
            "error": "judge_parse",
            "reason": f"Could not parse judge response: {reason[:100]}",
            "duration_s": round(duration, 1),
        }

    return {
        "name": name,
        "score": score,
        "status": "evaluated",
        "reason": reason,
        "duration_s": round(duration, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Model-based crew evaluation")
    parser.add_argument("--fixture", default=None, help="Path to eval YAML (default: .crews/evals.yaml or tests/crew-evals.yaml)")
    parser.add_argument("--tag", help="Filter evals by tag")
    parser.add_argument("--name", help="Run single eval by name")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD, help="Pass threshold (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--verbose", action="store_true", help="Show full agent output")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Agent timeout in seconds (default: 300)")
    parser.add_argument("--intent-only", action="store_true", help="Check delegation intent only (short timeout, judge first response)")
    args = parser.parse_args()

    # Intent-only mode: short timeout, we only care about the first response
    if args.intent_only:
        args.timeout = min(args.timeout, 30)

    # Load fixture
    fixture_path = Path(args.fixture) if args.fixture else discover_fixture()
    if not fixture_path.exists():
        print(f"Error: fixture not found: {fixture_path}", file=sys.stderr)
        sys.exit(2)

    with open(fixture_path) as f:
        data = yaml.safe_load(f)

    evals = data.get("evals", [])

    # Filter
    if args.tag:
        evals = [e for e in evals if args.tag in e.get("tags", [])]
    if args.name:
        evals = [e for e in evals if e["name"] == args.name]

    if not evals:
        print("No evals matched filters.", file=sys.stderr)
        sys.exit(2)

    # Dry run
    if args.dry_run:
        for ev in evals:
            threshold = ev.get("threshold", args.threshold)
            tags = ", ".join(ev.get("tags", []))
            print(f"  {ev['name']:40} agent={ev['agent']:20} threshold={threshold} [{tags}]")
        print(f"\n{len(evals)} evals would run.")
        return

    # Run evals
    print(f"Running {len(evals)} evals...\n")
    results = []
    start_time = time.time()

    # Set intent_only flag for run_eval to pick up
    run_eval._intent_only = args.intent_only

    for ev in evals:
        result = run_eval(ev, verbose=args.verbose, global_timeout=args.timeout)
        results.append(result)

        # Print result
        threshold = ev.get("threshold", args.threshold)
        score = result["score"]
        if score is None:
            print(f"[ERR] {result['name']}: {result.get('error', 'unknown')} — {result['reason']}")
        else:
            passed = score >= threshold
            marker = f"\033[32m{score}\033[0m" if passed else f"\033[31m{score}\033[0m"
            print(f"[ {marker} ] {result['name']}: {result['reason']}")

    # Summary
    total_duration = time.time() - start_time
    evaluated = [r for r in results if r["status"] == "evaluated"]
    errors = [r for r in results if r["status"] == "error"]
    passed = [r for r in evaluated if r["score"] >= (next((e.get("threshold", args.threshold) for e in evals if e["name"] == r["name"]), args.threshold))]
    failed = [r for r in evaluated if r not in passed]
    avg_score = sum(r["score"] for r in evaluated) / len(evaluated) if evaluated else 0

    print(f"\n---")
    print(f"Results: {len(passed)}/{len(evaluated)} passed (threshold: \u2265{args.threshold}), avg score: {avg_score:.1f}")
    if errors:
        print(f"Errors: {len(errors)} (not scored)")
    if failed:
        print(f"Failed:")
        for r in failed:
            print(f"  - {r['name']} (score: {r['score']})")
    print(f"Duration: {total_duration:.0f}s")

    # Write results file
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    results_file = results_dir / f"eval-{PROJECT}-{timestamp}.json"

    # Determine crews from fixture
    crews = sorted(set(tag for e in evals for tag in e.get("tags", []) if "crew" in tag)) or ["meta"]

    output_data = {
        "project": PROJECT,
        "crews": crews,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pass_threshold": args.threshold,
        "duration_s": round(total_duration, 1),
        "summary": {
            "total": len(results),
            "evaluated": len(evaluated),
            "passed": len(passed),
            "failed": len(failed),
            "errors": len(errors),
            "avg_score": round(avg_score, 1),
        },
        "results": results,
    }

    with open(results_file, "w") as f:
        json.dump(output_data, f, indent=2)
        f.write("\n")
    print(f"\nResults written to: {results_file}")

    # Exit code
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
