#!/usr/bin/env python3
import yaml, os

local = yaml.safe_load(open('fleet.local.yaml')) if os.path.exists('fleet.local.yaml') else {}
for proj in local.get('deployments', {}):
    print(proj)
