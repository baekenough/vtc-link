from __future__ import annotations

from app.core.config import HospitalConfig
from app.core.db import oracle_connection, mssql_connection


def insert_records(config: HospitalConfig, payload: dict) -> dict:
    """병원 DB에 레코드를 삽입

    Args:
        config: 병원 설정
        payload: 삽입할 페이로드

    Returns:
        삽입 결과
    """
    if not config.db:
        return {"inserted": 0}
    table = config.db.get("insert_table")
    if not table:
        return {"inserted": 0}
    columns = config.db.get("insert_columns", [])
    if not columns:
        return {"inserted": 0}
    values = [payload.get(col) for col in columns]
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)
    query = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"

    if config.db.get("type") == "oracle":
        with oracle_connection(config.db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
        return {"inserted": 1}
    if config.db.get("type") == "mssql":
        with mssql_connection(config.db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
        return {"inserted": 1}
    return {"inserted": 0}
