# Configuration Guide

VTC-Link uses a layered configuration system combining environment variables for sensitive settings and YAML files for hospital-specific configurations. This guide covers all configuration options.

---

## Overview

Configuration is loaded from two primary sources:

```
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Sources                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────────────────────────┐ │
│  │    .env      │      │       hospitals.yaml             │ │
│  │              │      │                                  │ │
│  │ Environment  │      │  Hospital-specific settings:     │ │
│  │ variables:   │      │  - Connector type               │ │
│  │ - Secrets    │      │  - Database config              │ │
│  │ - Paths      │      │  - API config                   │ │
│  │ - Flags      │      │  - Transform profile            │ │
│  │              │      │  - Postprocess settings         │ │
│  └──────────────┘      └──────────────────────────────────┘ │
│          │                          │                       │
│          └───────────┬──────────────┘                       │
│                      ▼                                      │
│              ┌──────────────┐                               │
│              │   Settings   │                               │
│              │   (Pydantic) │                               │
│              └──────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

### Basic Configuration

Create a `.env` file in the project root:

```bash
# Environment mode: local, dev, prod
ENVIRONMENT=local

# Application version (readonly)
VERSION=0.1.0

# Logging level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

### Admin Authentication

```bash
# Admin UI credentials
ADMIN_ID=admin
ADMIN_PASSWORD=your-secure-password
```

!!! warning "Security"
    Change default admin credentials in production environments.

### Backend API

```bash
# Backend processing server
BACKEND_BASE_URL=http://localhost:9000
BACKEND_API_KEY=your-api-key
```

### Paths

```bash
# Hospital configuration file path
CONFIG_PATH=hospitals.yaml

# DuckDB telemetry database path
DUCKDB_PATH=data/telemetry.duckdb
```

### Scheduler

```bash
# Enable/disable background scheduler
SCHEDULER_ENABLED=true
```

### Complete .env Example

```bash
# Environment
ENVIRONMENT=prod
VERSION=0.1.0

# Logging
LOG_LEVEL=INFO

# Admin Authentication
ADMIN_ID=admin
ADMIN_PASSWORD=Str0ngP@ssw0rd!

# Backend API
BACKEND_BASE_URL=https://api.backend.example.com
BACKEND_API_KEY=sk-prod-xxxxxxxxxxxx

# Paths
CONFIG_PATH=hospitals.yaml
DUCKDB_PATH=data/telemetry.duckdb

# Scheduler
SCHEDULER_ENABLED=true
```

---

## Settings Model

The `Settings` class in `app/core/config.py` defines all environment variables:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    environment: Literal["local", "dev", "prod"] = "local"
    version: str = "0.1.0"
    log_level: str = "INFO"
    admin_id: str = "admin"
    admin_password: str = "admin"
    backend_base_url: str = "http://localhost:9000"
    backend_api_key: str = ""
    config_path: str = "hospitals.yaml"
    duckdb_path: str = "data/telemetry.duckdb"
    scheduler_enabled: bool = True
```

### Accessing Settings

```python
from app.core.config import get_settings

settings = get_settings()
print(settings.backend_base_url)
print(settings.log_level)
```

---

## hospitals.yaml Schema

### Top-Level Structure

```yaml
hospital:
  hospital_id: string      # Unique identifier
  connector_type: string   # Connector type
  enabled: boolean         # Enable/disable flag
  schedule_minutes: int    # Pull interval (pull connectors only)
  transform_profile: string # Transform profile name
  db: object              # Database configuration (optional)
  api: object             # API configuration (optional)
  postprocess: object     # Postprocess configuration (optional)
```

### Hospital Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hospital_id` | string | Yes | Unique identifier for the hospital |
| `connector_type` | string | Yes | One of: `pull_db_view`, `pull_rest_api`, `push_rest_api`, `push_db_insert` |
| `enabled` | boolean | No | Whether to enable this hospital (default: true) |
| `schedule_minutes` | integer | For pull connectors | Interval between scheduled fetches |
| `transform_profile` | string | Yes | Name of transform profile in `transforms/hospital_profiles/` |
| `db` | object | For DB connectors | Database connection settings |
| `api` | object | For REST connectors | API endpoint settings |
| `postprocess` | object | No | Post-pipeline operations |

