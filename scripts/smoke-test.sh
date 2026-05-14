#!/usr/bin/env bash
# Behavioral smoke test for agent crews.
# Runs kiro-cli in non-interactive mode with test prompts and checks output for expected signals.
# Usage: ./scripts/smoke-test.sh <target-path> [test-file]
# Default test file: tests/smoke-tests.yaml (or inline tests below)
set -euo pipefail

TARGET="${1:?Usage: smoke-test.sh <target-path> [test-file]}"
TEST_FILE="${2:-}"
PASS=0
FAIL=0
SKIP=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

run_test() {
    local name="$1"
    local agent="$2"
    local prompt="$3"
    local expect="$4"        # grep pattern expected in output
    local not_expect="${5:-}" # grep pattern that should NOT appear (optional)

    echo -n "  $name... "

    # Run agent non-interactively
    local output
    output=$(cd "$TARGET" && kiro-cli chat --no-interactive --trust-all-tools \
        ${agent:+--agent "$agent"} "$prompt" 2>&1) || true

    # Check expected signal
    if echo "$output" | grep -qiE "$expect"; then
        # Check not-expected if provided
        if [ -n "$not_expect" ] && echo "$output" | grep -qiE "$not_expect"; then
            echo -e "${RED}FAIL${NC} (unexpected pattern found: $not_expect)"
            FAIL=$((FAIL + 1))
            return
        fi
        echo -e "${GREEN}PASS${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC} (expected: $expect)"
        echo "    Output (last 200 chars): ${output: -200}"
        FAIL=$((FAIL + 1))
    fi
}

echo "🧪 Smoke testing agents in: $TARGET"
echo ""

# If a test file is provided, source it
if [ -n "$TEST_FILE" ] && [ -f "$TEST_FILE" ]; then
    source "$TEST_FILE"
else
    # Default inline tests — basic behavioral checks
    echo "Running default behavioral tests..."
    echo ""

    echo "=== Inspector: confidence labels ==="
    run_test "Uses [verified] labels" "inspector" \
        "Review this claim: terraform validate checks for security issues. Is this true?" \
        "\[verified\]|\[likely\]|\[unverified\]"

    echo ""
    echo "=== Champion: JTBD challenge ==="
    run_test "Challenges with JTBD" "champion" \
        "We need to add a caching layer to the API" \
        "job|customer|problem|solving|outcome|situation"

    echo ""
    echo "=== Security reviewer: network exposure ==="
    run_test "Flags public endpoint risk" "security" \
        "Review this plan: deploy a container with a public IP and security group open to 0.0.0.0/0" \
        "risk|exposure|restrict|block|FAIL|warning|concern"

    echo ""
    echo "=== Oracle: blind spot detection ==="
    run_test "Challenges assumptions" "oracle" \
        "We're building a custom auth system because Cognito is too limited" \
        "assumption|blind.spot|adjacent|inversion|what if"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}, ${YELLOW}${SKIP} skipped${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
