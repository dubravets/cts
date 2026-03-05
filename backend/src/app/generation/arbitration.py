from __future__ import annotations

from itertools import combinations
from uuid import uuid4

from app.generation.actions import assert_relative, enter_menu, read_calibration, set_level, wait_ms
from app.generation.engine import GeneratedCase


def generate_arbitration_and_combination_cases(
    *,
    spec_rules: list[dict],
    reference_ids: list[str],
    settle_time_ms: int = 500,
    tolerance_percent: float = 2.0,
) -> list[GeneratedCase]:
    arbitration_cases: list[GeneratedCase] = []
    combo_cases: list[GeneratedCase] = []

    for left, right in combinations(spec_rules, 2):
        left_map = _mapping_by_level(left.get("expression", {}).get("mappings", []))
        right_map = _mapping_by_level(right.get("expression", {}).get("mappings", []))
        shared_levels = sorted(set(left_map) & set(right_map))
        for level in shared_levels:
            if left_map[level] == right_map[level]:
                continue
            arbitration_cases.append(
                GeneratedCase(
                    id=str(uuid4()),
                    name=f"arbitration-{left['name']}-{right['name']}-{level}",
                    case_type="arbitration",
                    source_spec_rule_id=left["id"],
                    status="Draft",
                    to_confirm=True,
                    steps=[
                        enter_menu("Display/Backlight").to_dict(),
                        set_level(level).to_dict(),
                        wait_ms(settle_time_ms).to_dict(),
                        read_calibration("nits").to_dict(),
                    ],
                    expected={
                        "candidate_values": [left_map[level], right_map[level]],
                        "expected_source": "spec_rule",
                        "level": level,
                        "tolerance_percent": tolerance_percent,
                    },
                    reference_ids=reference_ids,
                )
            )

    if len(spec_rules) >= 2:
        first_levels = spec_rules[0].get("expression", {}).get("mappings", [])
        second_levels = spec_rules[1].get("expression", {}).get("mappings", [])
        for left in first_levels:
            for right in second_levels:
                level_combo = f"{left['level']}+{right['level']}"
                combo_cases.append(
                    GeneratedCase(
                        id=str(uuid4()),
                        name=f"combination-{level_combo}",
                        case_type="combination",
                        source_spec_rule_id=spec_rules[0]["id"],
                        status="Draft",
                        to_confirm=False,
                        steps=[
                            enter_menu("Display/Backlight").to_dict(),
                            set_level(level_combo).to_dict(),
                            wait_ms(settle_time_ms).to_dict(),
                            read_calibration("nits").to_dict(),
                            assert_relative(
                                expected_value=(
                                    float(left["expected_nits"])
                                    + float(right["expected_nits"])
                                ),
                                tolerance_percent=tolerance_percent,
                                expected_source="spec_rule",
                            ).to_dict(),
                        ],
                        expected={
                            "level": level_combo,
                            "expected_source": "spec_rule",
                            "combined_from": [left["level"], right["level"]],
                        },
                        reference_ids=reference_ids,
                    )
                )

    return arbitration_cases + combo_cases


def _mapping_by_level(mappings: list[dict]) -> dict[str, float]:
    return {str(item["level"]): float(item["expected_nits"]) for item in mappings}
