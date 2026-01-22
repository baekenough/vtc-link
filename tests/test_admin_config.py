import base64

import os
import pytest

from fastapi.testclient import TestClient

from app.core.config import get_settings, load_app_config
from app.main import create_app


def _basic_auth_header(username: str, password: str) -> dict:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def _make_client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    config_path = tmp_path / "hospitals.yaml"
    config_path.write_text(
        """hospital:\n  hospital_id: HOSP_A\n  connector_type: pull_db_view\n  enabled: true\n  schedule_minutes: 5\n  transform_profile: HOSP_A\n""",
        encoding="utf-8",
    )
    monkeypatch.setenv("CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "telemetry.duckdb"))
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    get_settings.cache_clear()
    load_app_config.cache_clear()
    app = create_app()
    return TestClient(app)


def test_admin_config_page_returns_401_without_auth(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/admin/config")
    assert response.status_code == 401


def test_admin_config_save_returns_200_with_auth(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    headers = _basic_auth_header("admin", "admin")
    response = client.post("/admin/config", headers=headers, data={})
    assert response.status_code == 200


def test_admin_config_save_updates_values(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    headers = _basic_auth_header("admin", "admin")
    data = {
        "hospital-hospital_id": "HOSP_X",
        "hospital-connector_type": "pull_db_view",
        "hospital-enabled": "true",
        "hospital-schedule_minutes": "7",
        "hospital-transform_profile": "HOSP_X",
        "hospital-db-type": "oracle",
        "hospital-db-host": "127.0.0.1",
        "hospital-db-port": "1521",
        "hospital-db-service": "ORCLCDB",
        "hospital-db-username": "readonly",
        "hospital-db-password": "readonly",
        "hospital-db-view_name": "VITAL_VIEW",
        "hospital-db-query": "SELECT * FROM VITAL_VIEW",
        "hospital-db-insert_table": "VITAL_LOG",
        "hospital-db-insert_columns": "col1,col2",
        "hospital-api-url": "http://localhost/api",
        "hospital-api-api_key": "key",
        "hospital-postprocess-mode": "update_flag",
        "hospital-postprocess-table": "VITAL_VIEW",
        "hospital-postprocess-key_column": "ID",
        "hospital-postprocess-key_value": "VID",
        "hospital-postprocess-key_value_source": "vital_id",
        "hospital-postprocess-flag_column": "SENT_YN",
        "hospital-postprocess-flag_value": "Y",
        "hospital-postprocess-columns": "col1,col2",
        "hospital-postprocess-values": "{col1: 1, col2: 2}",
        "hospital-postprocess-sources": "{col1: key1, col2: key2}",
        "hospital-postprocess-retry": "3",
    }
    response = client.post("/admin/config", headers=headers, data=data)
    assert response.status_code == 200

    load_app_config.cache_clear()
    config = load_app_config().model_dump()
    assert config["hospital"]["hospital_id"] == "HOSP_X"
    assert config["hospital"]["schedule_minutes"] == 7
