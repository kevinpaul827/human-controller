# Use local .venv if present (dev devices), else fall back to python3
PYTHON := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

.PHONY: ptest app-check backend-check backend-test frontend-build macos-app macos-sync-frontend macos-refresh-frontend

ptest:
	$(PYTHON) -m unittest discover -s app -p 'test_*.py'

app-check:
	$(PYTHON) -m compileall app
	$(MAKE) ptest

backend-check:
	$(PYTHON) -m compileall backend
	$(MAKE) backend-test

backend-test:
	$(PYTHON) -m pytest backend/matching_engine/tests

frontend-build:
	cd frontend && npm run build

macos-app:
	$(PYTHON) app/build_macos_app.py

macos-sync-frontend:
	$(PYTHON) app/sync_frontend_to_macos_app.py

macos-refresh-frontend: frontend-build macos-sync-frontend
