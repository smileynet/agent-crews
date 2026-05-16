#!/bin/bash
# tests/assumptions/run.sh — Validate platform assumptions about kiro-cli behavior
# Run from project root: ./tests/assumptions/run.sh
#
# Creates a temp workspace, deploys test fixtures, runs agents, checks canary phrases.
# Results written to tests/assumptions/results/<timestamp>.json
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
mkdir -p "$RESULTS_DIR"

TIMESTAMP=$(date -u +%Y-%m-%dT%H-%M-%SZ)
KIRO_VERSION=$(kiro-cli --version 2>/dev/null || echo "unknown")

# Create isolated workspace
WORKDIR=$(mktemp -d -t assumption-test-XXXX)
trap "rm -rf $WORKDIR" EXIT

# Deploy fixtures into workspace
mkdir -p "$WORKDIR/.kiro/agents"
mkdir -p "$WORKDIR/.kiro/steering/worker"
mkdir -p "$WORKDIR/context-files"

# --- Canary files ---
echo "The canary phrase is: CANARY_FILE_7X9Q2" > "$WORKDIR/context-files/canary.md"
echo "Parent secret: PARENT_ONLY_3Z7W5" > "$WORKDIR/context-files/parent-canary.md"
echo "Child secret: CHILD_ONLY_9R2X8" > "$WORKDIR/context-files/child-canary.md"
mkdir -p "$WORKDIR/context-files/glob-test"
echo "First glob: GLOB_A_5T3K" > "$WORKDIR/context-files/glob-test/a.md"
echo "Second glob: GLOB_B_8M2N" > "$WORKDIR/context-files/glob-test/b.md"

# Fake steering file (to test if it auto-loads)
cat > "$WORKDIR/.kiro/steering/worker/test-steering.md" << 'EOF'
---
inclusion: always
---
# Test Steering
The steering secret is: STEERING_SECRET_2W4P6
EOF

# Fake AGENTS.md
echo "AGENTS.md secret: AGENTSMD_AUTO_8K3J1" > "$WORKDIR/AGENTS.md"

# --- Test Agents ---

# T1 + T6: Bare agent (no resources, no tools)
cat > "$WORKDIR/.kiro/agents/bare-agent.json" << 'EOF'
{
  "name": "bare-agent",
  "description": "Test agent with no resources and no tools",
  "tools": [],
  "allowedTools": [],
  "prompt": "You are a test agent. When asked about your context, report ONLY what is pre-loaded in your context window. Be precise and literal. If you don't have something, say so clearly."
}
EOF

# T2: Agent with file:// resource (no tools — can't cheat by reading)
cat > "$WORKDIR/.kiro/agents/file-resource-agent.json" << 'EOF'
{
  "name": "file-resource-agent",
  "description": "Test agent with explicit file resource",
  "tools": [],
  "allowedTools": [],
  "resources": ["file://context-files/canary.md"],
  "prompt": "You are a test agent. Report the canary phrase from your pre-loaded context. Be exact."
}
EOF

# T3: Agent with skill:// resource (on-demand)
mkdir -p "$WORKDIR/.kiro/skills/flamingo-facts"
cat > "$WORKDIR/.kiro/skills/flamingo-facts/SKILL.md" << 'EOF'
---
name: flamingo-facts
description: Facts about flamingos. Use when asked about flamingos, pink birds, or wading birds.
---
# Flamingo Facts
The flamingo skill secret is: FLAMINGO_SKILL_6V8R3
Flamingos are pink because of carotenoid pigments in their diet.
EOF
cat > "$WORKDIR/.kiro/agents/skill-agent.json" << 'EOF'
{
  "name": "skill-agent",
  "description": "Test agent with skill resource (no read tool)",
  "tools": [],
  "allowedTools": [],
  "resources": ["skill://.kiro/skills/flamingo-facts/SKILL.md"],
  "prompt": "You are a test agent. Answer questions using your available knowledge and skills. Be precise and literal. If asked to quote a secret phrase, do so exactly."
}
EOF

# T3b: Agent with skill + read tool (simulates real worker)
cat > "$WORKDIR/.kiro/agents/skill-reader-agent.json" << 'EOF'
{
  "name": "skill-reader-agent",
  "description": "Test agent with skill resource and read tool",
  "tools": ["read"],
  "allowedTools": ["read"],
  "resources": ["skill://.kiro/skills/flamingo-facts/SKILL.md"],
  "prompt": "You are a test agent. Answer questions using your available skills. Quote any secret phrases exactly."
}
EOF

# T4: Parent + child agents for subagent isolation test
cat > "$WORKDIR/.kiro/agents/parent-agent.json" << 'EOF'
{
  "name": "parent-agent",
  "description": "Parent agent that delegates to child",
  "tools": ["subagent"],
  "allowedTools": ["subagent"],
  "resources": ["file://context-files/parent-canary.md"],
  "toolsSettings": {
    "crew": {
      "availableAgents": ["child-agent"],
      "trustedAgents": ["child-agent"]
    }
  },
  "prompt": "You are a parent test agent. You have a secret phrase in your context from parent-canary.md. When asked to delegate, use the subagent tool to send the EXACT task to child-agent. Report back EXACTLY what the child says, word for word."
}
EOF
cat > "$WORKDIR/.kiro/agents/child-agent.json" << 'EOF'
{
  "name": "child-agent",
  "description": "Child agent with own canary",
  "tools": [],
  "allowedTools": [],
  "resources": ["file://context-files/child-canary.md"],
  "prompt": "You are a child test agent. When asked about secrets or phrases in your context, quote them exactly. You should have a child canary phrase. Report ONLY what you see pre-loaded."
}
EOF

