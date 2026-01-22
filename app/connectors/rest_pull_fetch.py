from __future__ import annotations

from app.core.config import HospitalConfig
import httpx


def fetch_records(config: HospitalConfig) -> list[dict]:
    """병원 REST API에서 레코드를 조회

    Args:
        config: 병원 설정

    Returns:
        원본 레코드 목록
    """
    if not config.api:
        return []
    url = str(config.api.get("url", "")).strip()
    if not url:
        return []
    headers = {}
    api_key = str(config.api.get("api_key", "")).strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("records", [])
    return []
