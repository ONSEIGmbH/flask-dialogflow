.PHONY: test htmlcov typescov docs
.DEFAULT_GOAL := test


SRC = flask_dialogflow/
TESTS = test/


test:
	pytest

testcov:
	pytest --cov=$(SRC) --cov-report term $(TESTS)

htmltestcov:
	pytest --cov=$(SRC) --cov-report html $(TESTS)
	open htmlcov/index.html

mypy:
	mypy --config-file .mypy.ini $(SRC) $(TESTS)

mypycov:
	mypy --html-report typescov/ $(SRC) $(TESTS)
	open typescov/index.html

flake:
	flake8 --config=.flake8 $(SRC) $(TESTS)
	# Docstrings check
	#
	# Diabled for now as pydocstyle does not support Google style docstrings.
	# Watch this issue for updates: https://github.com/PyCQA/pydocstyle/issues/275
	# pydocstyle $(SRC)

lint:
	pylint $(SRC) $(TESTS)

# Build and open the Sphinx documentation in the default dir hierarchy
docs:
	cd docs/ && $(MAKE) html && open _build/html/index.html

clean: clean-build clean-pyc clean-test

# Remove build artifacts
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	cd docs/ && $(MAKE) clean

# Remove Python file artifacts
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

# Remove test and coverage artifacts
clean-test:
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -rf typescov/
	rm -rf .mypy_cache/
	rm -rf .pylint_cache/

# Run all inspections before a pull request
pr: clean test testcov mypy flake lint

