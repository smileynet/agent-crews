#!/usr/bin/env bash
# Validate mermaid code blocks in markdown files
# Usage: validate-mermaid.sh [file_or_dir]
# Requires: npx mmdc (mermaid-cli)
set -euo pipefail

TARGET="${1:-.}"
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

pass=0; fail=0; total=0

find "$TARGET" -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" | sort | while read -r f; do
  grep -n '```mermaid' "$f" | cut -d: -f1 | while read -r start; do
    total=$((total + 1))
    content_start=$((start + 1))
    end=$(awk -v s="$start" 'NR>s && /^```/{print NR; exit}' "$f")
    [ -z "$end" ] && { echo "FAIL $f:$start — unclosed block"; fail=$((fail+1)); continue; }
    sed -n "${content_start},$((end - 1))p" "$f" > "$TMPDIR/d.mmd"
    if npx -y mmdc -i "$TMPDIR/d.mmd" -o "$TMPDIR/out.svg" -q 2>"$TMPDIR/err.txt"; then
      pass=$((pass + 1))
    else
      echo "FAIL $f:$start — $(head -1 "$TMPDIR/err.txt")"
      fail=$((fail + 1))
    fi
  done
done

echo "$((pass + fail)) diagrams checked: $pass pass, $fail fail"
[ "$fail" -eq 0 ]
