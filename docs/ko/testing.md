# 테스트 가이드

VTC-Link는 **pytest** 기반의 테스트 프레임워크를 사용하여 코드 품질과 안정성을 보장합니다.

---

## 테스트 구조

```
vtc-link/
└── tests/
    ├── test_parsing.py           # 파싱 유틸리티 테스트
    ├── test_postprocess.py       # 후처리 로직 테스트
    ├── test_pipeline_logging.py  # 파이프라인 로깅 테스트
    ├── test_scheduler.py         # 스케줄러 테스트
    └── test_admin_config.py      # Admin UI 설정 테스트
```

### 테스트 분류

| 분류 | 설명 | 예시 |
|------|------|------|
| **단위 테스트** | 개별 함수/클래스 검증 | `test_parsing.py` |
| **통합 테스트** | 컴포넌트 간 상호작용 검증 | `test_pipeline_logging.py` |
| **API 테스트** | FastAPI 엔드포인트 검증 | `test_admin_config.py` |

---

## pytest 실행 방법

### 기본 실행

```bash
# 전체 테스트 실행
uv run pytest

# 상세 출력과 함께 실행
uv run pytest -v

# 더 상세한 출력 (각 테스트 이름 표시)
uv run pytest -vv
```

### 특정 테스트 실행

=== "파일 단위"

    ```bash
    # 특정 테스트 파일 실행
    uv run pytest tests/test_parsing.py
    ```

=== "함수 단위"

    ```bash
    # 특정 테스트 함수 실행
    uv run pytest tests/test_parsing.py::test_parse_int_valid
    ```

=== "키워드 필터"

    ```bash
    # 'postprocess' 키워드가 포함된 테스트만 실행
    uv run pytest -k "postprocess"
    ```

### 유용한 옵션

```bash
# 첫 번째 실패에서 중단
uv run pytest -x

# 마지막 실패한 테스트만 재실행
uv run pytest --lf

# 실패한 테스트 먼저 실행
uv run pytest --ff

# 출력 캡처 비활성화 (print 확인)
uv run pytest -s

# 병렬 실행 (pytest-xdist 필요)
uv run pytest -n auto
```

---

## 단위 테스트 작성법

### 기본 구조

```python
import pytest
from app.utils.parsing import parse_int
from app.core.errors import ParseError


def test_parse_int_valid():
    """정상 정수 문자열 파싱 테스트"""
    result = parse_int("123", "SBP")
    assert result == 123


def test_parse_int_invalid():
    """잘못된 입력에 대한 예외 발생 테스트"""
    with pytest.raises(ParseError):
        parse_int("abc", "SBP")
```

### 파라미터화 테스트

```python
import pytest


@pytest.mark.parametrize("input_value,expected", [
    ("10", 10),
    ("10.2", 10),
    ("invalid", 0),
    ("", 0),
])
def test_coerce_int(input_value, expected):
    """다양한 입력값에 대한 coerce_int 테스트"""
    from app.utils.parsing import coerce_int
    assert coerce_int(input_value) == expected
```

### Fixture 사용

```python
import pytest
from app.core.config import HospitalConfig


@pytest.fixture
def sample_hospital_config():
    """테스트용 병원 설정 fixture"""
    return HospitalConfig(
        hospital_id="TEST_HOSP",
        connector_type="pull_db_view",
        transform_profile="TEST_HOSP",
        enabled=True,
        schedule_minutes=5,
    )


def test_hospital_config_defaults(sample_hospital_config):
    """병원 설정 기본값 검증"""
    assert sample_hospital_config.enabled is True
    assert sample_hospital_config.schedule_minutes == 5
```

---

## 통합 테스트 작성법

### 파이프라인 테스트 예시

```python
from app.core.config import HospitalConfig
from app.core.pipeline import run_pull_pipeline
from app.core.telemetry import TelemetryStore


def test_postprocess_failure_logs(tmp_path, monkeypatch):
    """후처리 실패 시 로그 기록 테스트"""
    # 1. 환경 설정
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "telemetry.duckdb"))
    from app.core.config import get_settings
    get_settings.cache_clear()

    # 2. 테스트 대상 초기화
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

    # 3. 실행
    run_pull_pipeline(hospital)

    # 4. 검증
    rows = store.query_logs("event = ?", ["postprocess_failed"])
    assert rows is not None
```

### API 통합 테스트

```python
import base64
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


def _basic_auth_header(username: str, password: str) -> dict:
    """Basic 인증 헤더 생성"""
    token = base64.b64encode(
        f"{username}:{password}".encode("utf-8")
    ).decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def _make_client(tmp_path, monkeypatch) -> TestClient:
    """테스트용 FastAPI 클라이언트 생성"""
    config_path = tmp_path / "hospitals.yaml"
    config_path.write_text(
        """hospital:
  hospital_id: HOSP_A
  connector_type: pull_db_view
  enabled: true
  schedule_minutes: 5
  transform_profile: HOSP_A
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "telemetry.duckdb"))
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    from app.core.config import get_settings, load_app_config
    get_settings.cache_clear()
    load_app_config.cache_clear()

    app = create_app()
    return TestClient(app)


def test_admin_config_page_returns_401_without_auth(tmp_path, monkeypatch):
    """인증 없이 Admin 설정 페이지 접근 시 401 반환"""
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/admin/config")
    assert response.status_code == 401
```

