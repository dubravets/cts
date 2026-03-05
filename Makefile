.PHONY: install db-init dev test lint

install:
	cd backend && python -m pip install --upgrade pip && pip install -e .[dev]

db-init:
	cd backend && python -m app.core.init_db

dev:
	cd backend && python -m app.core.init_db && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check .