# T5: Agent with glob resource (no tools)
cat > "$WORKDIR/.kiro/agents/glob-resource-agent.json" << 'EOF'
{
  "name": "glob-resource-agent",
  "description": "Test agent with glob pattern resource",
  "tools": [],
  "allowedTools": [],
  "resources": ["file://context-files/glob-test/*.md"],
  "prompt": "You are a test agent. Report ALL phrases from your pre-loaded context files. Be exact."
}
EOF

# --- Test execution ---
PASS=0
FAIL=0
declare -a RESULTS=()

run_test() {
    local name="$1"
    local agent="$2"
    local input="$3"
    local expect_present="$4"   # grep pattern that SHOULD be in output (or "NONE")
    local expect_absent="$5"    # grep pattern that should NOT be in output (or "NONE")
    
    local output tmpfile
    tmpfile=$(mktemp)
    cd "$WORKDIR"
    timeout 90 kiro-cli chat --no-interactive -a --agent "$agent" "$input" > "$tmpfile" 2>&1 || true
    cd "$PROJECT_ROOT"
    output=$(cat "$tmpfile" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g')
    rm -f "$tmpfile"
    
    local status="PASS"
    local reason=""
    
    # Check expected present
    if [ "$expect_present" != "NONE" ]; then
        if ! echo "$output" | grep -qi "$expect_present"; then
            status="FAIL"
            reason="Expected '$expect_present' not found"
        fi
    fi
    
    # Check expected absent
    if [ "$expect_absent" != "NONE" ]; then
        if echo "$output" | grep -qi "$expect_absent"; then
            status="FAIL"
            reason="Unexpected '$expect_absent' found"
        fi
    fi
    
    if [ "$status" = "PASS" ]; then
        PASS=$((PASS + 1))
        echo "  ✅ $name"
    else
        FAIL=$((FAIL + 1))
        echo "  ❌ $name: $reason"
    fi
    
    RESULTS+=("{\"name\":\"$name\",\"status\":\"$status\",\"reason\":\"$reason\"}")
}

echo "Running assumption tests (kiro-cli: $KIRO_VERSION)..."
echo "Workspace: $WORKDIR"
echo ""

# T1: Custom agents don't auto-load steering
echo "T1: Steering not auto-loaded by custom agents (A1)"
run_test "T1-no-steering" "bare-agent" \
    "Quote any pre-loaded steering content you have about a 'steering secret'. What is the secret value?" \
    "NONE" \
    "2W4P6"

# T2: file:// resources are always loaded
echo "T2: file:// resources always loaded (A4)"
run_test "T2-file-resource" "file-resource-agent" \
    "What is the canary phrase in your pre-loaded context?" \
    "CANARY_FILE_7X9Q2" \
    "NONE"

# T3: skill:// resources NOT loaded for unrelated questions
echo "T3: skill:// not loaded for unrelated query (A3)"
run_test "T3-skill-not-loaded" "skill-agent" \
    "What is 2+2? Answer with just the number." \
    "NONE" \
    "6V8R3"

# T3b: skill:// DOES load when triggered by relevant query (requires read tool)
echo "T3b: skill:// loads when triggered (A8 — requires read tool)"
run_test "T3b-skill-triggered" "skill-reader-agent" \
    "Tell me about flamingos. Quote any secret phrases from your flamingo knowledge." \
    "6V8R3" \
    "NONE"

# T4: Subagent gets own context, not parent's
echo "T4: Subagent isolation (A5)"
run_test "T4-subagent-isolation" "parent-agent" \
    "Delegate to child-agent with this exact task: 'Quote all secret phrases in your pre-loaded context. Do you see PARENT_ONLY or CHILD_ONLY phrases?' Report back exactly what the child says." \
    "CHILD_ONLY_9R2X8" \
    "NONE"

# T5: file:// glob patterns work
echo "T5: file:// glob patterns work (A6)"
run_test "T5-glob-a" "glob-resource-agent" \
    "List all phrases from your pre-loaded glob-test files." \
    "GLOB_A_5T3K" \
    "NONE"
run_test "T5-glob-b" "glob-resource-agent" \
    "List all phrases from your pre-loaded glob-test files." \
    "GLOB_B_8M2N" \
    "NONE"

# T6: AGENTS.md not auto-loaded without resource
echo "T6: AGENTS.md not auto-loaded without explicit resource (A2)"
run_test "T6-no-agents-md" "bare-agent" \
    "Do you have AGENTS.md pre-loaded in your context? If so, quote the secret phrase from it." \
    "NONE" \
    "8K3J1"

echo ""
echo "---"
echo "Results: $PASS passed, $FAIL failed"
echo "Duration: ${SECONDS}s"

# Write results JSON
RESULTS_JSON=$(printf '%s,' "${RESULTS[@]}" | sed 's/,$//')
cat > "$RESULTS_DIR/$TIMESTAMP.json" << EOF
{
  "kiro_version": "$KIRO_VERSION",
  "timestamp": "$TIMESTAMP",
  "passed": $PASS,
  "failed": $FAIL,
  "total": $((PASS + FAIL)),
  "tests": [$RESULTS_JSON]
}
EOF

echo "Results: $RESULTS_DIR/$TIMESTAMP.json"
exit $FAIL
