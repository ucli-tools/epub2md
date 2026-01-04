# Contributing to epub2md

Thank you for your interest in contributing to epub2md! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/epub2md.git
   cd epub2md
   ```
3. Set up the development environment (see below)

## Development Setup

### Prerequisites

- Python 3.8 or higher
- [Pandoc](https://pandoc.org/installing.html)
- pip or uv for package management

### Setting Up

Using the Makefile:

```bash
make dev
```

Or manually:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (bash/zsh)
source .venv/bin/activate

# Or for fish shell
source .venv/bin/activate.fish

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Locally

After setting up:

```bash
# Run from development environment
python -m epub2md convert book.epub

# Or use the Makefile
make local-run ARGS="convert book.epub"
```

## Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting

### Formatting

```bash
make format
```

### Linting

```bash
make lint
```

### Style Guidelines

- Follow PEP 8 guidelines
- Maximum line length: 100 characters
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

## Testing

### Running Tests

```bash
make test
```

### Adding Tests

- Add test files in the `tests/` directory
- Name test files with `test_` prefix
- Use pytest for testing

## Submitting Changes

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request on GitHub

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests liberally

### Pull Request Guidelines

- Describe what the PR does and why
- Reference any related issues
- Include tests for new functionality
- Ensure all tests pass
- Update documentation if needed

## Reporting Issues

When reporting issues, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: How to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**:
   - OS and version
   - Python version
   - Pandoc version
   - epub2md version
6. **Sample File**: If possible, attach or link to an EPUB that demonstrates the issue

## Architecture

### Project Structure

```
epub2md/
├── epub2md/              # Python package
│   ├── __init__.py
│   ├── __main__.py       # Entry point for python -m epub2md
│   ├── cli.py            # Command-line interface
│   ├── converter.py      # Core conversion logic
│   ├── processors/       # Content processors
│   │   ├── cleanup.py    # Markdown cleanup
│   │   ├── images.py     # Image handling
│   │   └── metadata.py   # EPUB metadata extraction
│   └── utils/            # Utility modules
├── tests/                # Test files
├── examples/             # Example files
├── epub2md.sh            # Shell wrapper for install
├── Makefile              # Build automation
├── pyproject.toml        # Project configuration
└── README.md             # Documentation
```

### Adding New Processors

To add a new processor:

1. Create a new file in `epub2md/processors/`
2. Implement the processor function
3. Export it in `epub2md/processors/__init__.py`
4. Call it from `converter.py`

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Questions?

Feel free to open an issue for any questions about contributing!
