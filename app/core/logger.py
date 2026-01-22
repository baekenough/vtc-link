from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.telemetry import TelemetryStore


def log_event(
    event: str,
    level: str,
    hospital_id: str,
    stage: str,
    message: str,
    error_code: str | None = None,
    duration_ms: int | None = None,
    record_count: int | None = None,
) -> None:
    """이벤트를 표준 로깅과 DuckDB에 기록

    Args:
        event: 이벤트 이름
        level: 로깅 레벨 문자열
        hospital_id: 병원 식별자
        stage: 파이프라인 단계
        message: 로그 메시지
        error_code: 에러 코드(선택)
        duration_ms: 처리 시간(밀리초, 선택)
        record_count: 레코드 수(선택)
    """
    logger = logging.getLogger("vtc-link")
    extra = {
        "event": event,
        "hospital_id": hospital_id,
        "stage": stage,
    }
    logger.log(getattr(logging, level.upper(), logging.INFO), message, extra=extra)

    TelemetryStore().insert_log(
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": level.upper(),
            "event": event,
            "hospital_id": hospital_id,
            "stage": stage,
            "error_code": error_code,
            "message": message,
            "duration_ms": duration_ms,
            "record_count": record_count,
        }
    )
