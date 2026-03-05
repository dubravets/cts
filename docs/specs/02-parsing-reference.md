# 02 Parsing Reference

## Excel parsing (v1)

- Expand merged cells before row extraction.
- Preserve source coordinates for traceability.
- Emit row-level `Reference` for extracted requirements/rules.

## Word parsing (v1)

- Parse heading outlines, including section `4.3` style paths.
- Extract mapping tables and detect level->value mappings.
- Attach `Reference` with heading path and table cell coordinates.
