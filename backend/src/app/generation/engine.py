from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.generation.actions import (
    Action,
    assert_relative,
    assert_threshold,
    enter_menu,
    read_calibration,
    set_level,
    wait_ms,
)


@dataclass(frozen=True)
class GeneratedCase:
    id: str
    name: str
    case_type: str
    source_spec_rule_id: str
    status: str
    to_confirm: bool
    steps: list[dict]
    expected: dict
    reference_ids: list[str]


def generate_mapping_cases(
    *,
    source_spec_rule_id: str,
    source_spec_rule_name: str,
    expression: dict,
    reference_ids: list[str],
    project_config: dict,
) -> list[GeneratedCase]:
    settle_time_ms = int(
        expression.get("settle_time_ms", project_config.get("settle_time_ms", 500))
    )
    tolerance_percent = float(
        expression.get("tolerance_percent", project_config.get("tolerance_percent", 2.0))
    )

    mappings = expression.get("mappings", [])
    generated: list[GeneratedCase] = []
    for mapping in mappings:
        level = str(mapping["level"])
        expected_nits = float(mapping["expected_nits"])
        expected_source = str(mapping.get("expected_source", "spec_rule"))
        steps = _serialize_steps(
            [
                enter_menu("Display/Backlight"),
                set_level(level),
                wait_ms(settle_time_ms),
                read_calibration("nits"),
                assert_relative(
                    expected_value=expected_nits,
                    tolerance_percent=tolerance_percent,
                    expected_source=expected_source,
                ),
            ]
        )
        generated.append(
            GeneratedCase(
                id=str(uuid4()),
                name=f"{source_spec_rule_name}-{level}",
                case_type="mapping",
                source_spec_rule_id=source_spec_rule_id,
                status="Draft",
                to_confirm=False,
                steps=steps,
                expected={
                    "level": level,
                    "expected_nits": expected_nits,
                    "expected_source": expected_source,
                    "tolerance_percent": tolerance_percent,
                    "settle_time_ms": settle_time_ms,
                },
                reference_ids=reference_ids,
            )
        )
    return generated


def generate_threshold_cases(
    *,
    source_spec_rule_id: str,
    source_spec_rule_name: str,
    expression: dict,
    reference_ids: list[str],
    project_config: dict,
) -> list[GeneratedCase]:
    settle_time_ms = int(
        expression.get("settle_time_ms", project_config.get("settle_time_ms", 500))
    )
    thresholds = expression.get("thresholds", [])
    generated: list[GeneratedCase] = []
    for item in thresholds:
        rule_name = str(item["name"])
        comparator = str(item["comparator"])
        value = float(item["value"])
        expected_source = str(item.get("expected_source", "spec_rule"))
        steps = _serialize_steps(
            [
                enter_menu("Display/Backlight"),
                wait_ms(settle_time_ms),
                read_calibration("nits"),
                assert_threshold(
                    comparator=comparator,
                    threshold_value=value,
                    expected_source=expected_source,
                ),
            ]
        )
        generated.append(
            GeneratedCase(
                id=str(uuid4()),
                name=f"{source_spec_rule_name}-threshold-{rule_name}",
                case_type="threshold",
                source_spec_rule_id=source_spec_rule_id,
                status="Draft",
                to_confirm=False,
                steps=steps,
                expected={
                    "name": rule_name,
                    "comparator": comparator,
                    "value": value,
                    "expected_source": expected_source,
                    "settle_time_ms": settle_time_ms,
                },
                reference_ids=reference_ids,
            )
        )
    return generated


def _serialize_steps(actions: list[Action]) -> list[dict]:
    return [action.to_dict() for action in actions]
