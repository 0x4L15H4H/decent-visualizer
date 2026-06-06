.PHONY: dev lint format

dev:
	uv run uvicorn app.main:app --reload --port 8000

lint:
	uv run ruff check .

format:
	uv run ruff format .
