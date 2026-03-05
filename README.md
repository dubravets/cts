# cluster-test-mgmt

Codex-ready test management system scaffold.

## Quick start

```bash
gh repo clone dubravets/cts
cd cts
make install
make db-init
make dev
```

## Project layout

- `backend/`: FastAPI service
- `docs/specs/`: product and engineering specs
- `.github/workflows/`: CI + Codex PR review
- `.github/codex/prompts/`: reusable Codex prompts

## Development

```bash
make lint
make test
```
