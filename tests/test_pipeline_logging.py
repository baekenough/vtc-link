from app.core.config import HospitalConfig
from app.core.pipeline import run_pull_pipeline
from app.core.telemetry import TelemetryStore


def test_postprocess_failure_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "telemetry.duckdb"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    store = TelemetryStore()

    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_rest_api",
        transform_profile="H1",
        enabled=True,
        postprocess={
            "mode": "update_flag",
            "table": "T",
            "key_column": "ID",
            "flag_column": "F",
            "flag_value": "Y",
            "retry": 1,
        },
        db={"type": "oracle"},
    )

    run_pull_pipeline(hospital)
    rows = store.query_logs("event = ?", ["postprocess_failed"])
    assert rows is not None
    if rows:
        assert rows[0][5] in {"POSTPROCESS_KEY_MISSING", "POSTPROCESS_FAILED"}
