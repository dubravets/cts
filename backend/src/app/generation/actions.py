from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Action:
    kind: str
    params: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def enter_menu(path: str) -> Action:
    return Action(kind="EnterMenu", params={"path": path})


def set_level(level: str) -> Action:
    return Action(kind="SetLevel", params={"level": level})


def wait_ms(duration_ms: int) -> Action:
    return Action(kind="Wait", params={"duration_ms": duration_ms})


def read_calibration(metric: str = "nits") -> Action:
    return Action(kind="ReadCal", params={"metric": metric, "output_key": "actual_value"})


def assert_relative(
    *,
    expected_value: float,
    tolerance_percent: float,
    expected_source: str,
) -> Action:
    return Action(
        kind="AssertRelative",
        params={
            "expected_value": expected_value,
            "tolerance_percent": tolerance_percent,
            "actual_key": "actual_value",
            "expected_source": expected_source,
        },
    )


def assert_threshold(*, comparator: str, threshold_value: float, expected_source: str) -> Action:
    return Action(
        kind="AssertThreshold",
        params={
            "comparator": comparator,
            "threshold_value": threshold_value,
            "actual_key": "actual_value",
            "expected_source": expected_source,
        },
    )


def assert_invalid(reason: str) -> Action:
    return Action(kind="AssertInvalid", params={"reason": reason})
