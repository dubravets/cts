# 03 Generation, Quality, Export

## Generation

- Mapping rule inputs produce parameterized test cases.
- Generated cases include settle time, tolerance, calibration read, assertion.
- Deterministic logic remains outside LLM calls.

## Quality gates

- Fail if numeric expected value is not sourced from `SpecRule` or `ProjectConfig`.
- Fail if references are missing.

## Export

- Export generated test cases to XLSX with traceability columns.
