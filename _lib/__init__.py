"""Internal modules for generate.py."""

import json


def get_architypes(crew: dict) -> list:
    """Get architypes list, supporting both 'architypes' and 'archetypes' spellings."""
    a = crew.get("architypes") or []
    b = crew.get("archetypes") or []
    return a + [x for x in b if x not in a] if a and b else a or b


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base. Arrays are concatenated and deduped."""
    result = base.copy()
    for key, val in override.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(val, dict):
                result[key] = deep_merge(result[key], val)
            elif isinstance(result[key], list) and isinstance(val, list):
                seen = set()
                merged = []
                for item in result[key] + val:
                    s = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                    if s not in seen:
                        seen.add(s)
                        merged.append(item)
                result[key] = merged
            else:
                result[key] = val
        else:
            result[key] = val
    return result