---

## Connector Types

### pull_db_view

Polls a database view on a schedule:

```yaml
hospital:
  hospital_id: "HOSP_A"
  connector_type: "pull_db_view"
  enabled: true
  schedule_minutes: 5
  transform_profile: "HOSP_A"
  db:
    type: "oracle"        # or "mssql"
    host: "10.0.1.100"
    port: 1521
    service: "ORCLCDB"    # Oracle only
    database: "vitals"    # MSSQL only
    username: "readonly"
    password: "password"
    view_name: "VITAL_VIEW"
    query: "SELECT * FROM VITAL_VIEW WHERE SENT_YN = 'N'"
```

### pull_rest_api

Polls a REST API endpoint on a schedule:

```yaml
hospital:
  hospital_id: "HOSP_B"
  connector_type: "pull_rest_api"
  enabled: true
  schedule_minutes: 10
  transform_profile: "HOSP_B"
  api:
    url: "https://hospital-api.example.com/vitals"
    api_key: "sk-xxxx"
```

### push_rest_api

Receives pushed data via REST endpoint:

```yaml
hospital:
  hospital_id: "HOSP_C"
  connector_type: "push_rest_api"
  enabled: true
  transform_profile: "HOSP_C"
  # No schedule_minutes needed - triggered by incoming requests
```

### push_db_insert

Inserts results back to hospital database:

```yaml
hospital:
  hospital_id: "HOSP_D"
  connector_type: "push_db_insert"
  enabled: true
  transform_profile: "HOSP_D"
  db:
    type: "mssql"
    host: "10.0.2.100"
    port: 1433
    database: "vitals_results"
    username: "writer"
    password: "password"
    insert_table: "VITAL_RESULTS"
    insert_columns: ["patient_id", "vital_id", "score"]
```

---

## Database Configuration

### Oracle Database

```yaml
db:
  type: "oracle"

  # Connection options (choose one):
  # Option 1: Individual parameters
  host: "10.0.1.100"
  port: 1521
  service: "ORCLCDB"

  # Option 2: Full DSN string
  dsn: "10.0.1.100:1521/ORCLCDB"

  # Authentication
  username: "readonly"
  password: "password"

  # Query configuration
  view_name: "VITAL_VIEW"
  query: "SELECT * FROM VITAL_VIEW WHERE SENT_YN = 'N'"
```

### MSSQL Database

```yaml
db:
  type: "mssql"

  # Connection options (choose one):
  # Option 1: Individual parameters
  host: "10.0.2.100"
  port: 1433
  database: "VitalDB"
  driver: "ODBC Driver 18 for SQL Server"  # Optional

  # Option 2: Full connection string
  connection_string: "DRIVER={ODBC Driver 18 for SQL Server};SERVER=10.0.2.100;..."

  # Authentication
  username: "readonly"
  password: "password"

  # Query configuration
  view_name: "VITAL_VIEW"
  query: "SELECT * FROM VITAL_VIEW WHERE SENT_YN = 'N'"
```

### Database Field Reference

| Field | Oracle | MSSQL | Description |
|-------|--------|-------|-------------|
| `type` | Required | Required | Database type: "oracle" or "mssql" |
| `host` | Required | Required | Database server hostname or IP |
| `port` | Optional (1521) | Optional (1433) | Database port |
| `service` | Required | N/A | Oracle service name |
| `database` | N/A | Optional | MSSQL database name |
| `driver` | N/A | Optional | ODBC driver name |
| `dsn` | Alternative | N/A | Full Oracle DSN string |
| `connection_string` | N/A | Alternative | Full MSSQL connection string |
| `username` | Required | Required | Database username |
| `password` | Required | Required | Database password |
| `view_name` | Optional | Optional | View to query (default source) |
| `query` | Optional | Optional | Custom SQL query |

