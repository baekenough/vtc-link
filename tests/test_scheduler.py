from app.core.config import AppConfig, HospitalConfig
from app.core.scheduler import start_scheduler


def test_scheduler_start_without_pull_connector():
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="push_rest_api",
        transform_profile="H1",
        enabled=True,
    )
    config = AppConfig(hospital=hospital)
    scheduler = start_scheduler(config)
    assert scheduler is not None
    scheduler.shutdown(wait=False)


def test_scheduler_restart_with_pull_connector():
    """pull 커넥터 스케줄러 시작 및 재시작 테스트"""
    hospital = HospitalConfig(
        hospital_id="H1",
        connector_type="pull_db_view",
        transform_profile="H1",
        enabled=True,
        schedule_minutes=1,
    )
    config = AppConfig(hospital=hospital)
    scheduler = start_scheduler(config)
    assert scheduler is not None
    scheduler.shutdown(wait=False)

    hospital_b = HospitalConfig(
        hospital_id="H2",
        connector_type="pull_rest_api",
        transform_profile="H2",
        enabled=True,
        schedule_minutes=2,
    )
    config_b = AppConfig(hospital=hospital_b)
    scheduler_b = start_scheduler(config_b)
    assert scheduler_b is not None
    scheduler_b.shutdown(wait=False)
