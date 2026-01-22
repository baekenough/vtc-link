from fastapi import APIRouter

from app.clients.backend_api import send_payload
from app.core.config import load_app_config
from app.transforms.hospital_profiles.HOSP_A.inbound import to_canonical
from app.core.postprocess import run_postprocess
from app.transforms.hospital_profiles.HOSP_A.outbound import from_backend, to_backend

router = APIRouter()


@router.post("/push")
def push_vitals(payload: dict) -> dict:
    """병원 푸시 페이로드를 수신

    Args:
        payload: 병원 원본 페이로드

    Returns:
        처리 결과
    """
    config = load_app_config()
    hospital = config.hospital
    canonical = to_canonical(payload)
    backend_payload = to_backend(canonical)
    response = send_payload(backend_payload)
    postprocess_ok, postprocess_code = run_postprocess(hospital, canonical.model_dump())
    if not postprocess_ok:
        return {"status": "postprocess_failed", "error_code": postprocess_code}
    return from_backend(response)
