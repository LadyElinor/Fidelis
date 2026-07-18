.PHONY: check verify test-python test-node import pull

check: verify test-python

verify:
	python scripts/verify_sources.py
	python scripts/verify_boundaries.py

test-python:
	python -m pytest -q

test-node:
	@if command -v pnpm >/dev/null 2>&1; then pnpm -r --if-present test; else echo "pnpm not installed; skipping Node tests"; fi

import:
	./scripts/sync_components.sh import

pull:
	./scripts/sync_components.sh pull
