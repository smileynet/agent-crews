#!/usr/bin/env bash
# crew-health.sh — one-shot health check for a project's crew configuration
set -euo pipefail

show_help() {
  cat << 'EOF'
Usage: ./scripts/crew-health.sh <project-name>

Crew structural health check. Finds: dead agents, scope overlaps, missing routing, tool permission issues.
Project name must match fleet.yaml (e.g. 'craft-mmo', not a path).

Examples:
  ./scripts/crew-health.sh craft-mmo
  ./scripts/crew-health.sh pidev-crafter
EOF
  exit 0
}
[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && show_help

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <project-name>" >&2
  exit 2
fi

PROJECT="$1"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 - "$PROJECT" "$REPO_ROOT" << 'PYTHON'
import yaml, json, os, sys, glob

project = sys.argv[1]
repo = sys.argv[2]
fleet_path = os.path.join(repo, 'fleet.yaml')

if not os.path.exists(fleet_path):
    print(f'ERROR: fleet.yaml not found at {fleet_path}', file=sys.stderr)
    sys.exit(2)

with open(fleet_path) as f:
    fleet = yaml.safe_load(f)

defaults = fleet.get('defaults', {})
projects = fleet.get('projects', {})

if project not in projects:
    print(f'ERROR: project "{project}" not found in fleet.yaml', file=sys.stderr)
    print(f'Available: {list(projects.keys())}', file=sys.stderr)
    sys.exit(2)

proj = projects[project]
crews = proj.get('crews', defaults.get('crews', ['general']))
theme = proj.get('theme', defaults.get('theme'))

# Merge verification from defaults + project
def_components = defaults.get('components', {})
proj_components = proj.get('components', {})
def_verification = def_components.get('verification', {}).get('checks', {})
proj_verification = proj_components.get('verification', {}).get('checks', {})
verification = {**def_verification, **proj_verification}

# Load agent JSONs
agents_dir = os.path.join(repo, 'projects', project, '.kiro', 'agents')
agents = {}
if os.path.isdir(agents_dir):
    for fp in glob.glob(os.path.join(agents_dir, '*.json')):
        with open(fp) as f:
            a = json.load(f)
            agents[a['name']] = a

issues = []
warnings = []
checks = []
fixes = []

# 1. General crew included
if 'general' in crews:
    checks.append('\u2713 general crew included')
elif 'meta' in crews:
    checks.append('\u2713 meta crew (self-hosted repo)')
else:
    issues.append('general crew not included')
    checks.append('\u2717 general crew NOT included')
    fixes.append(f"Add 'general' to {project}'s crews in fleet.yaml")

# 2+3. Routing table and availableAgents checks
for name, agent in agents.items():
    ts = agent.get('toolsSettings', {})
    sub = ts.get('subagent', {})
    available = sub.get('availableAgents', [])
    for ref in available:
        if ref not in agents:
            msg = f"dead agent: '{ref}' in {name}'s availableAgents but no JSON exists"
            issues.append(msg)
            checks.append(f'\u2717 {msg}')
            fixes.append(f"Add '{ref}.json' or remove '{ref}' from {name}'s availableAgents")

if not any('dead agent' in c for c in checks):
    checks.append('\u2713 all routing table entries have matching agents')

# 4. Duplicate keyboard shortcuts
shortcuts = {}
for name, agent in agents.items():
    ks = agent.get('keyboardShortcut')
    if ks:
        shortcuts.setdefault(ks, []).append(name)
for ks, names in shortcuts.items():
    if len(names) > 1:
        msg = f"duplicate shortcut '{ks}': {names}"
        issues.append(msg)
        checks.append(f'\u2717 {msg}')
        fixes.append(f"Assign unique shortcuts for: {names}")
if not any('duplicate shortcut' in c for c in checks):
    checks.append('\u2713 no duplicate keyboard shortcuts')

# 5. Verification commands
has_any_verification = any(v for v in verification.values() if v)
if has_any_verification:
    checks.append('\u2713 verification commands configured')
else:
    warnings.append('no verification commands configured (all null)')
    checks.append('\u26a0 no verification commands configured')

# 6. Scope boundaries when >2 crews
active_crews = [c for c in crews if c != 'meta']
if len(active_crews) > 2:
    leads_without_scope = []
    for name, agent in agents.items():
        if name.endswith('-lead') and 'Scope Boundary' not in agent.get('prompt', ''):
            leads_without_scope.append(name)
    if leads_without_scope:
        for lead in leads_without_scope:
            msg = f"{lead} has no scope boundary ({len(active_crews)} crews present)"
            warnings.append(msg)
            checks.append(f'\u26a0 {msg}')
    else:
        checks.append('\u2713 all leads have scope boundaries')
elif len(active_crews) == 2:
    for name, agent in agents.items():
        if name.endswith('-lead') and 'Scope Boundary' not in agent.get('prompt', ''):
            checks.append(f'\u26a0 {name} has no scope boundary (only {len(active_crews)} crews, acceptable)')
            warnings.append(f'{name} has no scope boundary (only 2 crews, acceptable)')
            break
    else:
        checks.append('\u2713 scope boundaries present')
else:
    checks.append('\u2713 scope boundaries n/a (single crew)')

# 7. Shell tool without allowedCommands
shell_issues_found = False
for name, agent in agents.items():
    tools = agent.get('tools', [])
    ts = agent.get('toolsSettings', {})
    if 'shell' in tools or 'execute_bash' in tools:
        bash_settings = ts.get('execute_bash', {})
        if not bash_settings.get('allowedCommands') and not bash_settings.get('autoAllowReadonly'):
            msg = f"tool mismatch: {name} has 'shell' in tools but no allowedCommands or autoAllowReadonly"
            issues.append(msg)
            checks.append(f'\u2717 {msg}')
            fixes.append(f"Add allowedCommands or autoAllowReadonly to {name}'s execute_bash toolsSettings")
            shell_issues_found = True
if not shell_issues_found:
    checks.append('\u2713 shell tool permissions configured correctly')

# 8. Empty prompts
empty_found = False
for name, agent in agents.items():
    prompt = agent.get('prompt', '')
    if not prompt.strip():
        msg = f"{name} has an empty prompt"
        issues.append(msg)
        checks.append(f'\u2717 {msg}')
        fixes.append(f"Add prompt content to {name}.json")
        empty_found = True
if not empty_found:
    checks.append('\u2713 no agents with empty prompts')

# 9. Resource references (checked against project's deploy dir)
project_root = os.path.join(repo, 'projects', project)
missing_resources = {}  # resource -> list of agents
for name, agent in agents.items():
    for res in agent.get('resources', []):
        if res.startswith('file://'):
            pattern = res[7:]
            full = os.path.join(project_root, pattern)
            if '*' not in pattern:
                if not os.path.exists(full):
                    missing_resources.setdefault(res, []).append(name)
            else:
                if not glob.glob(full):
                    missing_resources.setdefault(res, []).append(name)
        elif res.startswith('skill://'):
            skill_path = res[8:]
            full = os.path.join(project_root, skill_path)
            if not os.path.exists(full):
                missing_resources.setdefault(res, []).append(name)
if missing_resources:
    count = len(missing_resources)
    checks.append(f'\u26a0 {count} resource path(s) unresolved locally (OK if deployed to target)')
    warnings.append(f'{count} resource paths unresolved locally')
else:
    checks.append('\u2713 all resource references valid')

# Count agents per crew from description prefix [CrewName]
crew_counts = {}
for name, agent in agents.items():
    desc = agent.get('description', '')
    if desc.startswith('[') and ']' in desc:
        crew_name = desc[1:desc.index(']')].lower()
        crew_counts[crew_name] = crew_counts.get(crew_name, 0) + 1
    else:
        crew_counts['other'] = crew_counts.get('other', 0) + 1

total_agents = len(agents)
counts_str = ', '.join(f'{k}: {v}' for k, v in sorted(crew_counts.items()))

# Output
print(f'=== CREW HEALTH: {project} ===')
print()
crews_str = ', '.join(crews)
print(f'crews: [{crews_str}]')
print(f'agents: {total_agents} ({counts_str})')
print(f'theme: {theme or "null"}')
print('verification:')
for cmd_name in sorted(verification.keys()):
    cmd = verification[cmd_name]
    if cmd:
        print(f'  {cmd_name}: {cmd} \u2713')
    else:
        print(f'  {cmd_name}: null')
print()
print('checks:')
for c in checks:
    print(f'  {c}')
print()
print(f'issues: {len(issues)}')
print(f'warnings: {len(warnings)}')

if fixes:
    print()
    print('fixes:')
    for i, fix in enumerate(fixes, 1):
        print(f'  {i}. {fix}')

sys.exit(1 if issues else 0)
PYTHON
