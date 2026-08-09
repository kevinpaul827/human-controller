# Use the repository virtual environment when present.
ifeq ($(OS),Windows_NT)
PYTHON := $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,python)
else
PYTHON := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
endif

.PHONY: ptest app-check app-coverage backend-check backend-test backend-coverage frontend-build macos-app preview-local

ptest:
	$(PYTHON) -m unittest discover -s app -p 'test_*.py'

app-check:
	$(PYTHON) -m compileall app
	$(MAKE) ptest

app-coverage:
	$(PYTHON) -m compileall app
	$(PYTHON) -m coverage run --source=app -m unittest discover -s app/tests -p 'test_*.py'
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage xml -o coverage-app.xml

backend-check:
	$(PYTHON) -m compileall backend
	$(MAKE) backend-test

backend-test:
	$(PYTHON) -m pytest backend

backend-coverage:
	$(PYTHON) -m compileall backend
	$(PYTHON) -m coverage run --source=backend -m pytest backend
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage xml -o coverage-backend.xml

frontend-build:
	cd frontend && npm run build

macos-app:
	$(PYTHON) scripts/build_macos_app.py

preview-local:
	$(PYTHON) scripts/preview_local.py $(ARGS)
