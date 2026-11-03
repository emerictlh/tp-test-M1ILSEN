PYTHON = python

.PHONY: test unit_test perf_test coverage lint doc

test:
	$(PYTHON) -m pytest

unit_test:
	$(PYTHON) -m pytest -m "not performance"

perf_test:
	$(PYTHON) -m pytest -m performance -s

coverage:
	-$(PYTHON) -m coverage run --branch --source=triangulator -m pytest -m "not performance"
	$(PYTHON) -m coverage report -m
	$(PYTHON) -m coverage html

lint:
	$(PYTHON) -m ruff check

doc:
	$(PYTHON) -m pdoc --html --force -o docs triangulator
