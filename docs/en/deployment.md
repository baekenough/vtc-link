# Deployment Guide

This guide covers deploying VTC-Link in various environments, from development to production. It includes Docker deployment, configuration best practices, and production readiness checklists.

---

## Deployment Options

| Method | Use Case | Complexity |
|--------|----------|------------|
| Direct (uvicorn) | Development | Low |
| Docker | Single server | Medium |
| Docker Compose | Multi-container | Medium |
| Kubernetes | Enterprise scale | High |

---

## Development Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/vtc-link.git
cd vtc-link

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Development Script

Use the provided development script:

```bash
./dev.sh
```

This runs uvicorn with:
- Auto-reload on code changes
- Debug logging
- Local binding

---

## Docker Deployment

### Dockerfile

Create a production-ready Dockerfile:

```dockerfile
# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev --frozen

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    unixodbc \
    libodbc1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/
COPY hospitals.yaml .

# Create data directory
RUN mkdir -p /app/data

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Building the Image

```bash
# Build image
docker build -t vtc-link:latest .

# Build with version tag
docker build -t vtc-link:1.0.0 .

# Build for specific platform
docker build --platform linux/amd64 -t vtc-link:latest .
```

### Running with Docker

```bash
# Basic run
docker run -d \
  --name vtc-link \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/hospitals.yaml:/app/hospitals.yaml:ro \
  vtc-link:latest

# With environment variables
docker run -d \
  --name vtc-link \
  -p 8000:8000 \
  -e ENVIRONMENT=prod \
  -e LOG_LEVEL=INFO \
  -e BACKEND_BASE_URL=https://api.example.com \
  -e BACKEND_API_KEY=sk-xxxx \
  -e ADMIN_PASSWORD=secure_password \
  -v $(pwd)/data:/app/data \
  vtc-link:latest
```

### Docker Management

```bash
# View logs
docker logs -f vtc-link

# Stop container
docker stop vtc-link

# Remove container
docker rm vtc-link

# View resource usage
docker stats vtc-link
```

---

## Docker Compose Setup

### docker-compose.yml

```yaml
version: "3.8"

services:
  vtc-link:
    build: .
    image: vtc-link:latest
    container_name: vtc-link
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=prod
      - LOG_LEVEL=INFO
      - DUCKDB_PATH=/app/data/telemetry.duckdb
      - CONFIG_PATH=/app/config/hospitals.yaml
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./config:/app/config:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - vtc-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  vtc-network:
    driver: bridge
```

### Production docker-compose.yml

For production with reverse proxy:

```yaml
version: "3.8"

services:
  vtc-link:
    build: .
    image: vtc-link:latest
    container_name: vtc-link
    restart: unless-stopped
    expose:
      - "8000"
    environment:
      - ENVIRONMENT=prod
      - LOG_LEVEL=WARNING
    env_file:
      - .env.prod
    volumes:
      - vtc-data:/app/data
      - ./config:/app/config:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - vtc-network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

  nginx:
    image: nginx:alpine
    container_name: vtc-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - vtc-link
    networks:
      - vtc-network

volumes:
  vtc-data:

networks:
  vtc-network:
    driver: bridge
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream vtc-link {
        server vtc-link:8000;
    }

    server {
        listen 80;
        server_name vtc-link.example.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name vtc-link.example.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

        location / {
            proxy_pass http://vtc-link;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /v1/push {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://vtc-link;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /health {
            proxy_pass http://vtc-link;
            access_log off;
        }
    }
}
```

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild and restart
docker-compose up -d --build

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Environment Configuration

### Development (.env.dev)

```bash
ENVIRONMENT=dev
LOG_LEVEL=DEBUG
ADMIN_ID=admin
ADMIN_PASSWORD=admin
BACKEND_BASE_URL=http://localhost:9000
BACKEND_API_KEY=dev-key
SCHEDULER_ENABLED=true
DUCKDB_PATH=data/telemetry.duckdb
```

### Production (.env.prod)

```bash
ENVIRONMENT=prod
LOG_LEVEL=WARNING
ADMIN_ID=vtc_admin
ADMIN_PASSWORD=${ADMIN_PASSWORD}  # Set via environment
BACKEND_BASE_URL=https://api.backend.example.com
BACKEND_API_KEY=${BACKEND_API_KEY}  # Set via environment
SCHEDULER_ENABLED=true
DUCKDB_PATH=/app/data/telemetry.duckdb
```

### Secrets Management

For production, use environment variables or secrets management:

```bash
# Docker secrets
echo "secure_password" | docker secret create admin_password -

