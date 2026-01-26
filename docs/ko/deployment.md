# 배포 가이드

VTC-Link는 Docker 기반 컨테이너화된 배포를 지원하며, 단일 병원 환경에 최적화되어 있습니다.

---

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Docker Host    │    │         External Systems         │ │
│  │  ┌───────────┐  │    │  ┌───────────┐  ┌───────────┐  │ │
│  │  │ VTC-Link  │──┼────┼─▶│ Hospital  │  │ Backend   │  │ │
│  │  │ Container │  │    │  │ HIS (DB)  │  │ API Server│  │ │
│  │  └─────┬─────┘  │    │  └───────────┘  └───────────┘  │ │
│  │        │        │    └─────────────────────────────────┘ │
│  │  ┌─────▼─────┐  │                                        │
│  │  │  Volume   │  │    ┌─────────────────────────────────┐ │
│  │  │ (data/)   │  │    │         Monitoring               │ │
│  │  └───────────┘  │    │  - /health endpoint              │ │
│  └─────────────────┘    │  - /admin/dashboard              │ │
│                         │  - DuckDB telemetry              │ │
│                         └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Docker 이미지 빌드

### Dockerfile 구조

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 시스템 의존성 설치 (Oracle/MSSQL 드라이버용)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     curl gcc g++ unixodbc unixodbc-dev \
  && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir uv
RUN uv pip install --system -r /app/pyproject.toml

# 애플리케이션 복사
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 빌드 명령어

=== "기본 빌드"

    ```bash
    # 이미지 빌드
    docker build -t vtc-link:latest .

    # 태그 지정 빌드
    docker build -t vtc-link:1.0.0 .
    ```

=== "빌드 스크립트"

    ```bash
    # build.sh 사용
    chmod +x build.sh
    ./build.sh
    ```

=== "멀티 플랫폼"

    ```bash
    # ARM64/AMD64 동시 빌드
    docker buildx build \
      --platform linux/amd64,linux/arm64 \
      -t vtc-link:latest \
      --push .
    ```

### 이미지 최적화

!!! tip "이미지 크기 최소화"
    ```dockerfile
    # 멀티 스테이지 빌드 (선택적)
    FROM python:3.12-slim AS builder
    WORKDIR /build
    COPY pyproject.toml .
    RUN pip install uv && uv pip install --system -r pyproject.toml

    FROM python:3.12-slim
    COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
    COPY . /app
    WORKDIR /app
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    ```

---

## Docker Compose 설정

### 기본 구성

```yaml
# docker-compose.yml
services:
  vtc-link:
    build: .
    container_name: vtc-link
    ports:
      - "8000:8000"
    environment:
      - ADMIN_ID=admin
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-changeme}
      - BACKEND_BASE_URL=${BACKEND_BASE_URL}
      - BACKEND_API_KEY=${BACKEND_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./hospitals.yaml:/app/hospitals.yaml:ro
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### 프로덕션 구성

```yaml
# docker-compose.prod.yml
services:
  vtc-link:
    image: vtc-link:${VERSION:-latest}
    container_name: vtc-link-prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=prod
      - ADMIN_ID=${ADMIN_ID}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - BACKEND_BASE_URL=${BACKEND_BASE_URL}
      - BACKEND_API_KEY=${BACKEND_API_KEY}
      - LOG_LEVEL=WARNING
      - SCHEDULER_ENABLED=true
    volumes:
      - ./hospitals.yaml:/app/hospitals.yaml:ro
      - vtc-data:/app/data
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"

volumes:
  vtc-data:
    driver: local
```

### 실행 명령어

```bash
# 개발 환경
docker-compose up -d

# 프로덕션 환경
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose logs -f vtc-link

# 재시작
docker-compose restart vtc-link

# 중지 및 제거
docker-compose down
```

---

## 환경 설정

### 환경 변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `ENVIRONMENT` | 실행 환경 (local/dev/prod) | `local` | |
| `ADMIN_ID` | Admin UI 사용자 ID | `admin` | |
| `ADMIN_PASSWORD` | Admin UI 비밀번호 | `admin` | **프로덕션 필수** |
| `BACKEND_BASE_URL` | 백엔드 API 서버 URL | `http://localhost:9000` | **필수** |
| `BACKEND_API_KEY` | 백엔드 API 인증 키 | (없음) | |
| `CONFIG_PATH` | 병원 설정 파일 경로 | `hospitals.yaml` | |
| `DUCKDB_PATH` | 텔레메트리 DB 경로 | `data/telemetry.duckdb` | |
| `SCHEDULER_ENABLED` | 스케줄러 활성화 | `true` | |
| `LOG_LEVEL` | 로그 레벨 | `INFO` | |

### .env 파일 예시

