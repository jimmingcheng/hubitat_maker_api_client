venv: poetry.lock
	python3 -m venv ./venv
	. venv/bin/activate && pip install poetry && poetry install

.PHONY: test
test: venv
	venv/bin/pytest tests/

.PHONY: package
package: venv
	venv/bin/python setup.py sdist bdist_wheel

.PHONY: deploy-to-pypi
deploy-to-pypi: package
	venv/bin/twine upload dist/*

.PHONY: clean
clean:
	rm -fr dist/*
	rm -fr venv
