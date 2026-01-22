from __future__ import annotations

from datetime import datetime, timezone

from app.clients.backend_api import send_payload
from app.connectors.mssql_view_fetch import fetch_records as fetch_mssql
from app.connectors.oracle_view_fetch import fetch_records as fetch_oracle
from app.connectors.rest_pull_fetch import fetch_records as fetch_rest
from app.core.logger import log_event
from app.core.telemetry import TelemetryStore
from app.models.canonical import CanonicalPayload
from app.transforms.hospital_profiles.HOSP_A.inbound import to_canonical
from app.transforms.hospital_profiles.HOSP_A.outbound import from_backend, to_backend
from app.core.postprocess import run_postprocess


def run_pull_pipeline(hospital) -> None:
    """풀 방식 병원의 파이프라인을 실행

    Args:
        hospital: 병원 설정 객체
    """
    start = datetime.now(timezone.utc)
    log_event("pipeline_start", "INFO", hospital.hospital_id, "fetch", "수집 시작")
    try:
        if hospital.connector_type == "pull_db_view" and hospital.db:
            if hospital.db.get("type") == "oracle":
                raw_records = fetch_oracle(hospital)
            elif hospital.db.get("type") == "mssql":
                raw_records = fetch_mssql(hospital)
            else:
                raw_records = []
        elif hospital.connector_type == "pull_rest_api":
            raw_records = fetch_rest(hospital)
        else:
            raw_records = []
        canonical_records = [to_canonical(raw).model_dump() for raw in raw_records]
        postprocess_ok = True
        for record in canonical_records:
            backend_payload = to_backend(CanonicalPayload(**record))
            response = send_payload(backend_payload)
            _ = from_backend(response)
            postprocess_ok, postprocess_code = run_postprocess(hospital, record)
            if not postprocess_ok:
                log_event(
                    "postprocess_failed",
                    "ERROR",
                    hospital.hospital_id,
                    "postprocess",
                    "후처리 실패",
                    error_code=postprocess_code,
                    record_count=1,
                )
                break
        log_event(
            "pipeline_complete",
            "INFO",
            hospital.hospital_id,
            "postprocess",
            "파이프라인 완료",
            record_count=len(canonical_records),
            duration_ms=int(
                (datetime.now(timezone.utc) - start).total_seconds() * 1000
            ),
        )
        TelemetryStore().update_status(
            {
                "hospital_id": hospital.hospital_id,
                "last_run_at": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "last_success_at": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "last_status": "성공",
                "last_error_code": None,
                "postprocess_fail_count": 0 if postprocess_ok else 1,
            }
        )
    except Exception as exc:
        log_event(
            "pipeline_failed",
            "ERROR",
            hospital.hospital_id,
            "pipeline",
            str(exc),
        )
        TelemetryStore().update_status(
            {
                "hospital_id": hospital.hospital_id,
                "last_run_at": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "last_success_at": None,
                "last_status": "실패",
                "last_error_code": "PIPE_STAGE_001",
                "postprocess_fail_count": 1,
            }
        )
