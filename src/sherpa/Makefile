.PHONY: format lint test

GIT_ROOT ?= $(shell git rev-parse --show-toplevel)

format:
	black .
	isort .

lint:
	flake8 .
	black . --check

test:
	pytest .