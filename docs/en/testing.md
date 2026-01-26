# Testing Guide

VTC-Link uses pytest for comprehensive testing, including unit tests for individual components and integration tests for end-to-end workflows. This guide covers testing practices, running tests, and writing new tests.

---

## Overview

The testing strategy follows the testing pyramid:

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲        Few, slow, high-confidence
                 ╱──────╲
                ╱        ╲
               ╱Integration╲    Some, medium speed
              ╱────────────╲
             ╱              ╲
            ╱   Unit Tests   ╲  Many, fast, isolated
           ╱──────────────────╲
```

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_admin_config.py     # Admin UI configuration tests
├── test_parsing.py          # Parsing utility tests
├── test_pipeline_logging.py # Pipeline logging tests
├── test_postprocess.py      # Postprocess operation tests
└── test_scheduler.py        # Scheduler tests
```

---

## Running Tests

### Prerequisites

Ensure development dependencies are installed:

```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -e ".[dev]"
```

### Basic Test Execution

```bash
# Run all tests
uv run pytest

# Or with pip
pytest
```

### Verbose Output

```bash
# Show test names and results
uv run pytest -v

# Show print statements
uv run pytest -s

# Combined
uv run pytest -vs
```

### Run Specific Tests

```bash
# Run specific file
uv run pytest tests/test_postprocess.py

# Run specific test function
uv run pytest tests/test_postprocess.py::test_postprocess_no_config_returns_true

# Run tests matching pattern
uv run pytest -k "postprocess"

# Run tests by marker
uv run pytest -m "slow"
```

### Test Coverage

```bash
# Run with coverage
uv run pytest --cov=app

# Generate HTML report
uv run pytest --cov=app --cov-report=html

# View coverage in terminal
uv run pytest --cov=app --cov-report=term-missing
```

Coverage report will be generated in `htmlcov/index.html`.

---

## Test Categories

### Unit Tests

Unit tests verify individual functions and classes in isolation.

#### Parsing Tests (`test_parsing.py`)

Tests for data parsing utilities:

```python
def test_parse_int_valid():
    """Valid integer parsing"""
    assert parse_int("123", "SBP") == 123

def test_parse_int_invalid():
    """Invalid integer raises ParseError"""
    with pytest.raises(ParseError):
        parse_int("abc", "SBP")

def test_parse_float_valid():
    """Valid float parsing"""
    assert parse_float("36.5", "BT") == 36.5

def test_parse_birthdate():
    """Birthdate normalization"""
    assert parse_birthdate("19900101", ["%Y%m%d"]) == "19900101"

def test_parse_timestamp():
    """Timestamp to UTC ISO8601"""
    result = parse_timestamp("2024-01-01 10:00:00", ["%Y-%m-%d %H:%M:%S"])
    assert result.endswith("Z")

def test_coerce_int():
    """Coerce to integer with fallback"""
    assert coerce_int("10") == 10
    assert coerce_int("10.2") == 10
    assert coerce_int("invalid") == 0
```

#### Postprocess Tests (`test_postprocess.py`)

Tests for postprocess operations:

```python
def test_postprocess_no_config_returns_true():
    """No postprocess config returns success"""
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        postprocess=None,
    )
    ok, code = run_postprocess(hospital)
    assert ok is True
    assert code is None

def test_postprocess_missing_key_value_returns_false():
    """Missing key value returns error"""
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        postprocess={
            "mode": "update_flag",
            "table": "T",
            "key_column": "ID",
            "flag_column": "F",
            "flag_value": "Y",
            "retry": 1,
        },
        db={"type": "oracle"},
    )
    ok, code = run_postprocess(hospital, {"vital_id": "VID"})
    assert ok is False
    assert code == "POSTPROCESS_KEY_MISSING"
```

### Integration Tests

Integration tests verify component interactions.

#### Admin Config Tests (`test_admin_config.py`)

Tests for admin UI configuration endpoints:

