# AGENTS.md — Cluster Test Management Project

## Goal
Build a test management system that parses Excel/Word requirement/spec documents and generates executable, traceable test cases.

## Non-negotiables (Quality Gates)
- Never invent numeric expectations (nits, %, ms, thresholds). Numeric expected values must come from SpecRule or ProjectConfig.
- Every generated Requirement/SpecRule/TestCase must include at least 1 Reference back to source doc.
- For mapping rules (level->nits), generated cases must include:
  - settle_time_ms (default 500ms unless overridden)
  - tolerance (default ±2% relative unless overridden)
  - calibration read step and an assertion step

## Repo structure
- backend/src/app/parsing: Excel/Word parsing
- backend/src/app/generation: case generation
- backend/src/app/quality: quality gates
- backend/src/app/export: xlsx export
- docs/specs: product specs (keep in sync)

## Dev commands
- make dev: start local stack (db + backend)
- make test: run unit tests
- make lint: formatting + lint

## Coding conventions
- Python 3.12, FastAPI, Pydantic v2
- Prefer small, testable functions.
- Add tests for parsers and quality gates.
- Keep deterministic logic outside LLM calls.
