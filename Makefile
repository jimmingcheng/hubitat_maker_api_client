# Variables
VENV := venv
PYTHON := $(VENV)/bin/python
POETRY := $(VENV)/bin/poetry

# Ensure virtual environment is created
.PHONY: venv
venv: $(VENV)/bin/activate

$(VENV)/bin/activate: pyproject.toml poetry.lock
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install poetry
	$(POETRY) install
	touch $(VENV)/bin/activate  # Mark venv as up-to-date

# Run tests
.PHONY: test
test: venv
	$(POETRY) run pytest tests/

# Build the package
.PHONY: package
package: venv
	rm -fr dist/*
	$(POETRY) build

# Publish to PyPI
.PHONY: deploy-to-pypi
deploy-to-pypi: package
	$(POETRY) publish

# Remove build artifacts but keep virtual environment
.PHONY: clean
clean:
	rm -fr dist/*

# Fully reset environment (including venv)
.PHONY: rebuild
rebuild: clean
	rm -fr $(VENV)
	make venv