```python
def _make_client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create test client with temporary config"""
    config_path = tmp_path / "hospitals.yaml"
    config_path.write_text(
        """hospital:\n  hospital_id: HOSP_A\n  connector_type: pull_db_view\n  enabled: true\n  schedule_minutes: 5\n  transform_profile: HOSP_A\n""",
        encoding="utf-8",
    )
    monkeypatch.setenv("CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "telemetry.duckdb"))
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    get_settings.cache_clear()
    load_app_config.cache_clear()
    app = create_app()
    return TestClient(app)

def test_admin_config_page_returns_401_without_auth(tmp_path, monkeypatch):
    """Config page requires authentication"""
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/admin/config")
    assert response.status_code == 401

def test_admin_config_save_returns_200_with_auth(tmp_path, monkeypatch):
    """Config save succeeds with auth"""
    client = _make_client(tmp_path, monkeypatch)
    headers = _basic_auth_header("admin", "admin")
    response = client.post("/admin/config", headers=headers, data={})
    assert response.status_code == 200
```

#### Pipeline Logging Tests (`test_pipeline_logging.py`)

Tests for telemetry logging during pipeline execution:

```python
def test_postprocess_failure_logs(tmp_path, monkeypatch):
    """Postprocess failure is logged to telemetry"""
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "telemetry.duckdb"))
    get_settings.cache_clear()
    store = TelemetryStore()

    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_rest_api",
        transform_profile="H1",
        enabled=True,
        postprocess={
            "mode": "update_flag",
            "table": "T",
            "key_column": "ID",
            "flag_column": "F",
            "flag_value": "Y",
            "retry": 1,
        },
        db={"type": "oracle"},
    )

    run_pull_pipeline(hospital)
    rows = store.query_logs("event = ?", ["postprocess_failed"])
    assert rows is not None
```

#### Scheduler Tests (`test_scheduler.py`)

Tests for scheduler functionality:

```python
def test_scheduler_start_without_pull_connector():
    """Scheduler starts even without pull connectors"""
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="push_rest_api",
        transform_profile="H1",
        enabled=True,
    )
    config = AppConfig(hospital=hospital)
    scheduler = start_scheduler(config)
    assert scheduler is not None
    scheduler.shutdown(wait=False)

def test_scheduler_restart_with_pull_connector():
    """Scheduler can be restarted with new config"""
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        enabled=True,
        schedule_minutes=1,
    )
    config = AppConfig(hospital=hospital)
    scheduler = start_scheduler(config)
    assert scheduler is not None
    scheduler.shutdown(wait=False)

    # Restart with new config
    hospital_b = HospitalConfig(
        hospital_id="H2",
        connector_type="pull_rest_api",
        transform_profile="H2",
        enabled=True,
        schedule_minutes=2,
    )
    config_b = AppConfig(hospital=hospital_b)
    scheduler_b = start_scheduler(config_b)
    assert scheduler_b is not None
    scheduler_b.shutdown(wait=False)
```

---

## Fixtures

### Common Fixtures (`conftest.py`)

Create shared fixtures in `tests/conftest.py`:

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_config(tmp_path):
    """Create temporary config file"""
    config_path = tmp_path / "hospitals.yaml"
    config_path.write_text("""
hospital:
  hospital_id: TEST_HOSPITAL
  connector_type: pull_db_view
  enabled: true
  schedule_minutes: 5
  transform_profile: TEST
""")
    return config_path

@pytest.fixture
def mock_settings(tmp_path, monkeypatch):
    """Configure settings for testing"""
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "hospitals.yaml"))
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "test.duckdb"))
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    from app.core.config import get_settings, load_app_config
    get_settings.cache_clear()
    load_app_config.cache_clear()

    return get_settings()

@pytest.fixture
def test_client(mock_settings):
    """Create FastAPI test client"""
    from fastapi.testclient import TestClient
    from app.main import create_app

    app = create_app()
    return TestClient(app)
```

### Using Fixtures

```python
def test_something(temp_config, mock_settings, test_client):
    """Test using multiple fixtures"""
    response = test_client.get("/health")
    assert response.status_code == 200
```

---

## Mocking

### Mocking Database Connections

```python
from unittest.mock import Mock, patch

