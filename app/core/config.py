from functools import lru_cache
from typing import Literal

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경 변수에서 애플리케이션 설정을 로드"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: Literal["local", "dev", "prod"] = "local"
    version: str = "0.1.0"
    log_level: str = "INFO"
    admin_id: str = "admin"
    admin_password: str = "admin"
    backend_base_url: str = "http://localhost:9000"
    backend_api_key: str = ""
    config_path: str = "hospitals.yaml"
    duckdb_path: str = "data/telemetry.duckdb"
    scheduler_enabled: bool = True


class HospitalConfig(BaseModel):
    """병원 설정 항목을 정의"""

    hospital_id: str
    connector_type: str
    enabled: bool = True
    schedule_minutes: int = 5
    transform_profile: str
    postprocess: dict | None = None
    db: dict | None = None
    api: dict | None = None


class AppConfig(BaseModel):
    """단일 병원 설정 래퍼"""

    hospital: HospitalConfig


@lru_cache
def get_settings() -> Settings:
    """캐시된 설정 인스턴스를 반환"""
    return Settings()


@lru_cache
def load_app_config() -> AppConfig:
    """설정 파일(YAML)에서 병원 설정 로드

    Returns:
        병원 설정 인스턴스
    """
    settings = get_settings()
    with open(settings.config_path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return AppConfig(**data)


def reload_app_config() -> AppConfig:
    """설정 캐시를 초기화하고 다시 로드

    Returns:
        병원 설정 인스턴스
    """
    load_app_config.cache_clear()
    return load_app_config()
