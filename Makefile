.PHONY: test

test:
	.venv/bin/pytest -q

.PHONY: build

build:
	.venv/bin/python -m pip install build >/dev/null
	.venv/bin/python -m build
