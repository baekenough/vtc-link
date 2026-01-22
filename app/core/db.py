from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import oracledb
import pyodbc


def _oracle_dsn(db: dict) -> str:
    """Oracle DSN 구성

    Args:
        db: DB 설정

    Returns:
        DSN 문자열
    """
    dsn = str(db.get("dsn", "")).strip()
    if dsn:
        return dsn
    host = str(db.get("host", "")).strip()
    port = str(db.get("port", "1521")).strip()
    service = str(db.get("service", "")).strip()
    if not host or not service:
        raise ValueError("Oracle 연결 정보 부족")
    return f"{host}:{port}/{service}"


def _mssql_conn_str(db: dict) -> str:
    """MSSQL 연결 문자열 구성

    Args:
        db: DB 설정

    Returns:
        연결 문자열
    """
    conn_str = str(db.get("connection_string", "")).strip()
    if conn_str:
        return conn_str
    driver = str(db.get("driver", "ODBC Driver 18 for SQL Server")).strip()
    host = str(db.get("host", "")).strip()
    port = str(db.get("port", "")).strip()
    database = str(db.get("database", "")).strip()
    if not host:
        raise ValueError("MSSQL 연결 정보 부족")
    server = f"{host},{port}" if port else host
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"UID={db.get('username', '')}",
        f"PWD={db.get('password', '')}",
        "TrustServerCertificate=yes",
    ]
    if database:
        parts.append(f"DATABASE={database}")
    return ";".join(parts)


@contextmanager
def oracle_connection(db: dict) -> Iterator[oracledb.Connection]:
    """Oracle 연결 생성

    Args:
        db: DB 설정

    Returns:
        Oracle 연결
    """
    dsn = _oracle_dsn(db)
    conn = oracledb.connect(
        user=db.get("username"),
        password=db.get("password"),
        dsn=dsn,
    )
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def mssql_connection(db: dict) -> Iterator[pyodbc.Connection]:
    """MSSQL 연결 생성

    Args:
        db: DB 설정

    Returns:
        MSSQL 연결
    """
    conn_str = _mssql_conn_str(db)
    conn = pyodbc.connect(conn_str)
    try:
        yield conn
    finally:
        conn.close()
