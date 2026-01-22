from __future__ import annotations

from app.core.config import HospitalConfig
from app.core.db import mssql_connection, oracle_connection


def _resolve_value(source: str | None, record: dict | None, fallback: object) -> object:
    """값 해석

    Args:
        source: 레코드 키
        record: 레코드 데이터
        fallback: 기본값

    Returns:
        해석된 값
    """
    if record is None or source is None:
        return fallback
    if source == "":
        return fallback
    return record.get(source, fallback)


def run_postprocess(
    hospital: HospitalConfig, record: dict | None = None
) -> tuple[bool, str | None]:
    """후처리를 실행

    Args:
        hospital: 병원 설정 객체
        record: 레코드 데이터

    Returns:
        성공 여부, 에러 코드
    """
    if hospital.postprocess is None:
        return True, None

    retries = int(hospital.postprocess.get("retry", 3))
    last_ok = False
    last_code: str | None = "POSTPROCESS_FAILED"
    for _ in range(retries):
        last_ok, last_code = _run_postprocess_once(hospital, record)
        if last_ok:
            return True, None
    return last_ok, last_code


def _run_postprocess_once(
    hospital: HospitalConfig, record: dict | None
) -> tuple[bool, str | None]:
    """후처리 단일 실행

    Args:
        hospital: 병원 설정 객체
        record: 레코드 데이터

    Returns:
        성공 여부, 에러 코드
    """
    if hospital.postprocess is None:
        return True, None
    mode = hospital.postprocess.get("mode")
    if mode == "update_flag":
        return _update_flag(hospital, record)
    if mode == "insert_log":
        return _insert_log(hospital, record)
    return False, "POSTPROCESS_UNSUPPORTED"


def _update_flag(
    hospital: HospitalConfig, record: dict | None
) -> tuple[bool, str | None]:
    """플래그 업데이트

    Args:
        hospital: 병원 설정 객체
        record: 레코드 데이터

    Returns:
        성공 여부, 에러 코드
    """
    if not hospital.db or not hospital.postprocess:
        return False, "POSTPROCESS_CONFIG_MISSING"
    table = hospital.postprocess.get("table")
    key_column = hospital.postprocess.get("key_column")
    flag_column = hospital.postprocess.get("flag_column")
    flag_value = hospital.postprocess.get("flag_value")
    key_value = _resolve_value(
        hospital.postprocess.get("key_value_source"),
        record,
        hospital.postprocess.get("key_value"),
    )
    if not all([table, key_column, flag_column]):
        return False, "POSTPROCESS_CONFIG_MISSING"
    if key_value is None:
        return False, "POSTPROCESS_KEY_MISSING"
    query = f"UPDATE {table} SET {flag_column} = ? WHERE {key_column} = ?"
    values = [flag_value, key_value]
    if hospital.db.get("type") == "oracle":
        with oracle_connection(hospital.db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
        return True, None
    if hospital.db.get("type") == "mssql":
        with mssql_connection(hospital.db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
        return True, None
    return False, "POSTPROCESS_DB_UNSUPPORTED"


def _insert_log(
    hospital: HospitalConfig, record: dict | None
) -> tuple[bool, str | None]:
    """로그 테이블 삽입

    Args:
        hospital: 병원 설정 객체
        record: 레코드 데이터

    Returns:
        성공 여부, 에러 코드
    """
    if not hospital.db or not hospital.postprocess:
        return False, "POSTPROCESS_CONFIG_MISSING"
    table = hospital.postprocess.get("table")
    columns = hospital.postprocess.get("columns", [])
    values_map = hospital.postprocess.get("values", {})
    sources_map = hospital.postprocess.get("sources", {})
    if not table or not columns:
        return False, "POSTPROCESS_CONFIG_MISSING"
    values = [
        _resolve_value(sources_map.get(col), record, values_map.get(col))
        for col in columns
    ]
    if any(value is None for value in values):
        return False, "POSTPROCESS_VALUE_MISSING"
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)
    query = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"
    if hospital.db.get("type") == "oracle":
        with oracle_connection(hospital.db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
        return True, None
    if hospital.db.get("type") == "mssql":
        with mssql_connection(hospital.db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
        return True, None
    return False, "POSTPROCESS_DB_UNSUPPORTED"
