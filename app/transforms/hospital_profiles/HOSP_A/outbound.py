from app.models.canonical import CanonicalPayload
from app.models.client import ClientResponse
from app.utils.parsing import coerce_int, format_screened_date

SCREENED_DATE_FORMATS = [
    "%Y%m%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
]


def from_backend(response: dict) -> dict:
    """백엔드 응답을 병원 응답으로 변환

    Args:
        response: 백엔드 응답 페이로드

    Returns:
        병원 응답 페이로드
    """
    mapped = ClientResponse(
        vital_id=str(response.get("vital_id", "")),
        patient_id=str(response.get("patient_id", "")),
        screened_type=str(response.get("screened_type", "")),
        screened_date=format_screened_date(
            response.get("screened_date"), SCREENED_DATE_FORMATS
        ),
        SEPS=coerce_int(response.get("SEPS")),
        MAES=coerce_int(response.get("MAES")),
        MORS=coerce_int(response.get("MORS")),
        NEWS=coerce_int(response.get("NEWS")),
        MEWS=coerce_int(response.get("MEWS")),
        created_at=str(response.get("created_at", "")),
        updated_at=str(response.get("updated_at", "")),
    )
    return mapped.model_dump()


def to_backend(payload: CanonicalPayload) -> dict:
    """캐노니컬 페이로드를 백엔드 페이로드로 변환

    Args:
        payload: 캐노니컬 페이로드

    Returns:
        백엔드 페이로드 딕셔너리
    """
    return payload.model_dump()
