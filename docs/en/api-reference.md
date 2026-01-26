# API Reference

VTC-Link exposes a RESTful API for receiving vital signs data, health monitoring, and administrative operations. This document provides complete API specifications.

---

## Base URL

| Environment | Base URL |
|-------------|----------|
| Development | `http://localhost:8000` |
| Production | `https://your-domain.com` |

---

## Authentication

### Public Endpoints

The following endpoints do not require authentication:

- `GET /health` - Health check
- `POST /v1/push` - Push vitals (hospital-to-server)

### Admin Endpoints

All `/admin/*` endpoints require HTTP Basic Authentication:

```http
Authorization: Basic base64(username:password)
```

**Example:**
```bash
# Encode credentials
echo -n "admin:password" | base64
# Result: YWRtaW46cGFzc3dvcmQ=

# Make request
curl -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" \
  http://localhost:8000/admin/dashboard
```

Configure admin credentials via environment variables:
```bash
ADMIN_ID=admin
ADMIN_PASSWORD=your-secure-password
```

---

## API Endpoints

### Health Check

Check service health status.

```http
GET /health
```

#### Response

```json
{
  "status": "OK"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Service is healthy |

#### Example

=== "curl"

    ```bash
    curl http://localhost:8000/health
    ```

=== "Python"

    ```python
    import httpx

    response = httpx.get("http://localhost:8000/health")
    print(response.json())
    ```

---

### Push Vitals

Receive vital signs data from hospital systems (push connector).

```http
POST /v1/push
```

#### Request Body

Hospital-specific payload format. The payload is transformed using the configured transform profile.

**Example (HOSP_A format):**
```json
{
  "PAT_ID": "P12345",
  "PAT_NM": "John Doe",
  "BIRTH_DT": "19900101",
  "SEX_CD": "M",
  "WARD_CD": "ICU",
  "DEPT_CD": "IM",
  "SBP": "120",
  "DBP": "80",
  "PR": "72",
  "RR": "18",
  "BT": "36.5",
  "SPO2": "98.0",
  "REG_DT": "2024-01-15 10:30:00",
  "MOD_DT": "2024-01-15 10:30:00"
}
```

#### Response

**Success:**
```json
{
  "vital_id": "V67890",
  "patient_id": "P12345",
  "screened_type": "NORMAL",
  "screened_date": "20240115 10:30:00",
  "SEPS": 0,
  "MAES": 1,
  "MORS": 0,
  "NEWS": 2,
  "MEWS": 1
}
```

**Postprocess Failure:**
```json
{
  "status": "postprocess_failed",
  "error_code": "POSTPROCESS_KEY_MISSING"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Successfully processed |
| 422 | Validation error (invalid payload) |
| 500 | Internal server error |

#### Example

=== "curl"

    ```bash
    curl -X POST http://localhost:8000/v1/push \
      -H "Content-Type: application/json" \
      -d '{
        "PAT_ID": "P12345",
        "BIRTH_DT": "19900101",
        "SEX_CD": "M",
        "SBP": "120",
        "DBP": "80",
        "PR": "72",
        "RR": "18",
        "BT": "36.5",
        "SPO2": "98.0",
        "REG_DT": "2024-01-15 10:30:00",
        "MOD_DT": "2024-01-15 10:30:00"
      }'
    ```

=== "Python"

    ```python
    import httpx

    payload = {
        "PAT_ID": "P12345",
        "BIRTH_DT": "19900101",
        "SEX_CD": "M",
        "SBP": "120",
        "DBP": "80",
        "PR": "72",
        "RR": "18",
        "BT": "36.5",
        "SPO2": "98.0",
        "REG_DT": "2024-01-15 10:30:00",
        "MOD_DT": "2024-01-15 10:30:00"
    }

    response = httpx.post(
        "http://localhost:8000/v1/push",
        json=payload
    )
    print(response.json())
    ```

---

## Admin Endpoints

All admin endpoints require Basic Authentication.

### Dashboard

Render the admin dashboard page.

```http
GET /admin/dashboard
```

#### Response

HTML page displaying:

- Total hospitals configured
- Today's record count
- Success rate
- Error count
- Recent status summary
- Recent log entries

#### Example

```bash
curl -H "Authorization: Basic YWRtaW46YWRtaW4=" \
  http://localhost:8000/admin/dashboard
```

---

### Logs

View pipeline logs.

```http
GET /admin/logs
```

#### Response

HTML page displaying log entries with columns:

| Column | Description |
|--------|-------------|
| Timestamp | Event timestamp (UTC) |
| Level | Log level (INFO, WARNING, ERROR) |
| Event | Event type identifier |
| Hospital ID | Hospital identifier |
| Stage | Pipeline stage |
| Error Code | Error code (if applicable) |
| Message | Human-readable message |
| Duration (ms) | Operation duration |
| Record Count | Records processed |

#### Example

```bash
curl -H "Authorization: Basic YWRtaW46YWRtaW4=" \
  http://localhost:8000/admin/logs
```

---

### Status

View hospital status overview.

```http
GET /admin/status
```

#### Response

HTML page displaying status for each hospital:

| Column | Description |
|--------|-------------|
| Hospital ID | Hospital identifier |
| Last Run At | Last pipeline execution time |
| Last Success At | Last successful execution time |
| Last Status | Current status (success/failed) |
| Last Error Code | Most recent error code |
| PostProcess Fail Count | Consecutive failures |

#### Example

```bash
curl -H "Authorization: Basic YWRtaW46YWRtaW4=" \
  http://localhost:8000/admin/status
```

---

### Configuration - View

View current hospital configuration.

```http
GET /admin/config
```

#### Response

HTML form displaying current configuration values:

- Hospital settings
- Database configuration
- API configuration
- Postprocess settings

#### Example

```bash
curl -H "Authorization: Basic YWRtaW46YWRtaW4=" \
  http://localhost:8000/admin/config
```

---

### Configuration - Save

Save hospital configuration.

```http
POST /admin/config
Content-Type: application/x-www-form-urlencoded
```

#### Request Body (Form Data)

| Field | Type | Description |
|-------|------|-------------|
| `hospital-hospital_id` | string | Hospital identifier |
| `hospital-connector_type` | string | Connector type |
| `hospital-enabled` | string | "true" or "false" |
| `hospital-schedule_minutes` | string | Schedule interval |
| `hospital-transform_profile` | string | Transform profile name |
| `hospital-db-type` | string | Database type |
| `hospital-db-host` | string | Database host |
| `hospital-db-port` | string | Database port |
| `hospital-db-service` | string | Oracle service name |
| `hospital-db-database` | string | MSSQL database name |
| `hospital-db-username` | string | Database username |
| `hospital-db-password` | string | Database password |
| `hospital-db-view_name` | string | View name |
| `hospital-db-query` | string | Custom query |
| `hospital-api-url` | string | API URL |
| `hospital-api-api_key` | string | API key |
| `hospital-postprocess-mode` | string | Postprocess mode |
| `hospital-postprocess-table` | string | Target table |
| `hospital-postprocess-key_column` | string | Key column |
| `hospital-postprocess-key_value` | string | Static key value |
| `hospital-postprocess-key_value_source` | string | Key value source field |
| `hospital-postprocess-flag_column` | string | Flag column |
| `hospital-postprocess-flag_value` | string | Flag value |
| `hospital-postprocess-columns` | string | Comma-separated columns |
| `hospital-postprocess-values` | string | YAML values map |
| `hospital-postprocess-sources` | string | YAML sources map |
| `hospital-postprocess-retry` | string | Retry count |

#### Response

HTML page with:

- Updated configuration form
- Validation errors (if any)
- Success message (if saved)

#### Validation Rules

The endpoint validates:

1. Required fields are present
2. Connector type is valid
3. Database config is complete for DB connectors
4. API URL is present for REST connectors
5. Postprocess config is consistent

#### Example

```bash
curl -X POST -H "Authorization: Basic YWRtaW46YWRtaW4=" \
  -d "hospital-hospital_id=HOSP_A" \
  -d "hospital-connector_type=pull_db_view" \
  -d "hospital-enabled=true" \
  -d "hospital-schedule_minutes=5" \
  -d "hospital-transform_profile=HOSP_A" \
  http://localhost:8000/admin/config
```

---

## Data Models

### Canonical Payload

The normalized internal format for vital signs data:

```python
{
  "patient": {
    "patient_id": string,       # Required - Patient identifier
    "patient_name": string,     # Optional - Patient name
    "birthdate": string,        # Required - YYYYMMDD format
    "age": integer,             # Optional - Patient age
    "sex": string,              # Required - M or F
    "ward": string,             # Optional - Ward code (max 30 chars)
    "department": string        # Optional - Department code (max 30 chars)
  },
  "vitals": {
    "SBP": integer,             # Required - Systolic Blood Pressure
    "DBP": integer,             # Required - Diastolic Blood Pressure
    "PR": integer,              # Required - Pulse Rate
    "RR": integer,              # Required - Respiratory Rate
    "BT": float,                # Required - Body Temperature (Celsius)
    "SpO2": float               # Required - Oxygen Saturation (%)
  },
  "timestamps": {
    "created_at": string,       # Required - UTC ISO8601
    "updated_at": string        # Required - UTC ISO8601
  }
}
```

### Client Response

The response format from the backend analysis server:

```python
{
  "vital_id": string,           # Vital record identifier
  "patient_id": string,         # Patient identifier
  "screened_type": string,      # NORMAL, WARNING, EMERGENCY
  "screened_date": string,      # YYYYMMDD HH:MM:SS format
  "SEPS": integer,              # Sepsis score (0-6)
  "MAES": integer,              # MAES score
  "MORS": integer,              # Mortality risk score
  "NEWS": integer,              # National Early Warning Score
  "MEWS": integer               # Modified Early Warning Score
}
```

---

## Error Responses

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Authentication Error (401)

```json
{
  "detail": "Authentication required"
}
```

Response Headers:
```http
WWW-Authenticate: Basic
```

### Internal Server Error (500)

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, VTC-Link does not implement rate limiting. For production deployments, consider adding rate limiting via:

1. **Reverse Proxy** (recommended): Configure rate limits in nginx or Traefik
2. **Application Middleware**: Add FastAPI rate limiting middleware

### Nginx Rate Limiting Example

```nginx
http {
    limit_req_zone $binary_remote_addr zone=vtclink:10m rate=10r/s;

    server {
        location /v1/push {
            limit_req zone=vtclink burst=20 nodelay;
            proxy_pass http://vtclink:8000;
        }
    }
}
```

---

## OpenAPI Documentation

VTC-Link automatically generates OpenAPI documentation:

| URL | Description |
|-----|-------------|
| `/docs` | Swagger UI (interactive) |
| `/redoc` | ReDoc (alternative UI) |
| `/openapi.json` | OpenAPI JSON schema |

### Access Swagger UI

Navigate to `http://localhost:8000/docs` in your browser.

---

## API Versioning

The API uses URL path versioning:

| Version | Base Path | Status |
|---------|-----------|--------|
| v1 | `/v1/*` | Current |

### Future Versions

New API versions will be added as new path prefixes (e.g., `/v2/*`) while maintaining backward compatibility with existing versions.

---

## See Also

- [Configuration Guide](configuration.md) - API and backend configuration
- [Error Codes](error-codes.md) - Error code reference
- [Testing Guide](testing.md) - API testing examples