```bash
# .env.production
ENVIRONMENT=prod

# Admin UI (반드시 변경!)
ADMIN_ID=vtc_admin
ADMIN_PASSWORD=secure_password_here

# Backend Server
BACKEND_BASE_URL=https://backend.example.com
BACKEND_API_KEY=your_api_key_here

# Application
CONFIG_PATH=hospitals.yaml
DUCKDB_PATH=data/telemetry.duckdb
SCHEDULER_ENABLED=true
LOG_LEVEL=WARNING
```

!!! danger "보안 경고"
    - `.env` 파일은 절대 Git에 커밋하지 마세요
    - 프로덕션 비밀번호는 반드시 변경하세요
    - API 키는 환경 변수나 시크릿 매니저로 관리하세요

### hospitals.yaml 설정

```yaml
hospital:
  hospital_id: "HOSP_A"
  connector_type: "pull_db_view"
  enabled: true
  schedule_minutes: 5
  transform_profile: "HOSP_A"

  db:
    type: "oracle"
    host: "hospital-db.internal"
    port: 1521
    service: "ORCLCDB"
    username: "readonly_user"
    password: "db_password"
    view_name: "V_VITAL_SIGNS"
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

---

## 헬스 체크

### 엔드포인트

```
GET /health
```

**응답 예시:**
```json
{
  "status": "정상"
}
```

### Docker 헬스체크 설정

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s      # 체크 간격
  timeout: 10s       # 타임아웃
  retries: 3         # 재시도 횟수
  start_period: 10s  # 시작 대기 시간
```

### Kubernetes Probe 예시

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

### 상태 모니터링

```bash
# 헬스 체크 수동 실행
curl -s http://localhost:8000/health | jq

# Docker 헬스 상태 확인
docker inspect --format='{{.State.Health.Status}}' vtc-link

# 연속 모니터링
watch -n 5 'curl -s http://localhost:8000/health'
```

---

## 스케일링 고려사항

### 단일 인스턴스 아키텍처

!!! info "설계 원칙"
    VTC-Link는 **단일 병원 = 단일 인스턴스** 원칙으로 설계되었습니다.
    병원마다 별도의 인스턴스를 배포하여 설정과 데이터를 격리합니다.

```
┌──────────────────────────────────────────────────────────┐
│                   Multi-Hospital Setup                    │
├──────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  VTC-Link   │  │  VTC-Link   │  │  VTC-Link   │      │
│  │  (HOSP_A)   │  │  (HOSP_B)   │  │  (HOSP_C)   │      │
│  │  :8001      │  │  :8002      │  │  :8003      │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │              │
│         └────────────────┼────────────────┘              │
│                          ▼                               │
│               ┌──────────────────┐                       │
│               │   Load Balancer  │                       │
│               │   (Optional)     │                       │
│               └──────────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

### 멀티 인스턴스 배포

```yaml
# docker-compose.multi.yml
services:
  vtc-link-hosp-a:
    image: vtc-link:latest
    container_name: vtc-link-hosp-a
    ports:
      - "8001:8000"
    volumes:
      - ./configs/hosp_a.yaml:/app/hospitals.yaml:ro
      - ./data/hosp_a:/app/data
    environment:
      - ADMIN_PASSWORD=${HOSP_A_ADMIN_PASSWORD}

  vtc-link-hosp-b:
    image: vtc-link:latest
    container_name: vtc-link-hosp-b
    ports:
      - "8002:8000"
    volumes:
      - ./configs/hosp_b.yaml:/app/hospitals.yaml:ro
      - ./data/hosp_b:/app/data
    environment:
      - ADMIN_PASSWORD=${HOSP_B_ADMIN_PASSWORD}
```

### 리소스 요구사항

| 환경 | CPU | 메모리 | 디스크 |
|------|-----|--------|--------|
| 최소 | 0.5 코어 | 256MB | 1GB |
| 권장 | 1 코어 | 512MB | 5GB |
| 대용량 | 2 코어 | 1GB | 10GB |

---

## 프로덕션 체크리스트

### 배포 전 필수 확인

=== "보안"

    - [ ] `ADMIN_PASSWORD` 변경 완료
    - [ ] `.env` 파일 Git 제외 확인
    - [ ] HTTPS 설정 (리버스 프록시)
    - [ ] 네트워크 방화벽 설정
    - [ ] DB 접속 계정 최소 권한 확인

=== "설정"

    - [ ] `hospitals.yaml` 설정 검증
    - [ ] 백엔드 서버 연결 테스트
    - [ ] 병원 DB 연결 테스트
    - [ ] 스케줄러 간격 확인

=== "모니터링"

    - [ ] 헬스체크 설정 확인
    - [ ] 로그 레벨 설정 (`WARNING` 권장)
    - [ ] 로그 로테이션 설정
    - [ ] 알림 설정 (선택)

=== "백업"

    - [ ] `data/` 볼륨 백업 계획
    - [ ] `hospitals.yaml` 백업
    - [ ] 롤백 절차 문서화

### 배포 스크립트

```bash
#!/bin/bash
# deploy.sh

