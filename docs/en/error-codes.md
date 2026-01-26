# Error Code Reference

VTC-Link uses structured error codes to identify, categorize, and facilitate troubleshooting of failures throughout the data pipeline. This document provides a comprehensive reference for all error codes.

---

## Error Code Format

All error codes follow the format:

```
DOMAIN_STAGE_CODE
```

| Component | Description | Example |
|-----------|-------------|---------|
| **DOMAIN** | Functional area | `TX`, `DB`, `API`, `PP` |
| **STAGE** | Pipeline stage or operation | `PARSE`, `CONN`, `FETCH` |
| **CODE** | Numeric identifier | `001`, `002`, `003` |

### Example Breakdown

```
TX_PARSE_001
│  │     │
│  │     └── Error sequence number (001 = first parse error type)
│  └──────── Stage: PARSE (parsing/transformation)
└─────────── Domain: TX (Transform)
```

---

## Domain Reference

| Domain | Full Name | Description |
|--------|-----------|-------------|
| **TX** | Transform | Data parsing, normalization, and transformation errors |
| **DB** | Database | Database connection and query errors |
| **API** | API | REST API communication errors |
| **PP** | PostProcess | Post-pipeline operations (flag update, log insert) |
| **PIPE** | Pipeline | General pipeline execution errors |

---

## Error Codes by Domain

### TX (Transform) Errors

Transform errors occur during data parsing and normalization operations.

| Code | Name | Description | Cause |
|------|------|-------------|-------|
| `TX_PARSE_001` | Parse Error | Field parsing/normalization failed | Invalid data format in source field |
| `TX_DATE_001` | Date Parse Error | Date field parsing failed | Invalid date format |
| `TX_DATE_002` | Date Format Error | Date format mismatch | Source date doesn't match expected formats |
| `TX_INT_001` | Integer Parse Error | Integer field parsing failed | Non-numeric value in integer field |
| `TX_FLOAT_001` | Float Parse Error | Float field parsing failed | Non-numeric value in float field |
| `TX_REQUIRED_001` | Required Field Missing | Required field is null or empty | Missing mandatory field in source data |

#### TX Troubleshooting

=== "TX_PARSE_001"

    **Symptoms:**
    ```python
    ParseError: SBP: Integer expected, got 'abc'
    ```

    **Resolution:**

    1. Check source data quality:
       ```sql
       SELECT * FROM source_view WHERE SBP NOT REGEXP '^[0-9]+$'
       ```

    2. Update transform profile to handle edge cases:
       ```python
       def to_canonical(raw: dict) -> CanonicalPayload:
           sbp = raw.get("SBP")
           if sbp is None or str(sbp).strip() == "":
               sbp = 0  # Default value
           return CanonicalPayload(
               vitals=Vitals(SBP=parse_int(sbp, "SBP"), ...)
           )
       ```

=== "TX_DATE_002"

    **Symptoms:**
    ```python
    ParseError: birthdate: Unsupported format: 01-15-1990
    ```

    **Resolution:**

    1. Add the format to accepted formats:
       ```python
       BIRTHDATE_FORMATS = ["%Y%m%d", "%Y-%m-%d", "%m-%d-%Y"]
       ```

    2. Verify source system date configuration.

---

### DB (Database) Errors

Database errors occur during connection establishment and query execution.

| Code | Name | Description | Cause |
|------|------|-------------|-------|
| `DB_CONN_001` | Connection Failed | Database connection failed | Network/auth issue |
| `DB_CONN_002` | Connection Timeout | Connection timed out | Network latency or DB overload |
| `DB_QUERY_001` | Query Failed | SQL query execution failed | Invalid SQL or permission issue |
| `DB_QUERY_002` | No Results | Query returned no rows | Empty view or filter issue |
| `DB_CONFIG_001` | Config Missing | Required DB config missing | Incomplete hospitals.yaml |

#### DB Troubleshooting

=== "DB_CONN_001"

    **Symptoms:**
    ```
    ORA-12154: TNS:could not resolve the connect identifier
    ```

    **Resolution:**

    1. Verify connection parameters in `hospitals.yaml`:
       ```yaml
       db:
         type: "oracle"
         host: "10.0.1.100"      # Check IP/hostname
         port: 1521              # Check port
         service: "ORCLCDB"      # Check service name
         username: "readonly"
         password: "xxxxx"
       ```

    2. Test connectivity:
       ```bash
       telnet 10.0.1.100 1521
       ```

    3. Verify Oracle client is installed (for thin mode):
       ```python
       import oracledb
       oracledb.init_oracle_client()  # Optional for thick mode
       ```

