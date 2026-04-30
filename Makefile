install:
	python -m pip install -e .
dev:
	python -m pip install -e ".[dev]"
format:
	ruff format .
lint:
	ruff check .
	mypy src/shellforgeai tests
test:
	pytest -q
check:
	ruff format .
	ruff check .
	mypy src/shellforgeai tests
	pytest -q
demo:
	shellforgeai doctor
	shellforgeai inspect host
