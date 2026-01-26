# Contributing Guide

Thank you for your interest in contributing to VTC-Link! This document provides guidelines for contributing to the project, including development setup, coding standards, and the pull request process.

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We expect all contributors to:

- Be respectful and constructive in discussions
- Focus on the technical merits of contributions
- Welcome newcomers and help them learn
- Accept constructive criticism gracefully

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- uv (recommended) or pip
- Git
- Docker (for integration testing)

### Development Setup

1. **Fork and clone the repository**

   ```bash
   # Fork via GitHub UI, then:
   git clone https://github.com/YOUR-USERNAME/vtc-link.git
   cd vtc-link
   ```

2. **Set up the development environment**

   ```bash
   # Install uv if not already installed
   pip install uv

   # Create virtual environment and install dependencies
   uv sync

   # Or with pip
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

4. **Run tests to verify setup**

   ```bash
   uv run pytest
   ```

5. **Start development server**

   ```bash
   uv run uvicorn app.main:app --reload
   ```

---

## Development Workflow

### Branch Strategy

We use a feature branch workflow:

```
main
  │
  ├── feature/add-new-connector
  ├── feature/improve-error-handling
  ├── fix/postprocess-retry-bug
  └── docs/update-api-reference
```

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/description` | `feature/add-postgresql-connector` |
| Bug Fix | `fix/description` | `fix/scheduler-memory-leak` |
| Documentation | `docs/description` | `docs/update-deployment-guide` |
| Refactoring | `refactor/description` | `refactor/simplify-pipeline` |
| Testing | `test/description` | `test/add-connector-tests` |

### Creating a Feature Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

---

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications. Use the provided tooling to ensure consistency:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy app/
```

### Configuration

Our `pyproject.toml` includes style configuration:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
```

### Code Conventions

#### Imports

```python
# Standard library
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Iterator

# Third-party
import duckdb
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# Local
from app.core.config import get_settings
from app.core.telemetry import TelemetryStore
```

#### Type Hints

Always use type hints for function signatures:

```python
def parse_int(value: str | int | float | None, field: str) -> int:
    """Parse value to integer.

    Args:
        value: Value to parse
        field: Field name for error messages

    Returns:
        Parsed integer value

    Raises:
        ParseError: If parsing fails
    """
    ...
```

#### Docstrings

Use Google-style docstrings:

```python
def fetch_records(config: HospitalConfig) -> list[dict]:
    """Fetch records from database view.

    Connects to the configured database and executes the query
    specified in the hospital configuration.

    Args:
        config: Hospital configuration with database settings

    Returns:
        List of record dictionaries with column names as keys

    Raises:
        ValueError: If database configuration is missing
        DatabaseError: If connection or query fails
    """
    ...
```

#### Error Handling

```python
# Use specific exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

# Raise with context
raise ParseError("birthdate", f"Unsupported format: {value}")

# Handle gracefully
try:
    result = parse_int(value, "SBP")
except ParseError as e:
    log_event("parse_error", "ERROR", hospital_id, "transform", e.message, error_code=e.code)
    raise
```

---

## Testing Requirements

### Test Coverage

All contributions must include tests:

| Change Type | Test Requirement |
|-------------|------------------|
| New feature | Unit tests + integration test |
| Bug fix | Test that reproduces the bug |
| Refactoring | Ensure existing tests pass |
| API change | Update API tests |

### Writing Tests

Follow existing test patterns:

```python
import pytest
from app.core.config import HospitalConfig
from app.core.postprocess import run_postprocess

def test_postprocess_update_flag_success(mock_db_connection):
    """Update flag postprocess succeeds with valid config."""
    # Arrange
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        postprocess={
            "mode": "update_flag",
            "table": "VITAL_VIEW",
            "key_column": "ID",
            "key_value_source": "vital_id",
            "flag_column": "SENT_YN",
            "flag_value": "Y",
        },
        db={"type": "oracle"},
    )
    record = {"vital_id": "V123"}

    # Act
    ok, code = run_postprocess(hospital, record)

    # Assert
    assert ok is True
    assert code is None
    mock_db_connection.execute.assert_called_once()
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run specific tests
uv run pytest tests/test_postprocess.py -v

# Run tests matching pattern
uv run pytest -k "postprocess"
```

---

## Pull Request Process

### Before Submitting

1. **Ensure tests pass**
   ```bash
   uv run pytest
   ```

2. **Format and lint code**
   ```bash
   uv run ruff format .
   uv run ruff check .
   ```

3. **Update documentation** if needed

4. **Write meaningful commit messages**

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(connector): add PostgreSQL connector support

Implements a new connector for PostgreSQL databases,
supporting both pull and push modes.

Closes #42
```

```
fix(postprocess): handle null key values correctly

Previously, null key values would cause a silent failure.
Now properly returns POSTPROCESS_KEY_MISSING error.

Fixes #38
```

### Submitting a Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create pull request** via GitHub UI

3. **Fill out the PR template:**
   ```markdown
   ## Summary
   Brief description of changes

   ## Changes
   - Added X
   - Modified Y
   - Fixed Z

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests pass
   - [ ] Manual testing completed

   ## Documentation
   - [ ] README updated (if needed)
   - [ ] API docs updated (if needed)

   ## Related Issues
   Closes #123
   ```

4. **Request review** from maintainers

### Review Process

- At least one approval required
- All CI checks must pass
- Address all review comments
- Squash commits before merge (if requested)

---

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Configure hospitals.yaml with...
2. Start the server
3. Send request to...
4. Observe error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Ubuntu 22.04
- Python: 3.12.1
- VTC-Link: 0.1.0

## Logs
```
Relevant log output
```

## Additional Context
Any other relevant information
```

### Feature Requests

Use the feature request template:

```markdown
## Summary
Brief description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches considered

## Additional Context
Any other relevant information
```

---

## Project Structure

Understanding the project structure helps with contributions:

```
vtc-link/
├── app/
│   ├── api/              # API endpoints
│   │   ├── admin.py      # Admin UI endpoints
│   │   ├── health.py     # Health check
│   │   ├── push.py       # Push endpoint
│   │   └── routes.py     # Route aggregator
│   ├── clients/          # External API clients
│   │   └── backend_api.py
│   ├── connectors/       # Data source connectors
│   │   ├── oracle_view_fetch.py
│   │   ├── mssql_view_fetch.py
│   │   └── rest_pull_fetch.py
│   ├── core/             # Core business logic
│   │   ├── config.py     # Configuration
│   │   ├── db.py         # Database connections
│   │   ├── errors.py     # Custom exceptions
│   │   ├── logger.py     # Logging
│   │   ├── pipeline.py   # Pipeline orchestration
│   │   ├── postprocess.py
│   │   ├── scheduler.py
│   │   └── telemetry.py  # DuckDB telemetry
│   ├── models/           # Pydantic models
│   │   └── canonical.py
│   ├── transforms/       # Hospital transforms
│   │   └── hospital_profiles/
│   └── utils/            # Utilities
│       └── parsing.py
├── tests/                # Test suite
├── docs/                 # Documentation
├── templates/            # Jinja2 templates
└── static/               # Static files
```

---

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and discussions
- **Pull Request Comments**: Code-specific questions

### Resources

- [Testing Guide](testing.md) - How to write and run tests
- [API Reference](api-reference.md) - API documentation
- [Configuration Guide](configuration.md) - Configuration options

---

## Recognition

Contributors are recognized in:

- GitHub contributors list
- Release notes for significant contributions
- CONTRIBUTORS.md file

Thank you for contributing to VTC-Link!
