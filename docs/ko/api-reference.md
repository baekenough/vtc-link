# API 레퍼런스

VTC-Link가 제공하는 모든 API 엔드포인트의 상세 명세입니다. Push 방식 연동, 헬스체크, 관리자 기능을 위한 API를 제공합니다.

---

## API 개요

```mermaid
flowchart TB
    subgraph 외부시스템
        Hospital[병원 시스템]
        Monitor[모니터링 시스템]
    end

    subgraph VTC-Link API
        Push[POST /v1/push]
        Health[GET /health]
        Admin[/admin/*]
    end

    Hospital -->|바이탈 데이터| Push
    Monitor -->|헬스체크| Health
    Admin -->|웹 브라우저| Admin
```

### 기본 정보

| 항목 | 값 |
|------|-----|
| Base URL | `http://localhost:8000` (기본) |
| Content-Type | `application/json` |
| 문자 인코딩 | UTF-8 |

---

## POST /v1/push

병원 시스템에서 바이탈 데이터를 푸시합니다.

### 엔드포인트

```
POST /v1/push
```

### 요청 헤더

| 헤더 | 필수 | 설명 |
|------|------|------|
| Content-Type | O | `application/json` |

### 요청 바디

병원별 원본 페이로드 형식을 사용합니다. 변환 프로파일(`transform_profile`)에서 정의된 `inbound.py`의 `to_canonical()` 함수가 파싱합니다.

#### 요청 스키마 (예시: HOSP_A)

```json
{
  "patient_id": "P001234",
  "patient_name": "홍길동",
  "birthdate": "19800101",
  "age": 45,
  "sex": "M",
  "ward": "51W",
  "department": "IM",
  "sbp": 120,
  "dbp": 80,
  "pulse": 72,
  "respiration": 16,
  "temperature": 36.5,
  "spo2": 98.0,
  "measure_time": "2025-01-26T10:30:00Z"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| patient_id | string | O | 환자 식별자 |
| patient_name | string | X | 환자 이름 |
| birthdate | string | O | 생년월일 (YYYYMMDD) |
| age | integer | X | 나이 |
| sex | string | O | 성별 코드 (M/F) |
| ward | string | X | 병동 코드 |
| department | string | X | 진료과 코드 |
| sbp | integer | O | 수축기 혈압 (mmHg) |
| dbp | integer | O | 이완기 혈압 (mmHg) |
| pulse | integer | O | 맥박수 (bpm) |
| respiration | integer | O | 호흡수 (/min) |
| temperature | float | O | 체온 (°C) |
| spo2 | float | O | 산소포화도 (%) |
| measure_time | string | O | 측정 시각 (ISO 8601) |

### 응답

#### 성공 응답 (200 OK)

```json
{
  "status": "success",
  "message": "Data processed successfully",
  "record_id": "REC-20250126-001234"
}
```

#### 후처리 실패 응답 (200 OK)

```json
{
  "status": "postprocess_failed",
  "error_code": "PP_EXEC_005"
}
```

!!! warning "후처리 실패"
    백엔드 전송은 성공했으나 원본 시스템 플래그 업데이트/로그 삽입이 실패한 경우입니다.
    데이터는 전송되었으므로 원본 시스템에서 수동 처리가 필요할 수 있습니다.

#### 에러 응답

=== "400 Bad Request"
    ```json
    {
      "detail": "Validation error",
      "errors": [
        {
          "field": "sbp",
          "message": "Value must be between 40 and 300"
        }
      ]
    }
    ```

=== "500 Internal Server Error"
    ```json
    {
      "detail": "Pipeline execution failed",
      "error_code": "TX_PARSE_001"
    }
    ```

### curl 예제

```bash
curl -X POST http://localhost:8000/v1/push \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "P001234",
    "patient_name": "홍길동",
    "birthdate": "19800101",
    "sex": "M",
    "ward": "51W",
    "department": "IM",
    "sbp": 120,
    "dbp": 80,
    "pulse": 72,
    "respiration": 16,
    "temperature": 36.5,
    "spo2": 98.0,
    "measure_time": "2025-01-26T10:30:00Z"
  }'
```

### Python 예제

```python
import requests