---

## API Configuration

### REST API Settings

```yaml
api:
  url: "https://hospital-api.example.com/vitals"
  api_key: "sk-xxxx"
```

| Field | Required | Description |
|-------|----------|-------------|
| `url` | For pull_rest_api | Full URL of the API endpoint |
| `api_key` | Optional | API key for authentication |

---

## PostProcess Configuration

PostProcess runs after successful data transmission to perform follow-up operations on the source database.

### Update Flag Mode

Updates a flag column to mark records as processed:

```yaml
postprocess:
  mode: "update_flag"
  table: "VITAL_VIEW"
  key_column: "ID"
  flag_column: "SENT_YN"
  flag_value: "Y"
  retry: 3

  # Key value options (choose one):
  key_value: "static_value"        # Static key
  key_value_source: "vital_id"     # From canonical payload
```

**Generated SQL:**
```sql
UPDATE VITAL_VIEW SET SENT_YN = 'Y' WHERE ID = ?
```

### Insert Log Mode

Inserts a log record for each processed item:

```yaml
postprocess:
  mode: "insert_log"
  table: "VITAL_LOG"
  columns: ["patient_id", "vital_id", "processed_at", "status"]
  retry: 3

  # Value sources:
  values:                          # Static values
    status: "SUCCESS"
  sources:                         # From canonical payload
    patient_id: "patient.patient_id"
    vital_id: "vital_id"
    processed_at: "timestamps.created_at"
```

**Generated SQL:**
```sql
INSERT INTO VITAL_LOG (patient_id, vital_id, processed_at, status)
VALUES (?, ?, ?, ?)
```

### PostProcess Field Reference

| Field | Mode | Required | Description |
|-------|------|----------|-------------|
| `mode` | All | Yes | "update_flag" or "insert_log" |
| `table` | All | Yes | Target table name |
| `retry` | All | No | Number of retry attempts (default: 3) |
| `key_column` | update_flag | Yes | Column to use in WHERE clause |
| `key_value` | update_flag | See below | Static key value |
| `key_value_source` | update_flag | See below | Canonical field for key value |
| `flag_column` | update_flag | Yes | Column to update |
| `flag_value` | update_flag | Yes | Value to set |
| `columns` | insert_log | Yes | List of columns to insert |
| `values` | insert_log | No | Static values for columns |
| `sources` | insert_log | No | Canonical field mappings |

!!! note "Key Value Resolution"
    For `update_flag` mode, either `key_value` or `key_value_source` must be provided.
    If `key_value_source` is set, it takes precedence and looks up the value from the canonical payload.

---

## Transform Profiles

Transform profiles are located in `app/transforms/hospital_profiles/{PROFILE_NAME}/`:

```
app/transforms/hospital_profiles/
└── HOSP_A/
    ├── __init__.py
    ├── inbound.py      # to_canonical() function
    ├── outbound.py     # to_backend(), from_backend() functions
    └── mapping.py      # Field mapping definitions
```

### Creating a Transform Profile

1. Create profile directory:
   ```bash
   mkdir -p app/transforms/hospital_profiles/HOSP_B
   ```

2. Create `inbound.py`:
   ```python
   from app.models.canonical import CanonicalPayload, Patient, Vitals, Timestamps
   from app.utils.parsing import parse_int, parse_float, parse_birthdate, parse_timestamp

   def to_canonical(raw: dict) -> CanonicalPayload:
       return CanonicalPayload(
           patient=Patient(
               patient_id=str(raw["PAT_ID"]),
               birthdate=parse_birthdate(raw["BIRTH_DT"], ["%Y%m%d"]),
               sex=raw["SEX_CD"],
           ),
           vitals=Vitals(
               SBP=parse_int(raw["SBP"], "SBP"),
               DBP=parse_int(raw["DBP"], "DBP"),
               # ... other vitals
           ),
           timestamps=Timestamps(
               created_at=parse_timestamp(raw["REG_DT"], ["%Y-%m-%d %H:%M:%S"]),
               updated_at=parse_timestamp(raw["MOD_DT"], ["%Y-%m-%d %H:%M:%S"]),
           )
       )
   ```

