#!/usr/bin/env python3
import yaml, os
from pathlib import Path

fleet = yaml.safe_load(open('fleet.local.yaml'))
local = yaml.safe_load(open('fleet.local.yaml')) if os.path.exists('fleet.local.yaml') else {}
projects = local.get('projects', {})
for proj, cfg in fleet.get('projects', {}).items():
    target = projects.get(proj, '(not deployed)')
    ptype = cfg.get('type', 'themed')
    linked = '✅' if os.path.islink(f'{target}/.kiro') or os.path.isdir(f'{target}/.kiro') else '❌'
    if cfg.get('deploy') is False:
        linked = '⏭️'
        target = '(reference only)'
    print(f'  {linked} {proj:<20} {ptype:<8} {target}')
