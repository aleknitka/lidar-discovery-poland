# Convenience targets. The real logic lives in the `ldp` CLI, so `uv run ldp dev` works
# everywhere, including Windows without make.
#
#   make dev     start the API and the web app together, open the browser
#   make mock    web app only, with fixture data (no API needed)

.DEFAULT_GOAL := help
.PHONY: help install dev mock api web test lint fmt build

help:  ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

install:  ## install Python and frontend dependencies
	uv sync
	cd frontend && npm install

dev:  ## start API + web app and open the browser (Ctrl+C stops both)
	uv run ldp dev

mock:  ## web app only, with fixture data
	uv run ldp dev --mock

api:  ## API only (http://127.0.0.1:8000)
	uv run ldp serve

web:  ## web app only (needs the API running)
	cd frontend && npm run dev

test:  ## backend and frontend tests
	uv run pytest
	cd frontend && npm test

lint:  ## ruff + eslint + type-check
	uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint && npx tsc --noEmit

fmt:  ## format Python code
	uv run ruff check --fix . && uv run ruff format .

build:  ## production build of the web app
	cd frontend && npm run build

verify:  ## one command to check everything (use this after any change)
	uv run ruff check . && uv run ruff format --check .
	uv run pytest
	cd frontend && npm run lint && npx tsc --noEmit && npm run build
	@echo "verify: all checks passed"
