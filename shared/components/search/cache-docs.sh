#!/usr/bin/env bash
# Cache external documentation locally for agent search
# Usage: cache-docs.sh URL [name]
# Tries llms.txt first, then llms-full.txt, then raw fetch
set -euo pipefail

URL="${1:?Usage: cache-docs.sh URL [name]}"
NAME="${2:-$(echo "$URL" | sed 's|https\?://||;s|/|_|g;s|[^a-zA-Z0-9_.-]||g' | head -c 80)}"
OUT_DIR=".kiro/cached-docs"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/$NAME.md"

# Try llms.txt (best format for AI consumption)
for suffix in "llms.txt" "llms-full.txt"; do
  TRY_URL="${URL%/}/$suffix"
  if curl -sfL "$TRY_URL" -o "$OUT_FILE.tmp" 2>/dev/null && [ -s "$OUT_FILE.tmp" ]; then
    { echo "---"; echo "source: $TRY_URL"; echo "cached: $(date -I)"; echo "---"; cat "$OUT_FILE.tmp"; } > "$OUT_FILE"
    rm "$OUT_FILE.tmp"
    echo "✅ Cached $suffix → $OUT_FILE"
    exit 0
  fi
  rm -f "$OUT_FILE.tmp"
done

# Fallback: fetch page as markdown
{ echo "---"; echo "source: $URL"; echo "cached: $(date -I)"; echo "---"; echo ""; } > "$OUT_FILE"

if python3 -c "import trafilatura" 2>/dev/null; then
  python3 -c "
import trafilatura, sys
html = trafilatura.fetch_url('$URL')
if html:
    md = trafilatura.extract(html, output_format='markdown', include_tables=True, include_links=True)
    print(md or '# Extraction failed')
else:
    print('# Fetch failed', file=sys.stderr); sys.exit(1)
" >> "$OUT_FILE"
elif command -v pandoc &>/dev/null; then
  curl -sfL "$URL" | pandoc -f html -t markdown --wrap=none >> "$OUT_FILE"
else
  curl -sfL "$URL" | sed 's/<[^>]*>//g' | sed '/^$/d' >> "$OUT_FILE"
fi

echo "✅ Cached → $OUT_FILE"
