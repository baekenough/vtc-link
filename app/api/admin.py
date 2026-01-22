from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import yaml

from app.core.auth import require_admin
from app.core.config import get_settings, load_app_config, reload_app_config
from app.core.scheduler import start_scheduler
from app.core.telemetry import TelemetryStore

router = APIRouter()

templates = Jinja2Templates(directory="templates")


def _validate_hospital(hospital: dict) -> list[str]:
    """병원 설정 유효성 검사

    Args:
        hospital: 병원 설정

    Returns:
        에러 목록
    """
    errors: list[str] = []
    connector_type = str(hospital.get("connector_type", "")).strip()
    hospital_id = str(hospital.get("hospital_id", "")).strip()
    transform_profile = str(hospital.get("transform_profile", "")).strip()
    schedule_minutes = hospital.get("schedule_minutes")
    allowed_connectors = {
        "pull_db_view",
        "pull_rest_api",
        "push_rest_api",
        "push_db_insert",
    }

    if not hospital_id:
        errors.append("hospital_id 필요")
    if connector_type not in allowed_connectors:
        errors.append("connector_type 값 오류")
    if not transform_profile:
        errors.append("transform_profile 필요")

    if connector_type in {"pull_db_view", "pull_rest_api"}:
        if not isinstance(schedule_minutes, int) or schedule_minutes <= 0:
            errors.append("schedule_minutes 양수 필요")

    db = hospital.get("db") or {}
    needs_db = connector_type in {"pull_db_view", "push_db_insert"}
    postprocess = hospital.get("postprocess") or {}
    post_mode = str(postprocess.get("mode", "")).strip()
    if post_mode in {"update_flag", "insert_log"}:
        needs_db = True

    if needs_db:
        db_type = str(db.get("type", "")).strip()
        if db_type not in {"oracle", "mssql"}:
            errors.append("db.type 값 오류")
        if db_type == "oracle":
            if not str(db.get("host", "")).strip():
                errors.append("db.host 필요")
            if not str(db.get("service", "")).strip():
                errors.append("db.service 필요")
        if db_type == "mssql":
            if not str(db.get("host", "")).strip():
                errors.append("db.host 필요")

    api = hospital.get("api") or {}
    if connector_type == "pull_rest_api":
        if not str(api.get("url", "")).strip():
            errors.append("api.url 필요")

    if post_mode:
        if post_mode not in {"update_flag", "insert_log"}:
            errors.append("postprocess.mode 값 오류")
        if post_mode == "update_flag":
            if not str(postprocess.get("table", "")).strip():
                errors.append("postprocess.table 필요")
            if not str(postprocess.get("key_column", "")).strip():
                errors.append("postprocess.key_column 필요")
            if not str(postprocess.get("flag_column", "")).strip():
                errors.append("postprocess.flag_column 필요")
            key_value = str(postprocess.get("key_value", "")).strip()
            key_source = str(postprocess.get("key_value_source", "")).strip()
            if not key_value and not key_source:
                errors.append("postprocess.key_value 또는 key_value_source 필요")
        if post_mode == "insert_log":
            if not str(postprocess.get("table", "")).strip():
                errors.append("postprocess.table 필요")
            columns = postprocess.get("columns", [])
            if not columns:
                errors.append("postprocess.columns 필요")
            values = postprocess.get("values", {})
            sources = postprocess.get("sources", {})
            for col in columns:
                if col not in values and col not in sources:
                    errors.append(f"postprocess 컬럼 누락: {col}")
    return errors


@router.get("/logs", response_class=HTMLResponse)
def admin_logs(request: Request, admin: None = Depends(require_admin)) -> HTMLResponse:
    """로그 페이지 렌더링

    Args:
        request: FastAPI 요청 객체
        admin: 관리자 인증 의존성

    Returns:
        HTML 응답
    """
    rows = TelemetryStore().query_logs("", [])
    logs = [
        {
            "timestamp": row[0],
            "level": row[1],
            "event": row[2],
            "hospital_id": row[3],
            "stage": row[4],
            "error_code": row[5],
            "message": row[6],
            "duration_ms": row[7],
            "record_count": row[8],
        }
        for row in rows
    ]
    return templates.TemplateResponse(
        "admin/logs.html",
        {"request": request, "logs": logs},
    )


