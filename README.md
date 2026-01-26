# VTC-Link

**Vital Data Interface Server** - A hospital vital signs data integration proxy that normalizes patient data from various hospital systems and forwards it to backend processing servers.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

**[한국어 문서 (Korean)](README_ko.md)**

## Overview

VTC-Link serves as a middleware layer between hospital information systems and vital signs analysis backends. It handles the complexity of integrating with diverse hospital data sources while providing a unified interface for downstream processing.

### Key Features

- **Multi-Connector Support**: Connect to Oracle/MSSQL databases, REST APIs (pull/push)
- **Data Normalization**: Transform hospital-specific formats into a canonical schema
- **Scheduled Processing**: APScheduler-based background jobs for pull connectors
- **Admin Dashboard**: Web UI for configuration, monitoring, and log viewing
- **Postprocess Operations**: Update flags or insert logs after successful processing
- **Telemetry**: DuckDB-based event logging and status tracking

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Hospital HIS   │───▶│    VTC-Link     │───▶│  Backend API    │
│  (DB / REST)    │    │  (This Server)  │    │  (Analysis)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Admin UI      │
                       │  (Monitoring)   │
                       └─────────────────┘
```

### Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     PULL-BASED PIPELINE                          │
├──────────────────────────────────────────────────────────────────┤
│  Scheduler (interval)                                            │
│      ↓                                                           │
│  Fetch (Oracle/MSSQL/REST) → Raw Records                        │
│      ↓                                                           │
│  Transform: to_canonical() → CanonicalPayload                   │
│      ↓                                                           │
│  Backend: send_payload() → Analysis Results                      │
│      ↓                                                           │
│  Postprocess: update_flag / insert_log                          │
│      ↓                                                           │
│  Telemetry: log_event() → DuckDB                                │
└──────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | FastAPI 0.115+ |
| Runtime | Python 3.12, Uvicorn |
| Databases | Oracle (oracledb), MSSQL (pyodbc), DuckDB |
| Scheduling | APScheduler |
| HTTP Client | httpx |
| Validation | Pydantic v2 |
| Admin UI | Jinja2, HTML/CSS |

## Project Structure

```
vtc-link/
├── app/
│   ├── main.py                 # FastAPI application factory
│   ├── api/                    # API endpoints
│   │   ├── routes.py           # Route aggregator
│   │   ├── push.py             # Push vitals endpoint
│   │   ├── admin.py            # Admin UI & config management
│   │   └── health.py           # Health check
│   ├── core/                   # Business logic
│   │   ├── config.py           # Configuration management
│   │   ├── pipeline.py         # Pipeline orchestration
│   │   ├── scheduler.py        # APScheduler wrapper
│   │   ├── postprocess.py      # Post-pipeline DB operations
│   │   ├── db.py               # Database connections
│   │   └── telemetry.py        # DuckDB telemetry
│   ├── connectors/             # Data source connectors
│   │   ├── oracle_view_fetch.py
│   │   ├── mssql_view_fetch.py
│   │   ├── rest_pull_fetch.py
│   │   └── rest_push_receive.py
│   ├── transforms/             # Hospital-specific transforms
│   │   └── hospital_profiles/
│   │       └── HOSP_A/
│   ├── models/                 # Pydantic models
│   └── clients/                # Backend HTTP client
├── templates/                  # Jinja2 templates for admin UI
├── static/                     # CSS for admin UI
├── tests/                      # pytest test suite
├── docs/                       # Documentation (MkDocs)
└── docker-compose.yml          # Docker deployment
```

## Data Models

### Canonical Payload (Normalized Format)

```python
{
  "patient": {
    "patient_id": "P12345",
    "patient_name": "John Doe",
    "birthdate": "19900101",
    "age": 34,
    "sex": "M",
    "ward": "ICU",
    "department": "Internal Medicine"
  },
  "vitals": {
    "SBP": 120,      # Systolic Blood Pressure
    "DBP": 80,       # Diastolic Blood Pressure
    "PR": 72,        # Pulse Rate
    "RR": 18,        # Respiratory Rate
    "BT": 36.5,      # Body Temperature
    "SpO2": 98.0     # Oxygen Saturation
  },
  "timestamps": {
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Client Response (Backend Result)

```python
{
  "vital_id": "V67890",
  "patient_id": "P12345",
  "screened_type": "EMERGENCY",
  "screened_date": "20240115 10:30:00",
  "SEPS": 2,        # Sepsis Score
  "MAES": 1,        # MAES Score
  "MORS": 0,        # Mortality Score
  "NEWS": 3,        # National Early Warning Score
  "MEWS": 2         # Modified Early Warning Score
}
```

## Getting Started

### Prerequisites

- Python 3.12
- uv (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/baekenough/vtc-link.git
cd vtc-link

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Configuration

1. Copy and edit environment variables:
```bash
cp .env.example .env
```

2. Configure hospital settings in `hospitals.yaml`:
```yaml
hospital:
  hospital_id: "HOSP_A"
  connector_type: "pull_db_view"
  enabled: true
  schedule_minutes: 5
  transform_profile: "HOSP_A"
  db:
    type: "oracle"
    host: "localhost"
    port: 1521
    service: "ORCLCDB"
    username: "readonly"
    password: "readonly"
    view_name: "VITAL_VIEW"
```

### Running

```bash
# Development mode
./dev.sh
# or
uv run uvicorn app.main:app --reload

# Production (Docker)
docker-compose up -d
```

### Access Points

- **API**: http://localhost:8000
- **Admin Dashboard**: http://localhost:8000/admin/dashboard
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

## Connector Types

| Type | Description | Use Case |
|------|-------------|----------|
| `pull_db_view` | Poll database view on schedule | Hospital provides DB view access |
| `pull_rest_api` | Poll REST API on schedule | Hospital exposes REST endpoint |
| `push_rest_api` | Receive pushed data via REST | Hospital sends data actively |
| `push_db_insert` | Insert results back to hospital DB | Hospital wants results in their DB |

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_pipeline_logging.py
```

## Documentation

Full documentation is available at **[baekenough.github.io/vtc-link](https://baekenough.github.io/vtc-link/)**

- [Architecture](https://baekenough.github.io/vtc-link/architecture/)
- [Data Models](https://baekenough.github.io/vtc-link/data-model/)
- [Connectors](https://baekenough.github.io/vtc-link/connectors/)
- [Pipeline](https://baekenough.github.io/vtc-link/pipeline/)
- [Admin UI](https://baekenough.github.io/vtc-link/admin-ui/)
- [Deployment](https://baekenough.github.io/vtc-link/deployment/)

**[한국어 문서](https://baekenough.github.io/vtc-link/ko/)**

