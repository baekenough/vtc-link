from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import AppConfig
from app.core.pipeline import run_pull_pipeline

_scheduler: BackgroundScheduler | None = None


def start_scheduler(config: AppConfig) -> BackgroundScheduler:
    """풀 커넥터용 백그라운드 스케줄러를 시작

    Args:
        config: 병원 설정 객체

    Returns:
        BackgroundScheduler 인스턴스
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    scheduler = BackgroundScheduler()
    hospital = config.hospital
    if hospital.enabled and hospital.connector_type in {
        "pull_db_view",
        "pull_rest_api",
    }:
        scheduler.add_job(
            run_pull_pipeline,
            "interval",
            minutes=hospital.schedule_minutes,
            args=[hospital],
            id=f"pull-{hospital.hospital_id}",
            replace_existing=True,
        )
    scheduler.start()
    _scheduler = scheduler
    return scheduler
