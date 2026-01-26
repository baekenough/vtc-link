# Logging and Monitoring

VTC-Link provides comprehensive telemetry capabilities through a DuckDB-based logging system, enabling real-time monitoring, historical analysis, and operational insights for healthcare data integration pipelines.

---

## Overview

The telemetry system captures detailed operational data at every stage of the pipeline, from data fetch through postprocessing. All events are persisted in a lightweight DuckDB database, providing SQL-queryable access to operational metrics.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Pipeline       │────▶│  TelemetryStore │────▶│  DuckDB         │
│  Events         │     │  (Singleton)    │     │  (telemetry.db) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │  Admin UI       │
                        │  (Query/View)   │
                        └─────────────────┘
```

---

## DuckDB Telemetry Store

### Architecture

The `TelemetryStore` class implements a singleton pattern ensuring a single database connection is maintained throughout the application lifecycle:

```python
from app.core.telemetry import TelemetryStore

# Singleton access - same instance across all modules
store = TelemetryStore()
```

### Storage Location

By default, the telemetry database is stored at:

```
data/telemetry.duckdb
```

Configure the path via environment variable:

```bash
DUCKDB_PATH=./data/telemetry.duckdb
```

---

## Database Schema

### Logs Table

The primary table for storing pipeline events:

```sql
CREATE TABLE logs (
    timestamp    TIMESTAMP,     -- Event timestamp (UTC ISO8601)
    level        VARCHAR,       -- Log level (INFO, WARNING, ERROR)
    event        VARCHAR,       -- Event type identifier
    hospital_id  VARCHAR,       -- Hospital identifier
    stage        VARCHAR,       -- Pipeline stage
    error_code   VARCHAR,       -- Error code (if applicable)
    message      VARCHAR,       -- Human-readable message
    duration_ms  INTEGER,       -- Operation duration in milliseconds
    record_count INTEGER        -- Number of records processed
);
```

### Hospital Status Table

Tracks the current operational status of each configured hospital:

```sql
CREATE TABLE hospital_status (
    hospital_id           VARCHAR,    -- Hospital identifier
    last_run_at           TIMESTAMP,  -- Last pipeline execution time
    last_success_at       TIMESTAMP,  -- Last successful execution time
    last_status           VARCHAR,    -- Current status (success/failed)
    last_error_code       VARCHAR,    -- Most recent error code
    postprocess_fail_count INTEGER    -- Consecutive postprocess failures
);
```

---

## Event Types

### Pipeline Events

| Event | Level | Stage | Description |
|-------|-------|-------|-------------|
| `pipeline_start` | INFO | fetch | Pipeline execution initiated |
| `pipeline_complete` | INFO | postprocess | Pipeline completed successfully |
| `pipeline_failed` | ERROR | pipeline | Pipeline terminated with error |

### Postprocess Events

| Event | Level | Stage | Description |
|-------|-------|-------|-------------|
| `postprocess_failed` | ERROR | postprocess | Postprocessing operation failed |

### Example Event Flow

```
Timeline:
─────────────────────────────────────────────────────────────►
│                                                             │
▼                                                             ▼
pipeline_start ───▶ [fetch] ───▶ [transform] ───▶ pipeline_complete
    │                                                    │
    │ (on error)                                         │
    └────────────────▶ pipeline_failed ◀─────────────────┘
                            │
                            └──▶ postprocess_failed
```

---

## Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| **INFO** | Normal operations | Pipeline start, completion |
| **WARNING** | Non-critical issues | Retry attempts, slow operations |
| **ERROR** | Operation failures | Connection errors, parse failures |
| **DEBUG** | Detailed diagnostics | Query results, intermediate data |

---

## Metrics Collected

### Duration Tracking

Every pipeline execution records duration in milliseconds:

```python
duration_ms = int((end_time - start_time).total_seconds() * 1000)
```

!!! info "Performance Baseline"
    Typical healthy pipeline duration:

    - Database fetch: 50-500ms
    - REST API fetch: 100-2000ms
    - Transform: 10-50ms per record
    - Backend send: 50-200ms per record

### Record Count

Track the number of records processed in each pipeline run:

```python
log_event(
    "pipeline_complete",
    "INFO",
    hospital_id,
    "postprocess",
    "Pipeline completed",
    record_count=len(canonical_records),
    duration_ms=duration_ms
)
```

### Error Tracking

Failed operations capture error codes for troubleshooting:

```python
log_event(
    "postprocess_failed",
    "ERROR",
    hospital_id,
    "postprocess",
    "Postprocess failed",
    error_code="POSTPROCESS_KEY_MISSING",
    record_count=1
)
```

---

## Logging API

### log_event Function

The primary logging interface:

```python
from app.core.logger import log_event

log_event(
    event="pipeline_start",         # Event type identifier
    level="INFO",                   # Log level
    hospital_id="HOSP_A",          # Hospital identifier
    stage="fetch",                  # Pipeline stage
    message="Starting data fetch",  # Human-readable message
    error_code=None,                # Optional error code
    duration_ms=None,               # Optional duration
    record_count=None               # Optional record count
)
```

### Dual Output

Events are written to both:

1. **Standard Python logging** (for console/file output)
2. **DuckDB telemetry store** (for persistence and querying)

```python
# Internal implementation
logger.log(logging.INFO, message, extra={"event": event, ...})
TelemetryStore().insert_log({...})
```

---

## Querying Logs

### Using TelemetryStore

```python
from app.core.telemetry import TelemetryStore

