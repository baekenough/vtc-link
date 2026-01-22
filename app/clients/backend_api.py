from __future__ import annotations

import httpx

from app.core.config import get_settings


def send_payload(payload: dict) -> dict:
    """백엔드 API로 페이로드를 전송

    Args:
        payload: 백엔드 페이로드

    Returns:
        백엔드 응답 페이로드
    """
    settings = get_settings()
    headers = {}
    if settings.backend_api_key:
        headers["Authorization"] = f"Bearer {settings.backend_api_key}"
    with httpx.Client(timeout=10.0) as client:
        response = client.post(settings.backend_base_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