3. Reference in configuration:
   ```yaml
   hospital:
     transform_profile: "HOSP_B"
   ```

---

## Example Configurations

### Oracle Pull with Flag Update

```yaml
hospital:
  hospital_id: "HOSPITAL_A"
  connector_type: "pull_db_view"
  enabled: true
  schedule_minutes: 5
  transform_profile: "HOSP_A"
  db:
    type: "oracle"
    host: "oracle.hospital-a.local"
    port: 1521
    service: "VITALSDB"
    username: "vtclink"
    password: "secure_password"
    query: "SELECT * FROM V_VITAL_SIGNS WHERE SENT_YN = 'N'"
  postprocess:
    mode: "update_flag"
    table: "V_VITAL_SIGNS"
    key_column: "VITAL_ID"
    key_value_source: "vital_id"
    flag_column: "SENT_YN"
    flag_value: "Y"
    retry: 3
```

### MSSQL Pull with Log Insert

```yaml
hospital:
  hospital_id: "HOSPITAL_B"
  connector_type: "pull_db_view"
  enabled: true
  schedule_minutes: 10
  transform_profile: "HOSP_B"
  db:
    type: "mssql"
    host: "sql.hospital-b.local"
    port: 1433
    database: "VitalSigns"
    username: "vtclink_reader"
    password: "secure_password"
    view_name: "VitalSignsView"
  postprocess:
    mode: "insert_log"
    table: "ProcessingLog"
    columns: ["PatientID", "VitalID", "ProcessedAt", "Status"]
    sources:
      PatientID: "patient.patient_id"
      VitalID: "vital_id"
    values:
      Status: "SENT"
    retry: 2
```

### REST API Pull

```yaml
hospital:
  hospital_id: "HOSPITAL_C"
  connector_type: "pull_rest_api"
  enabled: true
  schedule_minutes: 15
  transform_profile: "HOSP_C"
  api:
    url: "https://api.hospital-c.com/v1/vitals/pending"
    api_key: "Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Push Receiver (Minimal)

```yaml
hospital:
  hospital_id: "HOSPITAL_D"
  connector_type: "push_rest_api"
  enabled: true
  transform_profile: "HOSP_D"
```

---

## Configuration Validation

The Admin UI validates configuration before saving:

### Required Validations

| Field | Validation |
|-------|------------|
| `hospital_id` | Non-empty string |
| `connector_type` | One of allowed values |
| `transform_profile` | Non-empty string |
| `schedule_minutes` | Positive integer (for pull connectors) |

### Conditional Validations

| Condition | Required Fields |
|-----------|-----------------|
| `connector_type` in [`pull_db_view`, `push_db_insert`] | `db.type`, `db.host` |
| `db.type` = "oracle" | `db.host`, `db.service` |
| `db.type` = "mssql" | `db.host` |
| `connector_type` = "pull_rest_api" | `api.url` |
| `postprocess.mode` = "update_flag" | `table`, `key_column`, `flag_column`, (`key_value` or `key_value_source`) |
| `postprocess.mode` = "insert_log" | `table`, `columns`, (values/sources for all columns) |

---

## Reloading Configuration

### Via Admin UI

1. Navigate to `/admin/config`
2. Make changes
3. Click Save
4. Configuration automatically reloads

### Programmatic Reload

```python
from app.core.config import reload_app_config

config = reload_app_config()  # Clears cache and reloads
```

### Scheduler Restart

When configuration is saved via Admin UI, the scheduler automatically restarts with new settings:

```python
if get_settings().scheduler_enabled:
    start_scheduler(reload_app_config())
```

---

## See Also

- [Deployment Guide](deployment.md) - Environment-specific configuration
- [Error Codes](error-codes.md) - Configuration-related error codes
- [API Reference](api-reference.md) - Admin configuration endpoints
