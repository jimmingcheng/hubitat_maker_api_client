venv: requirements-dev.txt
	virtualenv --python=python3.8 venv
	venv/bin/pip install -r requirements-dev.txt

.PHONY: test
test: venv
	venv/bin/pytest tests/

.PHONY: package
package: venv
	venv/bin/python setup.py sdist bdist_wheel

.PHONY: deploy-to-pypi
deploy-to-pypi: package
	twine upload dist/*

.PHONY: clean
clean:
	rm -fr dist/*
	rm -fr venv
