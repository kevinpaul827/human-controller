.PHONY: ptest app-check backend-check

ptest:
	python3 -m unittest discover -s app -p 'test_*.py'

app-check:
	python3 -m compileall app
	$(MAKE) ptest

backend-check:
	python3 -m compileall backend
