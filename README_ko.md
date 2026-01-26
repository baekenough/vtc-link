# VTC-Link

**Vital Data Interface Server** - 다양한 병원 시스템에서 환자의 생체신호 데이터를 수집하여 정규화한 후 백엔드 분석 서버로 전달하는 인터페이스 프록시

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

## 개요

VTC-Link는 병원 정보 시스템(HIS)과 생체신호 분석 백엔드 사이의 미들웨어입니다. 병원마다 다른 데이터 소스와 포맷을 통합하면서 다운스트림 처리를 위한 통일된 인터페이스를 제공합니다.

### 주요 기능

- **다중 커넥터 지원**: Oracle/MSSQL 데이터베이스, REST API (pull/push) 연동
- **데이터 정규화**: 병원별 포맷을 캐노니컬 스키마로 변환
- **스케줄 처리**: APScheduler 기반 백그라운드 작업 (pull 커넥터용)
- **관리자 대시보드**: 설정, 모니터링, 로그 조회를 위한 웹 UI
- **후처리 작업**: 처리 완료 후 플래그 업데이트 또는 로그 삽입
- **텔레메트리**: DuckDB 기반 이벤트 로깅 및 상태 추적

## 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   병원 HIS      │───▶│    VTC-Link     │───▶│   백엔드 API    │
│  (DB / REST)    │    │   (이 서버)      │    │    (분석)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │    관리자 UI     │
                       │   (모니터링)     │
                       └─────────────────┘
