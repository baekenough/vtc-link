from app.core.errors import ParseError
from app.models.canonical import CanonicalPayload, Patient, Timestamps, Vitals
from app.transforms.hospital_profiles.HOSP_A.mapping import SEX_MAPPING
from app.utils.parsing import (
    parse_birthdate,
    parse_float,
    parse_int,
    parse_int_optional,
    parse_timestamp,
)

BIRTHDATE_FORMATS = ["%Y%m%d", "%Y-%m-%d"]
TIMESTAMP_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]


def _trim_text(value: object, max_length: int) -> str | None:
    """문자열 정리와 길이 제한

    Args:
        value: 원본 값
        max_length: 최대 길이

    Returns:
        정리된 문자열 또는 None
    """
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    return text[:max_length]


def _map_sex(value: str | None) -> str:
    """성별 값을 캐노니컬 포맷으로 매핑

    Args:
        value: 원본 성별 값

    Returns:
        캐노니컬 성별 코드

    Raises:
        ParseError: 매핑 실패 시
    """
    if value is None:
        raise ParseError("sex", "값이 필요함")
    mapped = SEX_MAPPING.get(str(value).strip())
    if mapped is None:
        raise ParseError("sex", f"지원하지 않는 값: {value}")
    return mapped


def to_canonical(raw: dict) -> CanonicalPayload:
    """병원 페이로드를 캐노니컬 모델로 변환

    Args:
        raw: 병원 원본 페이로드

    Returns:
        캐노니컬 페이로드 모델
    """
    patient = Patient(
        patient_id=str(raw.get("patient_id", "")).strip(),
        patient_name=raw.get("patient_name"),
        birthdate=parse_birthdate(raw.get("birthdate"), BIRTHDATE_FORMATS),
        age=parse_int_optional(raw.get("age")),
        sex=_map_sex(raw.get("sex")),
        ward=_trim_text(raw.get("ward"), 30),
        department=_trim_text(raw.get("department"), 30),
    )
    vitals = Vitals(
        SBP=parse_int(raw.get("SBP"), "SBP"),
        DBP=parse_int(raw.get("DBP"), "DBP"),
        PR=parse_int(raw.get("PR"), "PR"),
        RR=parse_int(raw.get("RR"), "RR"),
        BT=parse_float(raw.get("BT"), "BT"),
        SpO2=parse_float(raw.get("SpO2"), "SpO2"),
    )
    timestamps = Timestamps(
        created_at=parse_timestamp(raw.get("created_at"), TIMESTAMP_FORMATS),
        updated_at=parse_timestamp(raw.get("updated_at"), TIMESTAMP_FORMATS),
    )
    return CanonicalPayload(patient=patient, vitals=vitals, timestamps=timestamps)