=== "DB_CONN_002"

    **Symptoms:**
    ```
    Connection timeout after 30 seconds
    ```

    **Resolution:**

    1. Check network route to database server
    2. Verify firewall rules allow connection
    3. Check database server load and connection pool limits

=== "DB_QUERY_001"

    **Symptoms:**
    ```
    ORA-00942: table or view does not exist
    ```

    **Resolution:**

    1. Verify view name:
       ```yaml
       db:
         view_name: "VITAL_VIEW"  # Check exact name
       ```

    2. Check user permissions:
       ```sql
       GRANT SELECT ON VITAL_VIEW TO readonly;
       ```

---

### API (REST API) Errors

API errors occur during HTTP communication with external systems.

| Code | Name | Description | Cause |
|------|------|-------------|-------|
| `API_CONN_001` | Connection Refused | Cannot connect to API endpoint | Service down or wrong URL |
| `API_CONN_002` | Connection Timeout | API request timed out | Network latency or service overload |
| `API_AUTH_001` | Authentication Failed | API authentication failed | Invalid API key or credentials |
| `API_RESP_001` | Invalid Response | Response parsing failed | Unexpected response format |
| `API_RESP_002` | Error Response | API returned error status | 4xx or 5xx HTTP status |

#### API Troubleshooting

=== "API_CONN_001"

    **Symptoms:**
    ```
    httpx.ConnectError: Connection refused
    ```

    **Resolution:**

    1. Verify backend URL:
       ```bash
       BACKEND_BASE_URL=http://localhost:9000
       ```

    2. Test endpoint:
       ```bash
       curl -X POST http://localhost:9000/api/vitals \
         -H "Content-Type: application/json" \
         -d '{"test": true}'
       ```

    3. Check backend service status

=== "API_AUTH_001"

    **Symptoms:**
    ```
    HTTP 401 Unauthorized
    ```

    **Resolution:**

    1. Verify API key in `.env`:
       ```bash
       BACKEND_API_KEY=your-api-key-here
       ```

    2. Check key hasn't expired
    3. Verify key has correct permissions

---

### PP (PostProcess) Errors

PostProcess errors occur during post-pipeline operations like flag updates or log insertions.

| Code | Name | Description | Cause |
|------|------|-------------|-------|
| `POSTPROCESS_FAILED` | General Failure | Postprocess operation failed | Generic postprocess error |
| `POSTPROCESS_CONFIG_MISSING` | Config Missing | Required postprocess config missing | Incomplete postprocess config |
| `POSTPROCESS_KEY_MISSING` | Key Missing | Key value not found | No key_value or key_value_source |
| `POSTPROCESS_VALUE_MISSING` | Value Missing | Insert column value missing | Column not in values or sources |
| `POSTPROCESS_DB_UNSUPPORTED` | DB Unsupported | Database type not supported | Invalid db.type for postprocess |
| `POSTPROCESS_UNSUPPORTED` | Mode Unsupported | Postprocess mode not supported | Invalid postprocess.mode |

#### PP Troubleshooting

=== "POSTPROCESS_KEY_MISSING"

    **Symptoms:**
    ```
    Postprocess failed: POSTPROCESS_KEY_MISSING
    ```

    **Resolution:**

    1. Check postprocess configuration:
       ```yaml
       postprocess:
         mode: "update_flag"
         key_value_source: "vital_id"  # Must match canonical field
         # OR
         key_value: "static_value"     # Static key value
       ```

    2. Verify canonical payload contains the source field:
       ```python
       canonical = to_canonical(raw)
       print(canonical.model_dump())  # Check vital_id exists
       ```

=== "POSTPROCESS_CONFIG_MISSING"

    **Symptoms:**
    ```
    Postprocess failed: POSTPROCESS_CONFIG_MISSING
    ```

    **Resolution:**

    1. Verify all required fields are present:
       ```yaml
       postprocess:
         mode: "update_flag"
         table: "VITAL_VIEW"           # Required
         key_column: "ID"              # Required
         flag_column: "SENT_YN"        # Required
         flag_value: "Y"               # Required
       ```

