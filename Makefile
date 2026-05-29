.PHONY: help build install clean test lint format

help:
	@echo "Available targets:"
	@echo "  build       Build wheel and sdist distributions"
	@echo "  install     Install package in editable mode"
	@echo "  clean       Remove build artifacts"
	@echo "  test        Run tests"
	@echo "  lint        Run linters (ruff)"
	@echo "  format      Format code (ruff)"

dist:
	@echo "Building kompress_tokens..."
	uv build
	@echo "✓ Build complete (see dist/)"

install:
	@echo "Installing kompress_tokens in editable mode..."
	uv pip install -e .
	@echo "✓ Installation complete"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info .eggs/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Clean complete"

test:
	@echo "Running tests..."
	uv run pytest -v
	@echo "✓ Tests complete"

lint:
	@echo "Linting code..."
	uv run ruff check src/
	@echo "✓ Lint complete"

format:
	@echo "Formatting code..."
	uv run ruff format src/
	uv run ruff check --fix src/
	@echo "✓ Format complete"
