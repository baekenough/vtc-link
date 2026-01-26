# 기여하기

VTC-Link 프로젝트에 기여해 주셔서 감사합니다! 이 문서는 프로젝트에 효과적으로 기여하는 방법을 안내합니다.

---

## 개발 환경 설정

### 필수 요구사항

| 요구사항 | 버전 | 비고 |
|----------|------|------|
| Python | 3.12.x | 3.12 이상 필수 |
| uv | 최신 | 권장 패키지 매니저 |
| Git | 2.x+ | 버전 관리 |
| Docker | 20.x+ | 선택 (통합 테스트용) |

### 환경 설정 단계

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/vtc-link.git
cd vtc-link

# 2. uv 설치 (없는 경우)
pip install uv

# 3. 의존성 설치
uv sync --dev

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 값 설정

# 5. 개발 서버 실행
./dev.sh
# 또는
uv run uvicorn app.main:app --reload
```

### IDE 설정

=== "VS Code"

    ```json
    // .vscode/settings.json
    {
      "python.defaultInterpreterPath": ".venv/bin/python",
      "python.analysis.typeCheckingMode": "basic",
      "editor.formatOnSave": true,
      "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
      }
    }
    ```

=== "PyCharm"

    1. **File > Settings > Project > Python Interpreter**
    2. `.venv/bin/python` 선택
    3. **Tools > Python Integrated Tools**
        - Docstring format: Google
        - Default test runner: pytest

### 가상 환경 구조

```
vtc-link/
├── .venv/                 # 가상 환경 (uv가 자동 생성)
├── pyproject.toml         # 프로젝트 설정 및 의존성
├── uv.lock                # 의존성 잠금 파일
└── ...
```

---

## 코드 스타일

### PEP 8 준수

VTC-Link는 [PEP 8](https://peps.python.org/pep-0008/) 스타일 가이드를 따릅니다.

**주요 규칙:**

- 들여쓰기: 4칸 스페이스
- 최대 줄 길이: 88자 (Black/Ruff 기본값)
- 함수/변수명: `snake_case`
- 클래스명: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`

### Ruff 설정

