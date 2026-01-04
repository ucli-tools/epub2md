# epub2md Makefile
#
# Usage:
#   make          - Install epub2md system-wide
#   make build    - Same as make (install)
#   make rebuild  - Uninstall and reinstall
#   make delete   - Uninstall epub2md
#   make test     - Run tests on example files
#   make dev      - Set up local development environment
#

SCRIPT_NAME := epub2md.sh
INSTALL_NAME := epub2md

.PHONY: all build rebuild delete test dev clean check local-run local-run-fish

all: build

build:
	@echo "Installing epub2md..."
	@chmod +x $(SCRIPT_NAME)
	@bash $(SCRIPT_NAME) install

rebuild: delete build

delete:
	@echo "Uninstalling epub2md..."
	@bash $(SCRIPT_NAME) uninstall

check:
	@bash $(SCRIPT_NAME) check

# Development setup
dev:
	@echo "Setting up development environment..."
	@python3 -m venv .venv
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -e .
	@.venv/bin/pip install pytest pytest-cov black ruff
	@echo ""
	@echo "Development environment ready!"
	@echo "Activate with: source .venv/bin/activate"
	@echo "Or for fish:   source .venv/bin/activate.fish"

# Local run (for development without installing)
local-run:
	@source .venv/bin/activate && python -m epub2md $(ARGS)

local-run-fish:
	@source .venv/bin/activate.fish && python -m epub2md $(ARGS)

# Run tests
test: dev
	@echo "Running tests..."
	@mkdir -p test_output
	@.venv/bin/python -m epub2md convert \
		"../EPUB_AC_ORDERED/god_series/01 - The God Game (The God Series Book 1).epub" \
		test_output/god_game.md
	@echo ""
	@echo "Test output:"
	@head -50 test_output/god_game.md
	@echo ""
	@echo "Tests completed! Check test_output/ for results."

# Clean up build artifacts
clean:
	@echo "Cleaning up..."
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .pytest_cache/ .coverage htmlcov/
	@rm -rf test_output/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete!"

# Format code
format:
	@.venv/bin/black epub2md/
	@.venv/bin/ruff check epub2md/ --fix

# Lint code
lint:
	@.venv/bin/ruff check epub2md/
	@.venv/bin/black --check epub2md/

help:
	@echo "epub2md Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make          - Install epub2md system-wide"
	@echo "  make build    - Same as make (install)"
	@echo "  make rebuild  - Uninstall and reinstall"
	@echo "  make delete   - Uninstall epub2md"
	@echo "  make dev      - Set up local development environment"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Remove build artifacts"
	@echo "  make format   - Format code with black and ruff"
	@echo "  make lint     - Check code style"
	@echo "  make check    - Check prerequisites"
	@echo "  make help     - Show this help"