```

### 데이터 흐름

```
┌──────────────────────────────────────────────────────────────────┐
│                     PULL 기반 파이프라인                          │
├──────────────────────────────────────────────────────────────────┤
│  스케줄러 (interval)                                              │
│      ↓                                                           │
│  수집 (Oracle/MSSQL/REST) → 원본 레코드                           │
│      ↓                                                           │
│  변환: to_canonical() → CanonicalPayload                         │
│      ↓                                                           │
│  백엔드: send_payload() → 분석 결과                               │
│      ↓                                                           │
│  후처리: update_flag / insert_log                                │
│      ↓                                                           │
│  텔레메트리: log_event() → DuckDB                                │
└──────────────────────────────────────────────────────────────────┘
```

## 기술 스택

| 분류 | 기술 |
|------|------|
| 프레임워크 | FastAPI 0.115+ |
| 런타임 | Python 3.12, Uvicorn |
| 데이터베이스 | Oracle (oracledb), MSSQL (pyodbc), DuckDB |
| 스케줄링 | APScheduler |
| HTTP 클라이언트 | httpx |
| 검증 | Pydantic v2 |
| 관리자 UI | Jinja2, HTML/CSS |

## 프로젝트 구조

```
vtc-link/
├── app/
│   ├── main.py                 # FastAPI 애플리케이션 팩토리
│   ├── api/                    # API 엔드포인트
│   │   ├── routes.py           # 라우트 집계
│   │   ├── push.py             # Push vitals 엔드포인트
│   │   ├── admin.py            # 관리자 UI 및 설정 관리
│   │   └── health.py           # 헬스체크
│   ├── core/                   # 비즈니스 로직
│   │   ├── config.py           # 설정 관리
│   │   ├── pipeline.py         # 파이프라인 오케스트레이션
│   │   ├── scheduler.py        # APScheduler 래퍼
│   │   ├── postprocess.py      # 후처리 DB 작업
│   │   ├── db.py               # 데이터베이스 연결
│   │   └── telemetry.py        # DuckDB 텔레메트리
│   ├── connectors/             # 데이터 소스 커넥터
│   │   ├── oracle_view_fetch.py
│   │   ├── mssql_view_fetch.py
│   │   ├── rest_pull_fetch.py
│   │   └── rest_push_receive.py
│   ├── transforms/             # 병원별 변환
│   │   └── hospital_profiles/
│   │       └── HOSP_A/
│   ├── models/                 # Pydantic 모델
│   └── clients/                # 백엔드 HTTP 클라이언트
├── templates/                  # 관리자 UI용 Jinja2 템플릿
├── static/                     # 관리자 UI CSS
├── tests/                      # pytest 테스트 스위트
├── docs/                       # 문서 (MkDocs)
└── docker-compose.yml          # Docker 배포
```

## 데이터 모델

### 캐노니컬 페이로드 (정규화 포맷)

```python
{
  "patient": {
    "patient_id": "P12345",
    "patient_name": "홍길동",
    "birthdate": "19900101",
    "age": 34,
    "sex": "M",
    "ward": "ICU",
    "department": "내과"
  },
  "vitals": {
    "SBP": 120,      # 수축기 혈압
    "DBP": 80,       # 이완기 혈압
    "PR": 72,        # 맥박수
    "RR": 18,        # 호흡수
    "BT": 36.5,      # 체온
    "SpO2": 98.0     # 산소포화도
  },
  "timestamps": {
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### 클라이언트 응답 (백엔드 결과)

```python
{
  "vital_id": "V67890",
  "patient_id": "P12345",
  "screened_type": "EMERGENCY",
  "screened_date": "20240115 10:30:00",
  "SEPS": 2,        # 패혈증 점수
  "MAES": 1,        # MAES 점수
  "MORS": 0,        # 사망 위험 점수
  "NEWS": 3,        # 국가 조기경보 점수
  "MEWS": 2         # 수정 조기경보 점수
}
```

## 시작하기

### 요구사항

- Python 3.12
- uv (권장) 또는 pip

### 설치

```bash
# 저장소 클론
git clone https://github.com/baekenough/vtc-link.git
cd vtc-link

# uv로 의존성 설치
uv sync

# 또는 pip으로 설치
pip install -e .
```

### 설정

1. 환경 변수 복사 및 편집:
```bash
cp .env.example .env
```

2. `hospitals.yaml`에서 병원 설정:
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

### 실행

```bash
# 개발 모드
./dev.sh
# 또는
uv run uvicorn app.main:app --reload

# 운영 (Docker)
docker-compose up -d
```

### 접속 URL

- **API**: http://localhost:8000
- **관리자 대시보드**: http://localhost:8000/admin/dashboard
- **헬스체크**: http://localhost:8000/health
- **API 문서**: http://localhost:8000/docs

## 커넥터 타입

| 타입 | 설명 | 사용 사례 |
|------|------|----------|
| `pull_db_view` | 스케줄에 따라 DB 뷰 폴링 | 병원에서 DB 뷰 접근 제공 |
| `pull_rest_api` | 스케줄에 따라 REST API 폴링 | 병원에서 REST 엔드포인트 제공 |
| `push_rest_api` | REST로 푸시된 데이터 수신 | 병원에서 능동적으로 데이터 전송 |
| `push_db_insert` | 결과를 병원 DB에 삽입 | 병원에서 결과를 자체 DB에 저장 원함 |

## 테스트

```bash
# 전체 테스트 실행
uv run pytest

# 커버리지 포함
uv run pytest --cov=app

# 특정 테스트 파일
uv run pytest tests/test_pipeline_logging.py
```

## 문서

전체 문서는 **[baekenough.github.io/vtc-link/ko](https://baekenough.github.io/vtc-link/ko/)** 에서 확인할 수 있습니다.

- [아키텍처](https://baekenough.github.io/vtc-link/ko/architecture/)
- [데이터 모델](https://baekenough.github.io/vtc-link/ko/data-model/)
- [커넥터](https://baekenough.github.io/vtc-link/ko/connectors/)
- [파이프라인](https://baekenough.github.io/vtc-link/ko/pipeline/)
- [관리자 UI](https://baekenough.github.io/vtc-link/ko/admin-ui/)
- [배포](https://baekenough.github.io/vtc-link/ko/deployment/)

**[English Documentation](https://baekenough.github.io/vtc-link/)**