store = TelemetryStore()

# Query all logs
all_logs = store.query_logs("", [])

# Query by hospital
hospital_logs = store.query_logs(
    "hospital_id = ?",
    ["HOSP_A"]
)

# Query errors
errors = store.query_logs(
    "level = ?",
    ["ERROR"]
)

# Query by date range
recent = store.query_logs(
    "timestamp > ?",
    ["2024-01-15T00:00:00Z"]
)
```

### SQL Query Examples

Connect directly to DuckDB for advanced queries:

```python
import duckdb

conn = duckdb.connect("data/telemetry.duckdb")

# Error frequency by hospital
conn.execute("""
    SELECT hospital_id, error_code, COUNT(*) as count
    FROM logs
    WHERE level = 'ERROR'
    GROUP BY hospital_id, error_code
    ORDER BY count DESC
""").fetchall()

# Average pipeline duration
conn.execute("""
    SELECT hospital_id,
           AVG(duration_ms) as avg_duration,
           MAX(duration_ms) as max_duration
    FROM logs
    WHERE event = 'pipeline_complete'
    GROUP BY hospital_id
""").fetchall()

# Records processed per day
conn.execute("""
    SELECT DATE_TRUNC('day', timestamp) as day,
           SUM(record_count) as total_records
    FROM logs
    WHERE event = 'pipeline_complete'
    GROUP BY day
    ORDER BY day DESC
""").fetchall()
```

---

## Hospital Status Monitoring

### Querying Status

```python
from app.core.telemetry import TelemetryStore

store = TelemetryStore()
status_list = store.query_status()

for status in status_list:
    hospital_id, last_run, last_success, status_text, error_code, fail_count = status
    print(f"{hospital_id}: {status_text} (failures: {fail_count})")
```

### Status Update Flow

```
Pipeline Run
     │
     ├── Success ───▶ update_status(last_status="success", fail_count=0)
     │
     └── Failure ───▶ update_status(last_status="failed", fail_count+=1)
```

---

## Admin UI Integration

### Logs Page

Access via: `GET /admin/logs`

Displays all logged events in a tabular format with columns:

- Timestamp
- Level
- Event
- Hospital ID
- Stage
- Error Code
- Message
- Duration (ms)
- Record Count

### Status Page

Access via: `GET /admin/status`

Shows real-time status of all configured hospitals:

- Hospital ID
- Last Run Time
- Last Success Time
- Current Status
- Last Error Code
- Postprocess Failure Count

### Dashboard

Access via: `GET /admin/dashboard`

Aggregated view with:

- Total hospitals configured
- Today's record count
- Success rate
- Error count
- Recent status summary
- Recent log entries

---

## Monitoring Best Practices

### 1. Set Up Alerting

Monitor for these critical conditions:

```python
# High failure rate
SELECT hospital_id,
       SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
FROM logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY hospital_id
HAVING error_rate > 10;  -- Alert if >10% errors
```

### 2. Track Pipeline Latency

```python
# Identify slow pipelines
SELECT hospital_id, AVG(duration_ms) as avg_ms
FROM logs
WHERE event = 'pipeline_complete'
  AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY hospital_id
HAVING avg_ms > 5000;  -- Alert if >5 seconds average
```

### 3. Monitor Postprocess Failures

```python
# Consecutive failures indicate systematic issues
SELECT hospital_id, postprocess_fail_count
FROM hospital_status
WHERE postprocess_fail_count >= 3;
```

### 4. Regular Health Checks

Create a monitoring script:

```python
#!/usr/bin/env python
from app.core.telemetry import TelemetryStore
from datetime import datetime, timedelta, timezone

store = TelemetryStore()

# Check for stale pipelines (no run in expected interval)
status_list = store.query_status()
now = datetime.now(timezone.utc)

for row in status_list:
    hospital_id, last_run_at, _, _, _, _ = row
    if last_run_at:
        last_run = datetime.fromisoformat(last_run_at.replace("Z", "+00:00"))
        if now - last_run > timedelta(minutes=15):
            print(f"ALERT: {hospital_id} pipeline stale")
```

### 5. Log Retention

Implement periodic cleanup for log retention:

```python
import duckdb

conn = duckdb.connect("data/telemetry.duckdb")

# Keep 30 days of logs
conn.execute("""
    DELETE FROM logs
    WHERE timestamp < NOW() - INTERVAL '30 days'
""")
```

---

## Troubleshooting

### No Logs Appearing

1. Check DuckDB path is writable:
   ```bash
   ls -la data/telemetry.duckdb
   ```

2. Verify TelemetryStore initialization:
   ```python
   from app.core.telemetry import TelemetryStore
   store = TelemetryStore()
   print(store._conn)  # Should show connection
   ```

### Query Performance

For large log tables, consider adding indexes:

```sql
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_hospital ON logs(hospital_id);
CREATE INDEX idx_logs_level ON logs(level);
```

### Disk Space

Monitor DuckDB file size:

```bash
du -h data/telemetry.duckdb
```

If growing too large, implement log rotation or archiving.

---

## See Also

- [Error Codes Reference](error-codes.md) - Complete error code documentation
- [Configuration Guide](configuration.md) - DuckDB path configuration
- [API Reference](api-reference.md) - Admin endpoints for log access
