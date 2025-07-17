# this_file: Makefile

.PHONY: help setup test build clean release lint format install dev-install

help:
	@echo "Available commands:"
	@echo "  setup      - Set up development environment"
	@echo "  test       - Run tests"
	@echo "  build      - Build the package"
	@echo "  clean      - Clean build artifacts"
	@echo "  release    - Create a release (requires VERSION=x.y.z)"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  install    - Install the package"
	@echo "  dev-install - Install in development mode"

setup:
	./scripts/dev-setup.sh

test:
	./scripts/test.sh

build:
	./scripts/build.sh

clean:
	rm -rf build/ dist/ src/*.egg-info/ htmlcov/ .coverage .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

release:
	@if [ -z "$(VERSION)" ]; then echo "Usage: make release VERSION=x.y.z"; exit 1; fi
	./scripts/release.sh $(VERSION)

lint:
	python3 -m flake8 src/ tests/
	python3 -m mypy src/ || true

format:
	python3 -m black src/ tests/

install:
	python3 -m pip install .

dev-install:
	python3 -m pip install -e .[testing,dev]

# Binary builds
build-binary:
	pyinstaller --onefile --name multinpainter src/multinpainter/__main__.py

# Version info
version:
	python3 -c "import multinpainter; print(multinpainter.__version__)"