---

## 테스트 커버리지

### 커버리지 측정

```bash
# 커버리지 리포트 생성
uv run pytest --cov=app

# HTML 리포트 생성
uv run pytest --cov=app --cov-report=html

# 특정 커버리지 이상 강제
uv run pytest --cov=app --cov-fail-under=80
```

### 커버리지 리포트 예시

```
---------- coverage: platform darwin, python 3.12.0 -----------
Name                           Stmts   Miss  Cover
--------------------------------------------------
app/__init__.py                    0      0   100%
app/api/admin.py                  89     12    87%
app/api/health.py                  5      0   100%
app/api/push.py                   23      4    83%
app/core/config.py                42      2    95%
app/core/pipeline.py              78     15    81%
app/utils/parsing.py              45      3    93%
--------------------------------------------------
TOTAL                            382     36    91%
```

!!! tip "커버리지 목표"
    - **최소 목표**: 80% 이상
    - **권장 목표**: 90% 이상
    - **핵심 모듈**: `core/`, `utils/`는 95% 이상 권장

---

## 모킹 전략

### monkeypatch 사용

```python
def test_with_env_override(monkeypatch):
    """환경 변수 오버라이드 테스트"""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    from app.core.config import get_settings
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.log_level == "DEBUG"
    assert settings.scheduler_enabled is False
```

### pytest-mock 사용

```python
def test_backend_api_call(mocker):
    """백엔드 API 호출 모킹"""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"vital_id": "V123"}

    mocker.patch(
        "app.clients.backend_api.httpx.post",
        return_value=mock_response
    )

    from app.clients.backend_api import send_payload
    result = send_payload({"patient": {}, "vitals": {}})
    assert result["vital_id"] == "V123"
```

### 데이터베이스 모킹

```python
def test_oracle_fetch_with_mock(mocker):
    """Oracle DB 조회 모킹"""
    mock_cursor = mocker.Mock()
    mock_cursor.fetchall.return_value = [
        ("P001", "홍길동", "19900101", 120, 80)
    ]
    mock_cursor.description = [
        ("PATIENT_ID",), ("NAME",), ("BIRTH",), ("SBP",), ("DBP",)
    ]

    mock_connection = mocker.Mock()
    mock_connection.cursor.return_value.__enter__ = mocker.Mock(
        return_value=mock_cursor
    )
    mock_connection.cursor.return_value.__exit__ = mocker.Mock(
        return_value=False
    )

    mocker.patch(
        "app.connectors.oracle_view_fetch.get_oracle_connection",
        return_value=mock_connection
    )
```

### 임시 파일/디렉토리

```python
def test_with_temp_config(tmp_path):
    """임시 설정 파일 사용 테스트"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text("""
hospital:
  hospital_id: TEST
  connector_type: push_rest_api
  transform_profile: TEST
  enabled: true
""")

    # config_file.as_posix() 또는 str(config_file) 사용
    assert config_file.exists()
```

---

## CI/CD 테스트 통합

### GitHub Actions 예시

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --dev

      - name: Run tests
        run: uv run pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

### 테스트 매트릭스

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.12"]
        os: [ubuntu-latest, macos-latest]

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      # ...
```

---

## 테스트 모범 사례

!!! success "권장 사항"
    - **명확한 테스트 이름**: `test_<기능>_<시나리오>_<예상결과>` 패턴 사용
    - **하나의 테스트, 하나의 검증**: 각 테스트는 단일 동작만 검증
    - **독립적인 테스트**: 테스트 간 의존성 제거
    - **Fixture 활용**: 중복 설정 코드 최소화
    - **캐시 정리**: `cache_clear()` 호출로 상태 초기화

!!! warning "주의 사항"
    - 테스트에서 실제 외부 서비스 호출 금지
    - `sleep()` 사용 자제 (비동기 테스트는 `pytest-asyncio` 활용)
    - 하드코딩된 경로 대신 `tmp_path` fixture 사용
    - 테스트 후 리소스 정리 (파일, DB 연결 등)

---

## 비동기 테스트

VTC-Link는 `pytest-asyncio`를 사용하여 비동기 코드를 테스트합니다.

```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """비동기 함수 테스트"""
    from app.clients.backend_api import send_payload_async

    result = await send_payload_async({"test": "data"})
    assert result is not None
```

### pyproject.toml 설정

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
```

---

## 문제 해결

### 자주 발생하는 오류

=== "ImportError"

    ```
    ImportError: cannot import name 'X' from 'app.module'
    ```

    **해결**: `pythonpath` 설정 확인
    ```bash
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    ```

=== "캐시 문제"

    ```
    테스트 결과가 예상과 다름
    ```

    **해결**: 설정 캐시 초기화
    ```python
    from app.core.config import get_settings, load_app_config
    get_settings.cache_clear()
    load_app_config.cache_clear()
    ```

=== "DB 연결 오류"

    ```
    Could not connect to database
    ```

    **해결**: 환경 변수 모킹 확인
    ```python
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "test.duckdb"))
    ```

---

## 다음 단계

- [파이프라인 가이드](pipeline.md) - 데이터 처리 파이프라인 이해
- [배포 가이드](deployment.md) - 프로덕션 배포 방법
- [기여하기](contributing.md) - 프로젝트 기여 방법
