from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from app.core.config import get_settings


def require_admin(request: Request) -> None:
    """관리자 인증 검증

    Args:
        request: FastAPI 요청 객체

    Raises:
        HTTPException: 인증 실패 시
    """
    settings = get_settings()
    credentials = request.headers.get("Authorization", "")
    if not credentials.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 필요",
            headers={"WWW-Authenticate": "Basic"},
        )

    encoded = credentials.replace("Basic ", "", 1).strip()
    try:
        import base64

        decoded = base64.b64decode(encoded).decode("utf-8")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보 오류",
            headers={"WWW-Authenticate": "Basic"},
        ) from exc

    if ":" not in decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보 오류",
            headers={"WWW-Authenticate": "Basic"},
        )

    admin_id, admin_password = decoded.split(":", 1)
    if admin_id != settings.admin_id or admin_password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 실패",
            headers={"WWW-Authenticate": "Basic"},
        )
