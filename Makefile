# Makefile

.PHONY: all test lint

all: test

test:
	$(MAKE) -C tests all

lint:
	$(MAKE) -C tests/junit-report lint
