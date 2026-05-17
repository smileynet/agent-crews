"""Internal modules for generate.py."""


def get_architypes(crew: dict) -> list:
    """Get architypes list, supporting both 'architypes' and 'archetypes' spellings."""
    a = crew.get("architypes") or []
    b = crew.get("archetypes") or []
    return a + [x for x in b if x not in a] if a and b else a or b