url = "http://localhost:8000/v1/push"
payload = {
    "patient_id": "P001234",
    "patient_name": "홍길동",
    "birthdate": "19800101",
    "sex": "M",
    "ward": "51W",
    "department": "IM",
    "sbp": 120,
    "dbp": 80,
    "pulse": 72,
    "respiration": 16,
    "temperature": 36.5,
    "spo2": 98.0,
    "measure_time": "2025-01-26T10:30:00Z"
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['status']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

---

## GET /health

서비스 헬스 상태를 확인합니다. 로드 밸런서 및 모니터링 시스템에서 사용합니다.

### 엔드포인트

```
GET /health
```

### 요청 헤더

인증 불필요

### 응답

#### 성공 응답 (200 OK)

```json
{
  "status": "정상"
}
```

### curl 예제

```bash
curl http://localhost:8000/health
```

### 헬스체크 활용

=== "Docker Compose"
    ```yaml
    services:
      vtc-link:
        image: vtc-link:latest
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
          interval: 30s
          timeout: 10s
          retries: 3
    ```

=== "Kubernetes"
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

=== "AWS ALB"
    ```
    Target Group Health Check:
    - Protocol: HTTP
    - Path: /health
    - Healthy threshold: 2
    - Unhealthy threshold: 3
    - Interval: 30 seconds
    - Timeout: 5 seconds
    ```

---

## 관리자 엔드포인트

관리자 UI 기능을 위한 엔드포인트입니다. Basic 인증이 필요합니다.

### 인증 방법

모든 관리자 엔드포인트는 HTTP Basic 인증을 사용합니다.

```
Authorization: Basic {base64(username:password)}
```

#### 인증 헤더 예시

```bash
# username=admin, password=changeme인 경우
# base64("admin:changeme") = "YWRtaW46Y2hhbmdlbWU="
Authorization: Basic YWRtaW46Y2hhbmdlbWU=
```

### curl 인증 예제

```bash
# -u 옵션 사용
curl -u admin:changeme http://localhost:8000/admin/dashboard

# 또는 헤더 직접 지정
curl -H "Authorization: Basic YWRtaW46Y2hhbmdlbWU=" \
  http://localhost:8000/admin/dashboard
```

### Python 인증 예제

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    "http://localhost:8000/admin/dashboard",
    auth=HTTPBasicAuth("admin", "changeme")
)
```

---

### GET /admin/dashboard

대시보드 페이지를 렌더링합니다.

```
GET /admin/dashboard
```

#### 응답

HTML 페이지 (Content-Type: text/html)

#### 대시보드 내용

- 전체 병원 수
- 오늘 처리 레코드 수
- 성공률
- 에러 횟수
- 최근 병원 상태 목록
- 최근 로그 목록

---

### GET /admin/logs

로그 조회 페이지를 렌더링합니다.

```
GET /admin/logs
```

#### 응답

HTML 페이지 (Content-Type: text/html)

#### 로그 테이블 컬럼

| 컬럼 | 설명 |
|------|------|
| timestamp | 발생 시각 |
| level | 로그 레벨 |
| event | 이벤트 타입 |
| hospital_id | 병원 ID |
| stage | 파이프라인 단계 |
| error_code | 에러 코드 |
| message | 메시지 |
| duration_ms | 실행 시간 |
| record_count | 레코드 수 |

---

### GET /admin/status

병원 상태 페이지를 렌더링합니다.

```
GET /admin/status
```

#### 응답

HTML 페이지 (Content-Type: text/html)

#### 상태 테이블 컬럼

| 컬럼 | 설명 |
|------|------|
| hospital_id | 병원 ID |
| last_run_at | 마지막 실행 시각 |
| last_success_at | 마지막 성공 시각 |
| last_status | 현재 상태 |
| last_error_code | 마지막 에러 코드 |
| postprocess_fail_count | 후처리 실패 횟수 |

---

### GET /admin/config

설정 페이지를 렌더링합니다.

```
GET /admin/config
```

#### 응답

HTML 페이지 (Content-Type: text/html)

현재 `hospitals.yaml` 설정을 폼으로 표시합니다.

---

### POST /admin/config

설정을 저장합니다.

```
POST /admin/config
```

#### 요청

Content-Type: `application/x-www-form-urlencoded`

HTML 폼 데이터

#### 응답

HTML 페이지 (Content-Type: text/html)

저장 성공/실패 메시지와 함께 설정 페이지 렌더링

#### 유효성 검사 에러

저장 시 다음 항목을 검증합니다:

| 검증 항목 | 에러 메시지 |
|-----------|-------------|
| hospital_id 누락 | "hospital_id 필요" |
| connector_type 오류 | "connector_type 값 오류" |
| transform_profile 누락 | "transform_profile 필요" |
| schedule_minutes 오류 | "schedule_minutes 양수 필요" |
| db.type 오류 | "db.type 값 오류" |
| db.host 누락 | "db.host 필요" |
| db.service 누락 (Oracle) | "db.service 필요" |
| api.url 누락 | "api.url 필요" |
| postprocess.mode 오류 | "postprocess.mode 값 오류" |
| postprocess.table 누락 | "postprocess.table 필요" |
| postprocess.key_column 누락 | "postprocess.key_column 필요" |
| postprocess.flag_column 누락 | "postprocess.flag_column 필요" |
| key_value 누락 | "postprocess.key_value 또는 key_value_source 필요" |
| postprocess.columns 누락 | "postprocess.columns 필요" |
| 컬럼 값 누락 | "postprocess 컬럼 누락: {col}" |

---

## 요청/응답 스키마

### Canonical Payload (내부 형식)

VTC-Link 내부에서 사용하는 정규화된 데이터 형식입니다.

```json
{
  "patient": {
    "patient_id": "P001234",
    "patient_name": "홍길동",
    "birthdate": "19800101",
    "age": 45,
    "sex": "M",
    "ward": "51W",
    "department": "IM"
  },
  "vitals": {
    "SBP": 120,
    "DBP": 80,
    "PR": 72,
    "RR": 16,
    "BT": 36.5,
    "SpO2": 98.0
  },
  "timestamps": {
    "created_at": "2025-01-26T10:30:00Z",
    "updated_at": "2025-01-26T10:30:00Z"
  }
}
```

#### Patient 스키마

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| patient_id | string | O | 환자 식별자 |
| patient_name | string | X | 환자 이름 |
| birthdate | string | O | 생년월일 (YYYYMMDD) |
| age | integer | X | 나이 |
| sex | string | O | 성별 (M/F) |
| ward | string | X | 병동 (최대 30자) |
| department | string | X | 진료과 (최대 30자) |

#### Vitals 스키마

| 필드 | 타입 | 필수 | 범위 | 설명 |
|------|------|------|------|------|
| SBP | integer | O | 40-300 | 수축기 혈압 (mmHg) |
| DBP | integer | O | 20-200 | 이완기 혈압 (mmHg) |
| PR | integer | O | 20-300 | 맥박수 (bpm) |
| RR | integer | O | 4-60 | 호흡수 (/min) |
| BT | float | O | 30.0-45.0 | 체온 (°C) |
| SpO2 | float | O | 50.0-100.0 | 산소포화도 (%) |

#### Timestamps 스키마

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| created_at | string | O | 생성 시각 (ISO 8601 UTC) |
| updated_at | string | O | 수정 시각 (ISO 8601 UTC) |

---

## 인증 상세

### Basic 인증 흐름

```mermaid
sequenceDiagram
    participant C as Client
    participant V as VTC-Link

    C->>V: GET /admin/dashboard (인증 없음)
    V->>C: 401 Unauthorized<br/>WWW-Authenticate: Basic

    C->>C: Base64 인코딩 (admin:password)
    C->>V: GET /admin/dashboard<br/>Authorization: Basic YWRt...
    V->>V: 인증 검증
    V->>C: 200 OK (HTML)
