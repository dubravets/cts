from __future__ import annotations


def impacted_cases_from_mapping_diff(
    *,
    old_expression: dict,
    new_expression: dict,
    existing_cases: list[dict],
) -> list[str]:
    old_map = _mapping_by_level(old_expression.get("mappings", []))
    new_map = _mapping_by_level(new_expression.get("mappings", []))

    changed_levels = {
        level
        for level in sorted(set(old_map) | set(new_map))
        if old_map.get(level) != new_map.get(level)
    }
    impacted = [
        case["id"]
        for case in sorted(existing_cases, key=lambda item: item["id"])
        if str(case.get("expected", {}).get("level")) in changed_levels
    ]
    return impacted


def _mapping_by_level(mappings: list[dict]) -> dict[str, float]:
    return {str(item["level"]): float(item["expected_nits"]) for item in mappings}
