from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable


def coerce_int(value: object, default: int = 0) -> int:
    """값을 정수로 변환

    Args:
        value: 원본 값
        default: 실패 시 기본값

    Returns:
        정수 값
    """
    if value is None:
        return default
    text = str(value).strip()
    if text == "":
        return default
    try:
        return int(text)
    except ValueError:
        try:
            return int(float(text))
        except ValueError:
            return default


def format_screened_date(value: object, formats: Iterable[str]) -> str:
    """Screened Date 정규화

    Args:
        value: 원본 값
        formats: 허용 포맷 목록

    Returns:
        YYYYMMDD HH:MM:SS 문자열
    """
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d %H:%M:%S")
    text = str(value).strip()
    if text == "":
        return ""
    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.strftime("%Y%m%d %H:%M:%S")
        except ValueError:
            continue
    return text


from app.core.errors import ParseError


def parse_int(value: str | int | float | None, field: str) -> int:
    """값을 정수로 파싱

    Args:
        value: 원본 값
        field: 에러 메시지에 사용할 필드명

    Returns:
        파싱된 정수 값

    Raises:
        ParseError: 파싱 실패 시
    """
    if value is None:
        raise ParseError(field, "값이 필요함")
    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise ParseError(field, f"정수가 아님: {value}") from exc


def parse_int_optional(value: str | int | float | None) -> int | None:
    """값이 있으면 정수로 파싱

    Args:
        value: 원본 값

    Returns:
        파싱된 정수 또는 None

    Raises:
        ParseError: 파싱 실패 시
    """
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError as exc:
        raise ParseError("age", f"정수가 아님: {value}") from exc


def parse_float(value: str | int | float | None, field: str) -> float:
    """값을 실수로 파싱

    Args:
        value: 원본 값
        field: 에러 메시지에 사용할 필드명

    Returns:
        파싱된 실수 값

    Raises:
        ParseError: 파싱 실패 시
    """
    if value is None:
        raise ParseError(field, "값이 필요함")
    try:
        return float(str(value).strip())
    except ValueError as exc:
        raise ParseError(field, f"실수가 아님: {value}") from exc


def parse_birthdate(value: str | None, formats: Iterable[str]) -> str:
    """생년월일을 YYYYMMDD 형식으로 파싱

    Args:
        value: 원본 생년월일 값
        formats: 허용 포맷 목록

    Returns:
        YYYYMMDD 형식의 생년월일

    Raises:
        ParseError: 파싱 실패 시
    """
    if value is None:
        raise ParseError("birthdate", "값이 필요함")
    for fmt in formats:
        try:
            return datetime.strptime(str(value).strip(), fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    raise ParseError("birthdate", f"지원하지 않는 생년월일 형식: {value}")


def parse_timestamp(value: str | None, formats: Iterable[str]) -> str:
    """타임스탬프를 UTC ISO8601 형식으로 파싱

    Args:
        value: 원본 타임스탬프 값
        formats: 허용 포맷 목록

    Returns:
        UTC ISO8601 형식의 타임스탬프

    Raises:
        ParseError: 파싱 실패 시
    """
    if value is None:
        raise ParseError("timestamp", "값이 필요함")
    for fmt in formats:
        try:
            parsed = datetime.strptime(str(value).strip(), fmt)
            parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.isoformat().replace("+00:00", "Z")
        except ValueError:
            continue
    raise ParseError("timestamp", f"지원하지 않는 타임스탬프 형식: {value}")