```

### 인증 실패 응답

```json
{
  "detail": "인증 필요"
}
```

또는

```json
{
  "detail": "인증 정보 오류"
}
```

또는

```json
{
  "detail": "인증 실패"
}
```

---

## 에러 응답 형식

### 일반 에러

```json
{
  "detail": "에러 메시지"
}
```

### 유효성 검사 에러

```json
{
  "detail": [
    {
      "loc": ["body", "sbp"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

### 파이프라인 에러

```json
{
  "detail": "Pipeline execution failed",
  "error_code": "TX_PARSE_001",
  "message": "birthdate: Invalid date format"
}
```

---

## 통합 예제

### 병원 시스템 연동 (Python)

```python
"""
병원 시스템에서 VTC-Link로 바이탈 데이터를 전송하는 예제
"""
import requests
from datetime import datetime
from typing import Optional


class VTCLinkClient:
    """VTC-Link API 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def push_vital(
        self,
        patient_id: str,
        birthdate: str,
        sex: str,
        sbp: int,
        dbp: int,
        pulse: int,
        respiration: int,
        temperature: float,
        spo2: float,
        patient_name: Optional[str] = None,
        age: Optional[int] = None,
        ward: Optional[str] = None,
        department: Optional[str] = None,
        measure_time: Optional[str] = None,
    ) -> dict:
        """바이탈 데이터를 VTC-Link로 전송

        Args:
            patient_id: 환자 식별자
            birthdate: 생년월일 (YYYYMMDD)
            sex: 성별 (M/F)
            sbp: 수축기 혈압
            dbp: 이완기 혈압
            pulse: 맥박수
            respiration: 호흡수
            temperature: 체온
            spo2: 산소포화도
            patient_name: 환자 이름 (선택)
            age: 나이 (선택)
            ward: 병동 (선택)
            department: 진료과 (선택)
            measure_time: 측정 시각 (선택, 기본: 현재 시각)

        Returns:
            API 응답 딕셔너리

        Raises:
            requests.HTTPError: API 에러 시
        """
        payload = {
            "patient_id": patient_id,
            "birthdate": birthdate,
            "sex": sex,
            "sbp": sbp,
            "dbp": dbp,
            "pulse": pulse,
            "respiration": respiration,
            "temperature": temperature,
            "spo2": spo2,
            "measure_time": measure_time or datetime.utcnow().isoformat() + "Z",
        }

        if patient_name:
            payload["patient_name"] = patient_name
        if age is not None:
            payload["age"] = age
        if ward:
            payload["ward"] = ward
        if department:
            payload["department"] = department

        response = self.session.post(
            f"{self.base_url}/v1/push",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """서비스 헬스 확인

        Returns:
            정상이면 True
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.RequestException:
            return False


# 사용 예제
if __name__ == "__main__":
    client = VTCLinkClient("http://localhost:8000")

    # 헬스 체크
    if not client.health_check():
        print("VTC-Link 서비스가 응답하지 않습니다")
        exit(1)

    # 바이탈 데이터 전송
    result = client.push_vital(
        patient_id="P001234",
        patient_name="홍길동",
        birthdate="19800101",
        age=45,
        sex="M",
        ward="51W",
        department="IM",
        sbp=120,
        dbp=80,
        pulse=72,
        respiration=16,
        temperature=36.5,
        spo2=98.0,
    )

    print(f"전송 결과: {result}")
```

### 배치 전송 예제

```python
"""
여러 건의 바이탈 데이터를 배치로 전송하는 예제
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def batch_push_vitals(client: VTCLinkClient, records: list[dict]) -> dict:
    """여러 레코드를 병렬로 전송

    Args:
        client: VTC-Link 클라이언트
        records: 전송할 레코드 목록

    Returns:
        성공/실패 통계
    """
    results = {"success": 0, "failed": 0, "errors": []}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(client.push_vital, **record): record
            for record in records
        }

        for future in as_completed(futures):
            record = futures[future]
            try:
                result = future.result()
                if result.get("status") == "success":
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "patient_id": record["patient_id"],
                        "error": result.get("error_code"),
                    })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "patient_id": record["patient_id"],
                    "error": str(e),
                })

    return results


# 사용 예제
if __name__ == "__main__":
    client = VTCLinkClient("http://localhost:8000")

    records = [
        {
            "patient_id": f"P{i:06d}",
            "birthdate": "19800101",
            "sex": "M",
            "sbp": 120 + i % 20,
            "dbp": 80 + i % 10,
            "pulse": 72,
            "respiration": 16,
            "temperature": 36.5,
            "spo2": 98.0,
        }
        for i in range(100)
    ]

    results = batch_push_vitals(client, records)
    print(f"성공: {results['success']}, 실패: {results['failed']}")
```

---

## Rate Limiting

현재 버전에서는 Rate Limiting이 구현되어 있지 않습니다.

!!! note "향후 계획"
    운영 환경에서는 다음 설정을 권장합니다:

    - Nginx/Kong 등 API Gateway에서 Rate Limit 설정
    - `/v1/push`: 1000 req/min per IP
    - `/admin/*`: 100 req/min per IP

---

## OpenAPI 문서

FastAPI가 제공하는 자동 생성 API 문서를 사용할 수 있습니다.

| URL | 설명 |
|-----|------|
| `/docs` | Swagger UI (대화형 API 문서) |
| `/redoc` | ReDoc (읽기 전용 API 문서) |
| `/openapi.json` | OpenAPI 3.0 스키마 (JSON) |