# Kubernetes secrets
kubectl create secret generic vtc-link-secrets \
  --from-literal=admin-password=secure_password \
  --from-literal=backend-api-key=sk-xxxx
```

---

## Health Checks

### Application Health Endpoint

The `/health` endpoint returns service status:

```bash
curl http://localhost:8000/health
# Response: {"status": "OK"}
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
```

---

## Scaling Considerations

### Horizontal Scaling

VTC-Link can be horizontally scaled with some considerations:

#### Stateless Components
- API endpoints (push, health)
- Transform operations

#### Stateful Components
- Scheduler (requires coordination)
- DuckDB telemetry (requires shared storage or separate instances)

### Scaling Strategy

```
                     Load Balancer
                          │
              ┌───────────┼───────────┐
              │           │           │
         ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
         │ VTC-1   │ │ VTC-2   │ │ VTC-3   │
         │ (Push)  │ │ (Push)  │ │ (Push)  │
         └────────┘ └─────────┘ └─────────┘
              │           │           │
              └───────────┼───────────┘
                          │
                   ┌──────▼──────┐
                   │  Scheduler  │
                   │  (Single)   │
                   └─────────────┘
```

### Recommendations

1. **Single Scheduler Instance**: Run scheduler on only one instance to prevent duplicate jobs
2. **Shared Telemetry**: Use external database (PostgreSQL) for telemetry if scaling
3. **Session Affinity**: Enable sticky sessions if using admin UI across instances

---

## Production Checklist

### Security

- [ ] Change default admin credentials
- [ ] Use HTTPS in production
- [ ] Configure firewall rules
- [ ] Rotate API keys regularly
- [ ] Review file permissions
- [ ] Enable security headers (via reverse proxy)

### Configuration

- [ ] Set `ENVIRONMENT=prod`
- [ ] Set `LOG_LEVEL=WARNING` or `INFO`
- [ ] Configure backend API URL and key
- [ ] Verify hospitals.yaml configuration
- [ ] Test database connectivity
- [ ] Verify postprocess operations

### Monitoring

- [ ] Configure health check monitoring
- [ ] Set up log aggregation
- [ ] Configure alerting thresholds
- [ ] Monitor disk space for DuckDB
- [ ] Set up performance monitoring

### Backup

- [ ] Schedule DuckDB backup
- [ ] Backup hospitals.yaml
- [ ] Document recovery procedures
- [ ] Test restore procedures

### High Availability

- [ ] Configure container restart policy
- [ ] Set up health check-based restarts
- [ ] Plan for database failover
- [ ] Document incident response

---

## Troubleshooting Deployment

### Container Won't Start

```bash
# Check logs
docker logs vtc-link

# Common issues:
# - Missing environment variables
# - Invalid hospitals.yaml
# - Port already in use
```

### Database Connection Fails

```bash
# Test connectivity from container
docker exec vtc-link python -c "
import oracledb
conn = oracledb.connect(user='readonly', password='xxx', dsn='host:1521/service')
print('Connected!')
"

# Check DNS resolution
docker exec vtc-link nslookup database-host
```

### Health Check Failing

```bash
# Test from inside container
docker exec vtc-link curl -f http://localhost:8000/health

# Check application logs
docker logs vtc-link | grep -i error
```

### Performance Issues

```bash
# Check resource usage
docker stats vtc-link

# View process list
docker exec vtc-link ps aux

# Check DuckDB size
docker exec vtc-link du -h /app/data/telemetry.duckdb
```

---

## Maintenance

### Log Rotation

Configure Docker log rotation in daemon.json:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Database Maintenance

```bash
# Compact DuckDB (run periodically)
docker exec vtc-link python -c "
import duckdb
conn = duckdb.connect('/app/data/telemetry.duckdb')
conn.execute('VACUUM')
conn.close()
"

# Cleanup old logs
docker exec vtc-link python -c "
import duckdb
conn = duckdb.connect('/app/data/telemetry.duckdb')
conn.execute(\"DELETE FROM logs WHERE timestamp < NOW() - INTERVAL '30 days'\")
conn.close()
"
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build

# Rolling restart
docker-compose up -d --no-deps vtc-link
```

---

## See Also

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Logging and Monitoring](logging-monitoring.md) - Production monitoring
- [Testing Guide](testing.md) - Pre-deployment testing