=== "POSTPROCESS_VALUE_MISSING"

    **Symptoms:**
    ```
    Postprocess failed: POSTPROCESS_VALUE_MISSING
    ```

    **Resolution:**

    For `insert_log` mode, ensure all columns have values:
    ```yaml
    postprocess:
      mode: "insert_log"
      table: "VITAL_LOG"
      columns: [col1, col2, col3]
      values:
        col1: "static_value"
      sources:
        col2: "vital_id"      # From canonical payload
        col3: "patient_id"    # From canonical payload
    ```

---

### PIPE (Pipeline) Errors

Pipeline errors are general execution errors that don't fit other categories.

| Code | Name | Description | Cause |
|------|------|-------------|-------|
| `PIPE_STAGE_001` | Stage Failed | Pipeline stage execution failed | Uncaught exception in pipeline |
| `PIPE_INIT_001` | Init Failed | Pipeline initialization failed | Configuration or dependency issue |

#### PIPE Troubleshooting

=== "PIPE_STAGE_001"

    **Symptoms:**
    ```
    Pipeline failed with PIPE_STAGE_001
    ```

    **Resolution:**

    1. Check logs for underlying exception:
       ```python
       store.query_logs("error_code = ?", ["PIPE_STAGE_001"])
       ```

    2. Review message field for exception details
    3. Check connector configuration
    4. Verify transform profile matches hospital

---

## Error Recovery Matrix

| Error Code | Auto-Retry | Manual Action | Impact |
|------------|------------|---------------|--------|
| TX_PARSE_001 | No | Fix source data | Single record |
| TX_DATE_002 | No | Update format config | Single record |
| DB_CONN_001 | Yes (3x) | Check connectivity | All records |
| DB_CONN_002 | Yes (3x) | Check network | All records |
| API_CONN_001 | Yes (3x) | Check backend | All records |
| API_AUTH_001 | No | Update credentials | All records |
| POSTPROCESS_KEY_MISSING | Yes (configurable) | Fix config | Single record |
| POSTPROCESS_CONFIG_MISSING | No | Fix config | All records |
| PIPE_STAGE_001 | No | Investigate logs | All records |

---

## Recovery Procedures

### Automatic Retry

Postprocess operations support automatic retry:

```yaml
postprocess:
  mode: "update_flag"
  retry: 3  # Retry up to 3 times on failure
```

### Manual Recovery

For failed records that weren't processed:

1. **Query failed records:**
   ```sql
   SELECT * FROM logs
   WHERE level = 'ERROR'
     AND timestamp > '2024-01-15'
   ORDER BY timestamp DESC;
   ```

2. **Identify affected hospitals:**
   ```sql
   SELECT hospital_id, COUNT(*) as error_count
   FROM logs
   WHERE level = 'ERROR'
   GROUP BY hospital_id;
   ```

3. **Trigger manual pipeline run:**
   - Access Admin UI
   - Navigate to Configuration
   - Force pipeline execution (if implemented)

4. **Fix underlying issue and re-enable:**
   ```yaml
   hospital:
     enabled: true  # Re-enable after fix
   ```

---

## Error Monitoring

### Dashboard Integration

The Admin Dashboard shows:

- Recent errors with codes
- Error count by hospital
- Error rate trends

### Alert Thresholds

Recommended alert thresholds:

| Metric | Warning | Critical |
|--------|---------|----------|
| Error rate (hourly) | > 5% | > 20% |
| Consecutive failures | >= 3 | >= 5 |
| POSTPROCESS failures | >= 3 | >= 5 |

### Query Examples

**Recent errors by code:**
```sql
SELECT error_code, COUNT(*) as count, MAX(timestamp) as last_seen
FROM logs
WHERE level = 'ERROR' AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY error_code
ORDER BY count DESC;
```

**Error trend by hour:**
```sql
SELECT DATE_TRUNC('hour', timestamp) as hour,
       COUNT(*) as errors
FROM logs
WHERE level = 'ERROR'
GROUP BY hour
ORDER BY hour DESC
LIMIT 24;
```

---

## See Also

- [Logging and Monitoring](logging-monitoring.md) - Telemetry system overview
- [Configuration Guide](configuration.md) - Hospital and postprocess configuration
- [Troubleshooting](../troubleshooting.md) - General troubleshooting guide
