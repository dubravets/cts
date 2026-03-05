from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityError:
    code: str
    case_id: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "case_id": self.case_id, "message": self.message}


@dataclass(frozen=True)
class QualityReport:
    passed: bool
    errors: list[QualityError]

    def as_dict(self) -> dict:
        return {"passed": self.passed, "errors": [item.as_dict() for item in self.errors]}


def validate_test_cases(cases: list[dict]) -> QualityReport:
    errors: list[QualityError] = []
    for case in cases:
        case_id = str(case["id"])
        refs = case.get("reference_ids", [])
        if not refs:
            errors.append(
                QualityError(
                    code="MISSING_REFERENCE",
                    case_id=case_id,
                    message="Test case must include at least one reference.",
                )
            )

        expected = case.get("expected", {})
        expected_source = expected.get("expected_source")
        if expected_source not in {"spec_rule", "project_config"}:
            errors.append(
                QualityError(
                    code="INVENTED_NUMERIC_EXPECTATION",
                    case_id=case_id,
                    message="Expected numeric values must come from SpecRule or ProjectConfig.",
                )
            )

        steps = case.get("steps", [])
        step_kinds = [step.get("kind") for step in steps]
        if case.get("case_type") == "mapping":
            for must_have in ("Wait", "ReadCal", "AssertRelative"):
                if must_have not in step_kinds:
                    errors.append(
                        QualityError(
                            code="MISSING_REQUIRED_STEP",
                            case_id=case_id,
                            message=f"Mapping case must include {must_have}.",
                        )
                    )

            settle_value = expected.get("settle_time_ms")
            tolerance_value = expected.get("tolerance_percent")
            if settle_value is None or tolerance_value is None:
                errors.append(
                    QualityError(
                        code="MISSING_MAPPING_DEFAULTS",
                        case_id=case_id,
                        message="Mapping case must include settle_time_ms and tolerance.",
                    )
                )

    return QualityReport(passed=not errors, errors=errors)
