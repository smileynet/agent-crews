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
    uv run scripts/eval-crew.py --timeout 180  # longer timeout
    uv run scripts/eval-crew.py --intent-only  # check delegation intent only (30s timeout)
    uv run scripts/eval-crew.py --trials 3     # run each eval 3x, report pass^k (default)
    uv run scripts/eval-crew.py --trials 1     # single trial for fast iteration
    uv run scripts/eval-crew.py --judge-trials 3  # majority-vote judge scoring
    uv run scripts/eval-crew.py --backfill latest  # re-run only failed/errored evals from last run
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from collections import Counter
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
DEFAULT_TIMEOUT = 120
PROJECT = "agent-crews"

# Directories to copy into isolated environment
COPY_DIRS = [".kiro", "base", "shared", ".crews"]
# Files to copy
COPY_FILES = ["AGENTS.md", "CHANGELOG.md", "justfile"]

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


def create_isolated_env(fixtures: dict | None = None) -> Path:
    """Create a temp directory with copied context and minimal git state.

    Copies provide full read/write access for agents that need to modify files.
    Fixtures override specific files for scenario-specific testing.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="eval-crew-"))
    for d in COPY_DIRS:
        src = ROOT / d
        if src.exists():
            shutil.copytree(src, tmpdir / d)
    for f in COPY_FILES:
        src = ROOT / f
        if src.exists():
            shutil.copy2(src, tmpdir / f)
    # Apply fixtures (override copied files with test-specific content)
    if fixtures:
        for path, content in fixtures.items():
            dest = tmpdir / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
    # Initialize minimal git repo so agents running git commands don't error
    subprocess.run(
        ["git", "init", "--quiet"], cwd=str(tmpdir),
        capture_output=True, timeout=5
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "eval baseline", "--quiet"],
        cwd=str(tmpdir), capture_output=True, timeout=5,
        env={**os.environ, "GIT_AUTHOR_NAME": "eval", "GIT_AUTHOR_EMAIL": "eval@test",
             "GIT_COMMITTER_NAME": "eval", "GIT_COMMITTER_EMAIL": "eval@test"}
    )
    return tmpdir


def cleanup_isolated_env(tmpdir: Path) -> None:
    """Remove temp directory."""
    shutil.rmtree(tmpdir, ignore_errors=True)


def invoke_agent(agent: str, prompt: str, cwd: str = ".", timeout: int = DEFAULT_TIMEOUT, intent_only: bool = False) -> tuple[str, bool]:
    """Invoke kiro-cli agent with retry. Returns (output, success).

    Retry policy: 1 retry on empty/timeout (transient failures).
    No retry on non-empty output (agent responded, even if poorly).
    """
    for attempt in range(2):
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
            if output.strip():
                return output, True
            # Empty output — retry
            if attempt == 0:
                continue
            return "", False
        except subprocess.TimeoutExpired as e:
            if intent_only:
                stdout = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
                stderr = (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
                output = strip_ansi(stdout + stderr)
                if output.strip():
                    return output, True
            # Timeout — retry
            if attempt == 0:
                continue
            return "", False
        except Exception as e:
            return str(e), False
    return "", False


def invoke_judge(criteria: str, output: str, ideal: str | None = None) -> tuple[int | None, str]:
    """Invoke judge with retry. Returns (score, reason).

    Retry policy: 1 retry on parse failure (judge gave unparseable output).
    No retry on valid score (even if low).
    """
    ideal_section = ""
    if ideal:
        ideal_section = f"## Reference (ideal response)\n{ideal}\nNote: The agent does not need to match this exactly. Use it as a reference for what correct behavior looks like."

    prompt = JUDGE_PROMPT.format(criteria=criteria, ideal_section=ideal_section, output=output)
    cmd = ["kiro-cli", "chat", "--no-interactive", "-a", "--wrap", "never", prompt]

    for attempt in range(2):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            text = strip_ansi(result.stdout + result.stderr)
            score, reason = parse_judge_response(text)
            if score is not None:
                return score, reason
            # Parse failure — retry
            if attempt == 0:
                continue
            return None, f"Could not parse after 2 attempts: {text[:100]}"
        except Exception as e:
            if attempt == 0:
                continue
            return None, f"Judge error: {e}"
    return None, "Judge failed after 2 attempts"


def invoke_judge_majority(criteria: str, output: str, ideal: str | None, judge_trials: int) -> tuple[int | None, str]:
    """Run judge multiple times and return majority-vote score."""
    scores = []
    reasons = []
    for _ in range(judge_trials):
        score, reason = invoke_judge(criteria, output, ideal)
        if score is not None:
            scores.append(score)
            reasons.append(reason)
    if not scores:
        return None, "All judge trials failed"
    # Majority vote (most common score)
    majority_score = Counter(scores).most_common(1)[0][0]
    # Use reason from first trial that matched majority
    majority_reason = next((r for s, r in zip(scores, reasons) if s == majority_score), reasons[0])
    if judge_trials > 1:
        majority_reason = f"[{len(scores)}/{judge_trials} judges, votes: {dict(Counter(scores))}] {majority_reason}"
    return majority_score, majority_reason


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
        numbers = re.findall(r'\b([1-5])\b', text)
        if numbers:
            score = int(numbers[0])
            reason = reason or text.strip()[:100]
    return score, reason


def run_eval(ev: dict, verbose: bool = False, global_timeout: int = DEFAULT_TIMEOUT,
             intent_only: bool = False, judge_trials: int = 1) -> dict:
    """Run a single eval trial. Returns result dict."""
    name = ev["name"]
    agent = ev["agent"]
    input_text = ev["input"]
    criteria = ev["criteria"]
    ideal = ev.get("ideal")
    timeout = ev.get("timeout", global_timeout)

    # Per-eval intent_only overrides global setting
    eval_intent_only = ev.get("intent_only", intent_only)
    if eval_intent_only and timeout == global_timeout:
        timeout = min(timeout, 30)

    # Create isolated environment with optional fixtures
    fixtures = ev.get("fixtures")
    tmpdir = create_isolated_env(fixtures)
    cwd = str(tmpdir)

    start = time.time()

    try:
        # Invoke agent (retry handled internally)
        output, success = invoke_agent(agent, input_text, cwd, timeout, eval_intent_only)

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

        # Invoke judge (with majority vote if judge_trials > 1)
        if judge_trials > 1:
            score, reason = invoke_judge_majority(criteria, output, ideal, judge_trials)
        else:
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
    finally:
        cleanup_isolated_env(tmpdir)


def run_eval_with_trials(ev: dict, trials: int, **kwargs) -> dict:
    """Run an eval N times and report pass^k."""
    if trials == 1:
        return run_eval(ev, **kwargs)

    threshold = ev.get("threshold", DEFAULT_THRESHOLD)
    trial_results = []
    for t in range(trials):
        result = run_eval(ev, **kwargs)
        trial_results.append(result)

    # Aggregate
    scores = [r["score"] for r in trial_results if r["score"] is not None]
    errors = [r for r in trial_results if r["status"] == "error"]
    total_duration = sum(r["duration_s"] for r in trial_results)

    if not scores:
        return {
            "name": ev["name"],
            "score": None,
            "status": "error",
            "error": "all_trials_failed",
            "reason": f"All {trials} trials failed",
            "duration_s": round(total_duration, 1),
            "trials": trials,
        }

    passes = sum(1 for s in scores if s >= threshold)
    majority_passed = passes > len(scores) / 2  # majority pass (2/3, 3/5, etc.)
    avg_score = sum(scores) / len(scores)
    min_score = min(scores)

    # pass^k: did MAJORITY of trials pass?
    return {
        "name": ev["name"],
        "score": min_score,  # Conservative: report worst score
        "avg_score": round(avg_score, 1),
        "status": "evaluated",
        "reason": f"pass^{trials}: {passes}/{len(scores)} passed (scores: {scores})",
        "pass_k": majority_passed,
        "trials": trials,
        "trial_scores": scores,
        "duration_s": round(total_duration, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Model-based crew evaluation")
    parser.add_argument("--fixture", default=None, help="Path to eval YAML")
    parser.add_argument("--tag", help="Filter evals by tag")
    parser.add_argument("--name", help="Run single eval by name")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD, help="Pass threshold (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--verbose", action="store_true", help="Show full agent output")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Agent timeout in seconds (default: 120)")
    parser.add_argument("--intent-only", action="store_true", help="Check delegation intent only (short timeout)")
    parser.add_argument("--trials", type=int, default=3, help="Run each eval N times, report pass^k (default: 3)")
    parser.add_argument("--judge-trials", type=int, default=1, help="Judge each output N times, majority vote (default: 1)")
    parser.add_argument("--backfill", type=str, metavar="RUN_DIR", help="Re-run only failed/errored evals from a previous run (path to run dir or 'latest')")
    parser.add_argument("--parallel", type=int, default=1, help="Run N evals concurrently (default: 1, sequential)")
    args = parser.parse_args()

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

    # Backfill: only re-run failed/errored evals from a previous run
    if args.backfill:
        backfill_path = Path(args.backfill)
        if args.backfill == "latest":
            backfill_path = ROOT / "results" / "latest"
        if not backfill_path.exists():
            print(f"Error: backfill path not found: {backfill_path}", file=sys.stderr)
            sys.exit(2)
        scores_file = backfill_path / "scores.jsonl"
        if not scores_file.exists():
            print(f"Error: no scores.jsonl in {backfill_path}", file=sys.stderr)
            sys.exit(2)
        # Find failed/errored eval names
        needs_rerun = set()
        with open(scores_file) as f:
            for line in f:
                r = json.loads(line)
                if r["status"] == "error":
                    needs_rerun.add(r["name"])
                elif r["status"] == "evaluated":
                    # Check if it failed its threshold
                    ev_def = next((e for e in evals if e["name"] == r["name"]), None)
                    if ev_def:
                        threshold = ev_def.get("threshold", args.threshold)
                        if r["score"] < threshold:
                            needs_rerun.add(r["name"])
                    # Also backfill pass^k failures
                    if r.get("pass_k") is False:
                        needs_rerun.add(r["name"])
        evals = [e for e in evals if e["name"] in needs_rerun]
        if not evals:
            print("Backfill: all evals passed in previous run. Nothing to re-run.")
            sys.exit(0)
        print(f"Backfill: re-running {len(evals)} failed/errored evals from {backfill_path.name}\n")

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
        if args.trials > 1:
            print(f"Trials: {args.trials} (pass^k reporting)")
        if args.judge_trials > 1:
            print(f"Judge trials: {args.judge_trials} (majority vote)")
        print(f"Isolation: all evals run in mktemp environment")
        return

    # Run evals
    trial_label = f" x{args.trials} trials" if args.trials > 1 else ""
    judge_label = f", {args.judge_trials}-vote judge" if args.judge_trials > 1 else ""
    parallel_label = f", {args.parallel} parallel" if args.parallel > 1 else ""
    print(f"Running {len(evals)} evals{trial_label}{judge_label}{parallel_label} (isolated)...\n")
    results = [None] * len(evals)
    start_time = time.time()

    def _run_one(idx_ev):
        idx, ev = idx_ev
        backoff = 1
        for attempt in range(3):
            result = run_eval_with_trials(
                ev, trials=args.trials,
                verbose=args.verbose, global_timeout=args.timeout,
                intent_only=args.intent_only, judge_trials=args.judge_trials,
            )
            # Retry on all-trials-failed with backoff (likely rate limit)
            if result.get("error") == "all_trials_failed" and attempt < 2:
                time.sleep(backoff)
                backoff *= 2
                continue
            return idx, result
        return idx, result

    if args.parallel > 1:
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = {executor.submit(_run_one, (i, ev)): i for i, ev in enumerate(evals)}
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result
                # Print as they complete
                ev = evals[idx]
                threshold = ev.get("threshold", args.threshold)
                score = result["score"]
                if score is None:
                    print(f"[ERR] {result['name']}: {result.get('error', 'unknown')} — {result['reason']}")
                elif args.trials > 1:
                    passed = result.get("pass_k", False)
                    marker = f"\033[32m✓\033[0m" if passed else f"\033[31m✗\033[0m"
                    print(f"[ {marker} ] {result['name']}: {result['reason']}")
                else:
                    passed = score >= threshold
                    marker = f"\033[32m{score}\033[0m" if passed else f"\033[31m{score}\033[0m"
                    print(f"[ {marker} ] {result['name']}: {result['reason']}")
    else:
        for i, ev in enumerate(evals):
            _, result = _run_one((i, ev))
            results[i] = result

            # Print result
            threshold = ev.get("threshold", args.threshold)
            score = result["score"]
            if score is None:
                print(f"[ERR] {result['name']}: {result.get('error', 'unknown')} — {result['reason']}")
            elif args.trials > 1:
                passed = result.get("pass_k", False)
                marker = f"\033[32m{'✓' if passed else '✗'}\033[0m" if passed else f"\033[31m✗\033[0m"
                print(f"[ {marker} ] {result['name']}: {result['reason']}")
            else:
                passed = score >= threshold
                marker = f"\033[32m{score}\033[0m" if passed else f"\033[31m{score}\033[0m"
                print(f"[ {marker} ] {result['name']}: {result['reason']}")

    # Summary
    total_duration = time.time() - start_time
    evaluated = [r for r in results if r["status"] == "evaluated"]
    errors = [r for r in results if r["status"] == "error"]

    if args.trials > 1:
        passed = [r for r in evaluated if r.get("pass_k", False)]
        failed = [r for r in evaluated if not r.get("pass_k", False)]
        avg_score = sum(r.get("avg_score", r["score"]) for r in evaluated) / len(evaluated) if evaluated else 0
        print(f"\n---")
        print(f"Results: {len(passed)}/{len(evaluated)} pass^{args.trials} (all trials ≥ threshold)")
        print(f"Avg score: {avg_score:.1f}")
    else:
        passed = [r for r in evaluated if r["score"] >= (next((e.get("threshold", args.threshold) for e in evals if e["name"] == r["name"]), args.threshold))]
        failed = [r for r in evaluated if r not in passed]
        avg_score = sum(r["score"] for r in evaluated) / len(evaluated) if evaluated else 0
        print(f"\n---")
        print(f"Results: {len(passed)}/{len(evaluated)} passed (threshold: ≥{args.threshold}), avg score: {avg_score:.1f}")

    if errors:
        print(f"Errors: {len(errors)} (not scored)")
    if failed:
        print(f"Failed:")
        for r in failed:
            if args.trials > 1:
                print(f"  - {r['name']} ({r['reason']})")
            else:
                print(f"  - {r['name']} (score: {r['score']})")
    print(f"Duration: {total_duration:.0f}s")

    # Write results
    results_dir = ROOT / "results" / "runs"
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run_dir = results_dir / timestamp
    run_dir.mkdir()

    # Gather context
    commit_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(ROOT)
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, cwd=str(ROOT)
    ).stdout.strip()
    kiro_version = subprocess.run(
        ["kiro-cli", "--version"], capture_output=True, text=True
    ).stdout.strip()
    fixture_sha = subprocess.run(
        ["git", "hash-object", str(fixture_path)], capture_output=True, text=True, cwd=str(ROOT)
    ).stdout.strip()

    crews = sorted(set(tag for e in evals for tag in e.get("tags", []) if "crew" in tag)) or ["meta"]

    meta = {
        "project": PROJECT,
        "crews": crews,
        "context": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit": commit_sha,
            "branch": branch,
            "kiro_version": kiro_version,
            "fixture_sha": fixture_sha,
            "fixture_path": str(fixture_path.relative_to(ROOT)),
        },
        "config": {
            "pass_threshold": args.threshold,
            "trials": args.trials,
            "judge_trials": args.judge_trials,
            "timeout": args.timeout,
            "intent_only": args.intent_only,
            "isolation": True,
            "filter_tag": args.tag,
            "filter_name": args.name,
        },
        "duration_s": round(total_duration, 1),
        "summary": {
            "total": len(results),
            "evaluated": len(evaluated),
            "passed": len(passed),
            "failed": len(failed),
            "errors": len(errors),
            "avg_score": round(avg_score, 1),
        },
    }

    with open(run_dir / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    with open(run_dir / "scores.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Update latest symlink
    latest = ROOT / "results" / "latest"
    latest.unlink(missing_ok=True)
    os.symlink(run_dir, latest)

    print(f"\nResults written to: {run_dir}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