set -e

echo "=== VTC-Link 배포 시작 ==="

# 1. 환경 변수 로드
if [ -f .env.production ]; then
    export $(cat .env.production | xargs)
fi

# 2. 설정 검증
echo "[1/5] 설정 검증 중..."
if [ -z "$ADMIN_PASSWORD" ] || [ "$ADMIN_PASSWORD" = "admin" ]; then
    echo "ERROR: ADMIN_PASSWORD를 변경해주세요"
    exit 1
fi

# 3. 이미지 풀
echo "[2/5] 이미지 다운로드 중..."
docker-compose -f docker-compose.prod.yml pull

# 4. 컨테이너 시작
echo "[3/5] 컨테이너 시작 중..."
docker-compose -f docker-compose.prod.yml up -d

# 5. 헬스 체크 대기
echo "[4/5] 헬스 체크 대기 중..."
sleep 10
for i in {1..10}; do
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "헬스 체크 성공!"
        break
    fi
    echo "대기 중... ($i/10)"
    sleep 3
done

# 6. 상태 확인
echo "[5/5] 배포 상태 확인..."
docker-compose -f docker-compose.prod.yml ps

echo "=== 배포 완료 ==="
```

---

## 로그 관리

### 로그 포맷

```
2024-01-15 10:30:00 INFO vtc-link event=pipeline_start hospital_id=HOSP_A stage=fetch Starting data fetch
2024-01-15 10:30:05 INFO vtc-link event=transform_complete hospital_id=HOSP_A stage=transform Processed 10 records
2024-01-15 10:30:06 INFO vtc-link event=backend_send hospital_id=HOSP_A stage=send Sent to backend
```

### Docker 로그 관리

```yaml
# docker-compose.yml
services:
  vtc-link:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"   # 파일당 최대 크기
        max-file: "5"     # 보관 파일 수
```

### 로그 조회

```bash
# 실시간 로그
docker-compose logs -f vtc-link

# 최근 100줄
docker-compose logs --tail=100 vtc-link

# 특정 시간 이후
docker-compose logs --since="2024-01-15T10:00:00" vtc-link

# 에러만 필터링
docker-compose logs vtc-link 2>&1 | grep -E "(ERROR|CRITICAL)"
```

### 외부 로그 시스템 연동

```yaml
# Fluentd/Fluent Bit 연동
services:
  vtc-link:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "localhost:24224"
        tag: "vtc-link.{{.Name}}"

# Loki 연동
services:
  vtc-link:
    logging:
      driver: "loki"
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        loki-batch-size: "400"
```

### DuckDB 텔레메트리

```sql
-- 최근 로그 조회
SELECT timestamp, level, event, hospital_id, message
FROM pipeline_logs
ORDER BY timestamp DESC
LIMIT 100;

-- 에러 통계
SELECT event, error_code, COUNT(*) as count
FROM pipeline_logs
WHERE level = 'ERROR'
GROUP BY event, error_code
ORDER BY count DESC;
```

---

## 운영 스크립트

### run.sh

```bash
#!/bin/bash
docker-compose up -d
echo "VTC-Link 시작됨: http://localhost:8000"
```

### stop.sh

```bash
#!/bin/bash
docker-compose down
echo "VTC-Link 중지됨"
```

### dev.sh

```bash
#!/bin/bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 문제 해결

### 자주 발생하는 문제

=== "컨테이너 시작 실패"

    ```bash
    # 로그 확인
    docker-compose logs vtc-link

    # 일반적인 원인
    # - hospitals.yaml 문법 오류
    # - 환경 변수 누락
    # - 포트 충돌
    ```

=== "DB 연결 실패"

    ```bash
    # 네트워크 확인
    docker exec vtc-link ping hospital-db.internal

    # 연결 테스트
    docker exec -it vtc-link python -c "
    from app.core.db import get_oracle_connection
    conn = get_oracle_connection()
    print('연결 성공')
    "
    ```

=== "메모리 부족"

    ```bash
    # 메모리 사용량 확인
    docker stats vtc-link

    # 리소스 제한 조정
    # docker-compose.yml에서 memory 설정 변경
    ```

---

## 다음 단계

- [테스트 가이드](testing.md) - 테스트 작성 및 실행
- [기여하기](contributing.md) - 프로젝트 기여 방법
- [파이프라인 가이드](pipeline.md) - 데이터 처리 파이프라인
