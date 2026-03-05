from __future__ import annotations

from app.generation.actions import assert_invalid, enter_menu, set_level
from app.generation.engine import GeneratedCase


def generate_invalid_cases(
    *,
    source_spec_rule_id: str,
    source_spec_rule_name: str,
    expression: dict,
    reference_ids: list[str],
) -> list[GeneratedCase]:
    invalid_levels = expression.get("invalid_levels", [])
    generated: list[GeneratedCase] = []
    for item in invalid_levels:
        level = str(item["level"])
        reason = str(item.get("reason", "invalid configuration"))
        generated.append(
            GeneratedCase(
                id=item.get("id", f"{source_spec_rule_id}:{level}"),
                name=f"{source_spec_rule_name}-invalid-{level}",
                case_type="invalid",
                source_spec_rule_id=source_spec_rule_id,
                status="Draft",
                to_confirm=False,
                steps=[
                    enter_menu("Display/Backlight").to_dict(),
                    set_level(level).to_dict(),
                    assert_invalid(reason).to_dict(),
                ],
                expected={
                    "level": level,
                    "reason": reason,
                    "expected_source": "spec_rule",
                },
                reference_ids=reference_ids,
            )
        )
    return generated
