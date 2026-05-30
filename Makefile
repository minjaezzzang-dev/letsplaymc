.PHONY: install dev install-test run lint format typecheck test clean \
        docker-build docker-run nuitka nuitka-debug distclean

SHELL := /bin/bash

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

install-test:
	pip install -e ".[test]"

install-nuitka:
	pip install nuitka

run:
	python src/main.py

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	pyright src/ tests/ 2>/dev/null || true

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

nuitka:
	python build.py

nuitka-debug:
	python build.py --debug

distclean: clean
	rm -rf dist/ *.spec *.build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .ruff_cache .pyrefly .mypy_cache build dist *.egg-info

docker-build:
	docker build -t letsplaymc .

docker-run:
	docker run --rm -v letsplaymc-data:/data letsplaymc
