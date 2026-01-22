from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    """서비스 헬스 상태를 반환"""
    return {"status": "정상"}
