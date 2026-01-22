from __future__ import annotations

from pathlib import Path

import duckdb

from app.core.config import get_settings


class TelemetryStore:
    """로그와 상태를 저장하는 DuckDB 텔레메트리 저장소"""

    _instance: "TelemetryStore | None" = None

    def __new__(cls) -> "TelemetryStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self) -> None:
        settings = get_settings()
        Path(settings.duckdb_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(settings.duckdb_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                timestamp TIMESTAMP,
                level VARCHAR,
                event VARCHAR,
                hospital_id VARCHAR,
                stage VARCHAR,
                error_code VARCHAR,
                message VARCHAR,
                duration_ms INTEGER,
                record_count INTEGER
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hospital_status (
                hospital_id VARCHAR,
                last_run_at TIMESTAMP,
                last_success_at TIMESTAMP,
                last_status VARCHAR,
                last_error_code VARCHAR,
                postprocess_fail_count INTEGER
            )
            """
        )

    def insert_log(self, record: dict) -> None:
        """로그 레코드를 저장

        Args:
            record: 로그 레코드 딕셔너리
        """
        self._conn.execute(
            """
            INSERT INTO logs (timestamp, level, event, hospital_id, stage, error_code, message, duration_ms, record_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                record.get("timestamp"),
                record.get("level"),
                record.get("event"),
                record.get("hospital_id"),
                record.get("stage"),
                record.get("error_code"),
                record.get("message"),
                record.get("duration_ms"),
                record.get("record_count"),
            ],
        )

    def update_status(self, status: dict) -> None:
        """병원 상태 레코드를 업서트

        Args:
            status: 상태 레코드 딕셔너리
        """
        self._conn.execute(
            """
            DELETE FROM hospital_status WHERE hospital_id = ?
            """,
            [status.get("hospital_id")],
        )
        self._conn.execute(
            """
            INSERT INTO hospital_status (hospital_id, last_run_at, last_success_at, last_status, last_error_code, postprocess_fail_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                status.get("hospital_id"),
                status.get("last_run_at"),
                status.get("last_success_at"),
                status.get("last_status"),
                status.get("last_error_code"),
                status.get("postprocess_fail_count"),
            ],
        )

    def query_logs(self, where: str, params: list) -> list[tuple]:
        """조건절(WHERE)을 사용해 로그를 조회

        Args:
            where: SQL WHERE 절
            params: 파라미터 목록

        Returns:
            행 목록
        """
        query = "SELECT * FROM logs"
        if where:
            query += f" WHERE {where}"
        return self._conn.execute(query, params).fetchall()

    def query_status(self) -> list[tuple]:
        """모든 병원 상태 항목을 조회

        Returns:
            행 목록
        """
        return self._conn.execute(
            "SELECT * FROM hospital_status ORDER BY hospital_id"
        ).fetchall()
