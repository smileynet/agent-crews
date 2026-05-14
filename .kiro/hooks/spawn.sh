#!/usr/bin/env bash
# agentSpawn hook — first-run detection for agent-crews
blockers=()
warnings=()

command -v python3 &>/dev/null || blockers+=("python3 not installed")
python3 -c "import yaml" 2>/dev/null || blockers+=("pyyaml not installed (pip install pyyaml)")
command -v mise &>/dev/null || warnings+=("MISE_MISSING: mise not installed — justfile recipes still work")

if [[ ${#blockers[@]} -gt 0 ]]; then
  echo "SETUP INCOMPLETE"
  printf '  - %s\n' "${blockers[@]}"
else
  echo "Setup OK. Ready to build agent crews."
  [[ ${#warnings[@]} -gt 0 ]] && printf '  - %s\n' "${warnings[@]}"
fi