def test_fetch_records_oracle():
    """Test Oracle fetch with mocked connection"""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.description = [("COL1",), ("COL2",)]
    mock_cursor.fetchall.return_value = [("val1", "val2")]
    mock_conn.cursor.return_value = mock_cursor

    with patch("app.core.db.oracledb.connect", return_value=mock_conn):
        from app.connectors.oracle_view_fetch import fetch_records
        from app.core.config import HospitalConfig

        config = HospitalConfig(
            hospital_id="H1",
            connector_type="pull_db_view",
            transform_profile="H1",
            db={"type": "oracle", "query": "SELECT * FROM V"}
        )

        result = fetch_records(config)
        assert result == [{"COL1": "val1", "COL2": "val2"}]
```

### Mocking HTTP Requests

```python
from unittest.mock import patch, Mock

def test_send_payload():
    """Test backend API call with mocked HTTP"""
    mock_response = Mock()
    mock_response.json.return_value = {"vital_id": "V123"}
    mock_response.raise_for_status = Mock()

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        from app.clients.backend_api import send_payload
        result = send_payload({"test": "data"})

        assert result["vital_id"] == "V123"
```

---

## Test Coverage

### Current Coverage Goals

| Module | Target | Reason |
|--------|--------|--------|
| `app/core/` | 90%+ | Critical business logic |
| `app/utils/` | 95%+ | Pure utility functions |
| `app/api/` | 80%+ | HTTP endpoints |
| `app/connectors/` | 70%+ | External integrations |

### Viewing Coverage Report

```bash
# Generate and open HTML report
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Coverage Configuration

Create `pyproject.toml` coverage section:

```toml
[tool.coverage.run]
source = ["app"]
omit = [
    "app/__init__.py",
    "app/*/test_*.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
]
```

---

## Writing New Tests

### Test Naming Conventions

```python
# Format: test_{function_name}_{scenario}_{expected_result}

def test_parse_int_valid_string_returns_integer():
    pass

def test_parse_int_invalid_string_raises_parse_error():
    pass

def test_postprocess_missing_config_returns_true():
    pass
```

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Set up test data and conditions
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        postprocess=None,
    )

    # Act - Execute the code being tested
    ok, code = run_postprocess(hospital)

    # Assert - Verify the results
    assert ok is True
    assert code is None
```

### Testing Exceptions

```python
import pytest

def test_parse_int_invalid_raises_error():
    with pytest.raises(ParseError) as exc_info:
        parse_int("abc", "SBP")

    assert "SBP" in str(exc_info.value)
    assert exc_info.value.code == "TX_PARSE_001"
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input_value,expected", [
    ("123", 123),
    ("  456  ", 456),
    ("0", 0),
    ("-10", -10),
])
def test_parse_int_valid_values(input_value, expected):
    assert parse_int(input_value, "field") == expected

@pytest.mark.parametrize("input_value", [
    "abc",
    "",
    None,
    "12.34",
])
def test_parse_int_invalid_values(input_value):
    with pytest.raises(ParseError):
        parse_int(input_value, "field")
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: coverage.xml
```

---

## Best Practices

### 1. Isolate Tests

Each test should be independent and not rely on other tests:

```python
# Good - uses fixtures for isolation
def test_example(tmp_path, monkeypatch):
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "test.duckdb"))
    # Test code...

# Bad - modifies global state
def test_example():
    os.environ["DUCKDB_PATH"] = "/tmp/test.duckdb"  # Affects other tests
```

### 2. Clear Cache Between Tests

```python
def test_config_change(monkeypatch):
    from app.core.config import get_settings, load_app_config

    # Clear caches before modifying environment
    get_settings.cache_clear()
    load_app_config.cache_clear()

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    settings = get_settings()
    assert settings.log_level == "DEBUG"
```

### 3. Use Descriptive Assertions

```python
# Good - clear failure message
def test_response_status():
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

# Better - use pytest's built-in assertion rewriting
def test_response_status():
    response = client.get("/health")
    assert response.status_code == 200  # pytest shows diff automatically
```

### 4. Clean Up Resources

```python
def test_scheduler():
    scheduler = start_scheduler(config)
    try:
        # Test code...
        assert scheduler.running
    finally:
        scheduler.shutdown(wait=False)  # Always clean up
```

---

## See Also

- [API Reference](api-reference.md) - Endpoint specifications for API tests
- [Configuration Guide](configuration.md) - Test configuration options
- [Error Codes](error-codes.md) - Error codes to test for