@router.get("/status", response_class=HTMLResponse)
def admin_status(
    request: Request, admin: None = Depends(require_admin)
) -> HTMLResponse:
    """상태 페이지 렌더링

    Args:
        request: FastAPI 요청 객체
        admin: 관리자 인증 의존성

    Returns:
        HTML 응답
    """
    rows = TelemetryStore().query_status()
    status_list = [
        {
            "hospital_id": row[0],
            "last_run_at": row[1],
            "last_success_at": row[2],
            "last_status": row[3],
            "last_error_code": row[4],
            "postprocess_fail_count": row[5],
        }
        for row in rows
    ]
    return templates.TemplateResponse(
        "admin/status.html",
        {"request": request, "status_list": status_list},
    )


@router.get("/config", response_class=HTMLResponse)
def admin_config(
    request: Request, admin: None = Depends(require_admin)
) -> HTMLResponse:
    """설정 페이지 렌더링

    Args:
        request: FastAPI 요청 객체
        admin: 관리자 인증 의존성

    Returns:
        HTML 응답
    """
    config = load_app_config().model_dump()
    return templates.TemplateResponse(
        "admin/config.html",
        {"request": request, "config": config, "errors": []},
    )


@router.post("/config", response_class=HTMLResponse)
async def save_config(
    request: Request, admin: None = Depends(require_admin)
) -> HTMLResponse:
    """설정 저장

    Args:
        request: FastAPI 요청 객체
        admin: 관리자 인증 의존성

    Returns:
        HTML 응답
    """
    settings = get_settings()
    config = load_app_config().model_dump()
    form_data = await request.form()

    hospital = config.get("hospital", {})
    prefix = "hospital-"
    hospital_id = form_data.get(prefix + "hospital_id")
    connector_type = form_data.get(prefix + "connector_type")
    enabled_value = form_data.get(prefix + "enabled")
    schedule_minutes = form_data.get(prefix + "schedule_minutes")
    transform_profile = form_data.get(prefix + "transform_profile")
    db_type = form_data.get(prefix + "db-type")
    db_host = form_data.get(prefix + "db-host")
    db_port = form_data.get(prefix + "db-port")
    db_service = form_data.get(prefix + "db-service")
    db_database = form_data.get(prefix + "db-database")
    db_username = form_data.get(prefix + "db-username")
    db_password = form_data.get(prefix + "db-password")
    db_view_name = form_data.get(prefix + "db-view_name")
    db_query = form_data.get(prefix + "db-query")
    db_insert_table = form_data.get(prefix + "db-insert_table")
    db_insert_columns = form_data.get(prefix + "db-insert_columns")
    api_url = form_data.get(prefix + "api-url")
    api_key = form_data.get(prefix + "api-api_key")
    post_mode = form_data.get(prefix + "postprocess-mode")
    post_table = form_data.get(prefix + "postprocess-table")
    post_key_column = form_data.get(prefix + "postprocess-key_column")
    post_key_value = form_data.get(prefix + "postprocess-key_value")
    post_key_value_source = form_data.get(prefix + "postprocess-key_value_source")
    post_flag_column = form_data.get(prefix + "postprocess-flag_column")
    post_flag_value = form_data.get(prefix + "postprocess-flag_value")
    post_columns = form_data.get(prefix + "postprocess-columns")
    post_values = form_data.get(prefix + "postprocess-values")
    post_sources = form_data.get(prefix + "postprocess-sources")
    post_retry = form_data.get(prefix + "postprocess-retry")

    if hospital_id is not None:
        hospital["hospital_id"] = str(hospital_id).strip()
    if connector_type is not None:
        hospital["connector_type"] = str(connector_type).strip()
    if enabled_value is not None:
        hospital["enabled"] = str(enabled_value).lower() == "true"
    if schedule_minutes is not None:
        try:
            hospital["schedule_minutes"] = int(str(schedule_minutes))
        except ValueError:
            pass
    if transform_profile is not None:
        hospital["transform_profile"] = str(transform_profile).strip()

    db_config = hospital.get("db") or {}
    if db_type is not None:
        db_config["type"] = str(db_type).strip()
    if db_host is not None:
        db_config["host"] = str(db_host).strip()
    if db_port is not None:
        db_config["port"] = str(db_port).strip()
    if db_service is not None:
        db_config["service"] = str(db_service).strip()
    if db_database is not None:
        db_config["database"] = str(db_database).strip()
    if db_username is not None:
        db_config["username"] = str(db_username).strip()
    if db_password is not None:
        db_config["password"] = str(db_password).strip()
    if db_view_name is not None:
        db_config["view_name"] = str(db_view_name).strip()
    if db_query is not None:
        db_config["query"] = str(db_query).strip()
    if db_insert_table is not None:
        db_config["insert_table"] = str(db_insert_table).strip()
    if db_insert_columns is not None:
        db_config["insert_columns"] = [
            value.strip()
            for value in str(db_insert_columns).split(",")
            if value.strip()
        ]
    hospital["db"] = db_config

    api_config = hospital.get("api") or {}
    if api_url is not None:
        api_config["url"] = str(api_url).strip()
    if api_key is not None:
        api_config["api_key"] = str(api_key).strip()
    hospital["api"] = api_config

    post_config = hospital.get("postprocess") or {}
    if post_mode is not None:
        post_config["mode"] = str(post_mode).strip()
    if post_table is not None:
        post_config["table"] = str(post_table).strip()
    if post_key_column is not None:
        post_config["key_column"] = str(post_key_column).strip()
    if post_key_value is not None:
        post_config["key_value"] = str(post_key_value).strip()
    if post_key_value_source is not None:
        post_config["key_value_source"] = str(post_key_value_source).strip()
    if post_flag_column is not None:
        post_config["flag_column"] = str(post_flag_column).strip()
    if post_flag_value is not None:
        post_config["flag_value"] = str(post_flag_value).strip()
    if post_columns is not None:
        post_config["columns"] = [
            value.strip() for value in str(post_columns).split(",") if value.strip()
        ]
    if post_values is not None:
        try:
            post_config["values"] = yaml.safe_load(str(post_values)) or {}
        except yaml.YAMLError:
            pass
    if post_sources is not None:
        try:
            post_config["sources"] = yaml.safe_load(str(post_sources)) or {}
        except yaml.YAMLError:
            pass
    if post_retry is not None:
        try:
            post_config["retry"] = int(str(post_retry))
        except ValueError:
            pass
    hospital["postprocess"] = post_config

    config["hospital"] = hospital

    errors = _validate_hospital(config.get("hospital", {}))
    if errors:
        return templates.TemplateResponse(
            "admin/config.html",
            {"request": request, "config": config, "errors": errors, "saved": False},
        )

    with open(settings.config_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, allow_unicode=True, sort_keys=False)

    if get_settings().scheduler_enabled:
        start_scheduler(reload_app_config())

    return templates.TemplateResponse(
        "admin/config.html",
        {"request": request, "config": config, "saved": True, "errors": []},
    )


@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(
    request: Request, admin: None = Depends(require_admin)
) -> HTMLResponse:
    """대시보드 페이지 렌더링

    Args:
        request: FastAPI 요청 객체
        admin: 관리자 인증 의존성

    Returns:
        HTML 응답
    """
    rows = TelemetryStore().query_status()
    status_list = [
        {
            "hospital_id": row[0],
            "last_run_at": row[1],
            "last_success_at": row[2],
            "last_status": row[3],
            "last_error_code": row[4],
            "postprocess_fail_count": row[5],
        }
        for row in rows
    ]
    log_rows = TelemetryStore().query_logs("", [])
    recent_logs = [
        {
            "timestamp": row[0],
            "level": row[1],
            "event": row[2],
            "hospital_id": row[3],
            "stage": row[4],
            "error_code": row[5],
            "message": row[6],
            "duration_ms": row[7],
            "record_count": row[8],
        }
        for row in log_rows
    ]
    stats = {
        "total_hospitals": 1 if load_app_config().hospital else 0,
        "today_records": 0,
        "success_rate": None,
        "error_count": 0,
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "stats": stats,
            "recent_status": status_list,
            "recent_logs": recent_logs,
        },
    )
