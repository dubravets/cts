# 01 Data Model Schema

## Entities

- `Document`: uploaded source file with version metadata.
- `Reference`: source trace link (`doc_id`, `location`, `excerpt`).
- `Requirement`: normalized requirement statement with references.
- `SpecRule`: deterministic rule (including mapping rules) with references.
- `TestCase`: generated case with actions/assertions and references.
- `ProjectConfig`: project-level defaults (e.g., tolerance, settle time).

## Constraints

- Every `Requirement`, `SpecRule`, `TestCase` must include at least one `Reference`.
- Numeric expected values must come from `SpecRule` or `ProjectConfig`.
