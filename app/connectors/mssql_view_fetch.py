from __future__ import annotations

from app.core.config import HospitalConfig
from app.core.db import mssql_connection


def fetch_records(config: HospitalConfig) -> list[dict]:
    """MSSQL 뷰에서 레코드를 조회

    Args:
        config: 병원 설정

    Returns:
        원본 레코드 목록
    """
    if not config.db:
        return []
    query = config.db.get("query") or f"SELECT * FROM {config.db.get('view_name')}"
    with mssql_connection(config.db) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]
