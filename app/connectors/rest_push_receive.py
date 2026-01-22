from __future__ import annotations

from app.core.config import HospitalConfig


def receive_payload(config: HospitalConfig, payload: dict) -> list[dict]:
    """병원 푸시 페이로드를 수신

    Args:
        config: 병원 설정
        payload: 병원 원본 페이로드

    Returns:
        원본 레코드 목록
    """
    _ = config
    if isinstance(payload, list):
        return payload
    return [payload]
