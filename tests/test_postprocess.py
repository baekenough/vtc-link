from app.core.config import HospitalConfig
from app.core.postprocess import run_postprocess


def test_postprocess_no_config_returns_true():
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        postprocess=None,
    )
    ok, code = run_postprocess(hospital)
    assert ok is True
    assert code is None


def test_postprocess_missing_key_value_returns_false():
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
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
    ok, code = run_postprocess(hospital, {"vital_id": "VID"})
    assert ok is False
    assert code == "POSTPROCESS_KEY_MISSING"


def test_postprocess_resolves_key_value():
    """key_value_source가 있을 때 레코드에서 key_value를 해석하는지 테스트"""
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        postprocess={
            "mode": "update_flag",
            "table": "T",
            "key_column": "ID",
            "key_value": "fallback",
            "key_value_source": "vital_id",
            "flag_column": "F",
            "flag_value": "Y",
            "retry": 1,
        },
        db={"type": "unsupported_db"},
    )
    ok, code = run_postprocess(hospital, {"vital_id": "VID"})
    assert ok is False
    assert code == "POSTPROCESS_DB_UNSUPPORTED"


def test_postprocess_insert_values_missing_returns_false():
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        postprocess={
            "mode": "insert_log",
            "table": "T",
            "columns": ["col1"],
            "values": {},
            "sources": {},
            "retry": 1,
        },
        db={"type": "oracle"},
    )
    ok, code = run_postprocess(hospital, {"col1": None})
    assert ok is False
    assert code == "POSTPROCESS_VALUE_MISSING"


def test_postprocess_retry_exhaustion_returns_last_code():
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        postprocess={
            "mode": "update_flag",
            "table": "T",
            "key_column": "ID",
            "flag_column": "F",
            "flag_value": "Y",
            "retry": 2,
        },
        db={"type": "oracle"},
    )
    ok, code = run_postprocess(hospital, {"vital_id": "VID"})
    assert ok is False
    assert code == "POSTPROCESS_KEY_MISSING"
