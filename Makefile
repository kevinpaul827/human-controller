.PHONY: ptest app-check

ptest:
	python3 -m unittest discover -s app -p 'test_*.py'

app-check:
	python3 -m compileall app
	$(MAKE) ptest