프로젝트는 [Ruff](https://docs.astral.sh/ruff/)를 린터 및 포매터로 사용합니다.

```toml
# pyproject.toml (예시)
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
]
ignore = ["E501"]  # 줄 길이는 포매터가 처리
```

### 린팅 및 포매팅 실행

```bash
# 코드 검사
uv run ruff check .

# 자동 수정
uv run ruff check --fix .

# 코드 포매팅
uv run ruff format .

# 포매팅 검사만
uv run ruff format --check .
```

### 타입 힌팅

모든 함수에 타입 힌트를 사용합니다.

```python
# 좋은 예
def parse_int(value: str, field_name: str) -> int:
    """문자열을 정수로 파싱합니다."""
    try:
        return int(value)
    except ValueError:
        raise ParseError(f"{field_name}: 정수 변환 실패 - {value}")


# 복잡한 타입
from typing import TypedDict

class VitalRecord(TypedDict):
    patient_id: str
    SBP: int
    DBP: int
    BT: float
```

### Docstring 스타일

Google 스타일 docstring을 사용합니다.

```python
def send_payload(payload: dict, hospital_id: str) -> dict:
    """백엔드 서버로 정규화된 데이터를 전송합니다.

    Args:
        payload: 정규화된 환자 데이터
        hospital_id: 병원 식별자

    Returns:
        백엔드 서버 응답 (분석 결과)

    Raises:
        BackendError: 서버 응답 오류 시
        ConnectionError: 연결 실패 시

    Example:
        >>> result = send_payload({"patient": {...}}, "HOSP_A")
        >>> print(result["vital_id"])
        V12345
    """
    ...
```

---

## 브랜치 전략

### Git Flow 기반

```
main (또는 master)
  │
  ├── develop
  │     │
  │     ├── feature/add-mssql-connector
  │     ├── feature/admin-ui-improvement
  │     └── feature/scheduler-retry
  │
  ├── hotfix/fix-critical-bug
  │
  └── release/1.0.0
```

### 브랜치 명명 규칙

| 접두어 | 용도 | 예시 |
|--------|------|------|
| `feature/` | 새 기능 개발 | `feature/add-push-connector` |
| `bugfix/` | 버그 수정 | `bugfix/fix-parsing-error` |
| `hotfix/` | 긴급 수정 | `hotfix/fix-security-issue` |
| `refactor/` | 리팩토링 | `refactor/clean-pipeline-code` |
| `docs/` | 문서 작업 | `docs/update-api-guide` |
| `test/` | 테스트 추가 | `test/add-connector-tests` |

### 작업 흐름

```bash
# 1. develop 브랜치에서 기능 브랜치 생성
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature

# 2. 작업 수행 및 커밋
git add .
git commit -m "feat: add new feature description"

# 3. 원격 저장소에 푸시
git push origin feature/my-new-feature

# 4. Pull Request 생성 (GitHub/GitLab UI에서)
```

---

## 커밋 메시지 규칙

### Conventional Commits

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### 타입 종류

| 타입 | 설명 | 예시 |
|------|------|------|
| `feat` | 새로운 기능 | `feat(connector): add MSSQL view fetch` |
| `fix` | 버그 수정 | `fix(parser): handle null values` |
| `docs` | 문서 변경 | `docs: update deployment guide` |
| `style` | 코드 스타일 | `style: format with ruff` |
| `refactor` | 리팩토링 | `refactor(pipeline): simplify flow` |
| `test` | 테스트 추가 | `test: add postprocess tests` |
| `chore` | 기타 작업 | `chore: update dependencies` |

### 커밋 메시지 예시

```bash
# 좋은 예
feat(connector): add Oracle view polling support

- Implement oracle_view_fetch connector
- Add connection pooling
- Handle Oracle-specific date formats

Closes #123

# 나쁜 예
update code
fix bug
WIP
```

---

## Pull Request 프로세스

### PR 생성 전 체크리스트

- [ ] 테스트 통과 (`uv run pytest`)
- [ ] 린팅 통과 (`uv run ruff check .`)
- [ ] 포매팅 적용 (`uv run ruff format .`)
- [ ] 타입 체크 통과 (선택)
- [ ] 문서 업데이트 (필요시)

### PR 템플릿

```markdown
## 개요
<!-- 변경 사항을 간단히 설명해주세요 -->

## 변경 유형
- [ ] 새 기능 (feat)
- [ ] 버그 수정 (fix)
- [ ] 문서 (docs)
- [ ] 리팩토링 (refactor)
- [ ] 테스트 (test)

## 변경 내용
<!-- 상세한 변경 내용을 작성해주세요 -->
-
-

## 테스트 방법
<!-- 테스트 방법을 설명해주세요 -->
```bash
uv run pytest tests/test_xxx.py
```

## 체크리스트
- [ ] 테스트 추가/수정
- [ ] 문서 업데이트
- [ ] CHANGELOG 업데이트 (해당 시)

## 관련 이슈
Closes #
```

### 리뷰 프로세스

```
PR 생성
    │
    ▼
자동 CI 검사 (테스트, 린팅)
    │
    ▼
코드 리뷰 요청
    │
    ▼
리뷰어 피드백
    │
    ▼
수정 및 재리뷰
    │
    ▼
승인 (Approve)
    │
    ▼
Squash & Merge
```

!!! tip "좋은 PR을 위한 팁"
    - **작은 단위**: 하나의 PR은 하나의 기능/수정
    - **명확한 설명**: 왜 이 변경이 필요한지 설명
    - **테스트 포함**: 새 기능은 테스트와 함께
    - **스크린샷**: UI 변경 시 전후 스크린샷 첨부

---

## 이슈 리포팅

### 버그 리포트

```markdown
## 버그 설명
<!-- 버그를 명확하게 설명해주세요 -->

## 재현 단계
1. '...'으로 이동
2. '...'를 클릭
3. 아래로 스크롤하여 '...' 확인
4. 오류 발생

## 예상 동작
<!-- 기대했던 동작을 설명해주세요 -->

## 실제 동작
<!-- 실제로 발생한 동작을 설명해주세요 -->

## 환경 정보
- OS: [예: macOS 14.0]
- Python: [예: 3.12.0]
- VTC-Link 버전: [예: 1.0.0]

## 로그/스크린샷
<!-- 관련 로그나 스크린샷을 첨부해주세요 -->
```

### 기능 요청

```markdown
## 기능 설명
<!-- 요청하는 기능을 설명해주세요 -->

## 사용 사례
<!-- 이 기능이 필요한 상황을 설명해주세요 -->

## 제안 구현 방법
<!-- 가능하다면 구현 방법을 제안해주세요 -->

## 대안
<!-- 고려한 대안이 있다면 설명해주세요 -->
```

### 라벨

| 라벨 | 설명 |
|------|------|
| `bug` | 버그 리포트 |
| `enhancement` | 기능 개선 요청 |
| `documentation` | 문서 관련 |
| `good first issue` | 입문자용 이슈 |
| `help wanted` | 도움 필요 |
| `question` | 질문 |
| `wontfix` | 수정하지 않음 |

---

## 개발 가이드라인

### 새 커넥터 추가

```python
# app/connectors/my_new_connector.py
"""새로운 데이터 소스 커넥터"""

from app.core.config import HospitalConfig
from app.core.logger import log_event


def fetch_records(hospital: HospitalConfig) -> list[dict]:
    """데이터 소스에서 레코드를 가져옵니다.

    Args:
        hospital: 병원 설정

    Returns:
        가져온 레코드 목록
    """
    log_event(
        event="fetch_start",
        level="INFO",
        hospital_id=hospital.hospital_id,
        stage="fetch",
        message="Fetching records from new connector",
    )

    # 구현
    records = []

    log_event(
        event="fetch_complete",
        level="INFO",
        hospital_id=hospital.hospital_id,
        stage="fetch",
        message=f"Fetched {len(records)} records",
        record_count=len(records),
    )

    return records
```

### 새 변환 프로필 추가

```python
# app/transforms/hospital_profiles/HOSP_NEW/__init__.py
"""HOSP_NEW 병원 변환 프로필"""

from .inbound import to_canonical
from .outbound import from_client_response

__all__ = ["to_canonical", "from_client_response"]
```

```python
# app/transforms/hospital_profiles/HOSP_NEW/inbound.py
"""인바운드 변환: 병원 데이터 -> 정규 포맷"""

from app.models.canonical import CanonicalPayload
from app.utils.parsing import parse_int, parse_float


def to_canonical(record: dict) -> CanonicalPayload:
    """병원 레코드를 정규 포맷으로 변환합니다."""
    return CanonicalPayload(
        patient={
            "patient_id": record.get("PT_NO"),
            "patient_name": record.get("PT_NM"),
            # ...
        },
        vitals={
            "SBP": parse_int(record.get("SYSTOLIC"), "SBP"),
            "DBP": parse_int(record.get("DIASTOLIC"), "DBP"),
            "BT": parse_float(record.get("TEMP"), "BT"),
            # ...
        },
        # ...
    )
```

### 에러 처리

```python
from app.core.errors import VTCLinkError


class ConnectorError(VTCLinkError):
    """커넥터 관련 에러"""
    pass


class ParseError(VTCLinkError):
    """파싱 관련 에러"""
    pass


# 사용 예시
def parse_value(value: str) -> int:
    try:
        return int(value)
    except ValueError as e:
        raise ParseError(f"정수 변환 실패: {value}") from e
```

---

## 테스트 작성 가이드

### 테스트 파일 구조

```
tests/
├── test_parsing.py           # app/utils/parsing.py 테스트
├── test_postprocess.py       # app/core/postprocess.py 테스트
├── test_pipeline_logging.py  # 파이프라인 통합 테스트
├── test_scheduler.py         # 스케줄러 테스트
└── test_admin_config.py      # Admin API 테스트
```

### 테스트 작성 원칙

```python
def test_function_name_describes_behavior():
    """함수가 특정 조건에서 예상대로 동작하는지 검증"""
    # Arrange (준비)
    input_data = "test"

    # Act (실행)
    result = function_under_test(input_data)

    # Assert (검증)
    assert result == expected_value
```

자세한 테스트 가이드는 [테스트 문서](testing.md)를 참조하세요.

---

## 라이센스

VTC-Link는 **MIT 라이센스**로 배포됩니다.

```
MIT License

Copyright (c) 2024 VTC-Link Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 기여 시 동의 사항

프로젝트에 기여함으로써 다음에 동의하는 것으로 간주됩니다:

- 귀하의 기여는 MIT 라이센스 하에 배포됩니다
- 귀하는 해당 기여에 대한 권리를 보유합니다
- 귀하의 기여가 제3자의 권리를 침해하지 않습니다

---

## 도움 받기

### 커뮤니케이션 채널

- **GitHub Issues**: 버그 리포트, 기능 요청
- **GitHub Discussions**: 일반 질문, 아이디어 공유
- **Pull Requests**: 코드 기여

### 질문하기

질문 전 확인사항:

1. [README](../../README.md) 확인
2. [문서](../index.md) 검색
3. 기존 이슈 검색
4. Google 검색

그래도 해결되지 않으면 이슈를 생성해 주세요!

---

## 감사의 말

모든 기여자분들께 감사드립니다! 작은 기여라도 프로젝트 발전에 큰 도움이 됩니다.

기여 방법:

- 버그 리포트
- 기능 제안
- 문서 개선
- 코드 기여
- 번역
- 테스트 추가

**함께 만들어가는 VTC-Link!**

---

## 다음 단계

- [테스트 가이드](testing.md) - 테스트 작성 방법
- [배포 가이드](deployment.md) - 프로덕션 배포
- [아키텍처](architecture.md) - 시스템 구조 이해
