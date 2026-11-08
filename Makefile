.PHONY: help install test check scan rules fix build selftest clean

PYTHON ?= python3

help:
	@echo "DocConcord 1.0.0 - available targets:"
	@echo "  make test       run the 40 unit tests (stdlib unittest)"
	@echo "  make check      self-audit the multilingual READMEs (CI gate)"
	@echo "  make scan       list discovered document families"
	@echo "  make rules      print the rule catalog"
	@echo "  make fix        preview safe auto-fix diffs"
	@echo "  make build      build wheel + sdist into dist/"
	@echo "  make selftest   full local verification loop"
	@echo "  make clean      remove build artifacts"

install:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) -m docconcord check . --format text --fail-on error

scan:
	$(PYTHON) -m docconcord scan .

rules:
	$(PYTHON) -m docconcord rules

fix:
	$(PYTHON) -m docconcord fix .

build:
	bash scripts/build.sh

selftest:
	bash scripts/selftest.sh

clean:
	rm -rf build dist src/*.egg-info *.egg-info .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
