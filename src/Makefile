.PHONY: format lint test

GIT_ROOT ?= $(shell git rev-parse --show-toplevel)

format:
	black .
	isort .

lint:
	flake8 .
	black . --check

test:
	echo "Running tests for sherpa"
	pytest tests
	echo "Running tests for sherpa slackapp"
	cd apps/slackapp && pytest tests