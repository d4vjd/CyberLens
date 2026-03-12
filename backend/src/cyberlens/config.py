# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "CyberLens SIEM"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_prefix: str = "/api/v1"
    debug: bool = True

    mysql_user: str = "cyberlens"
    mysql_password: str = "cyberlens"
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_database: str = "cyberlens"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_event_stream: str = "cyberlens:events"
    redis_alert_stream: str = "cyberlens:alerts"

    syslog_enabled: bool = False
    syslog_bind_host: str = "0.0.0.0"
    syslog_bind_port: int = 514
    rules_path: str = "../rules"
    playbooks_path: str = "../playbooks"
    mitre_bundle_path: str = "src/cyberlens/mitre/data/enterprise-attack.json"
    evidence_dir: str = "/tmp/cyberlens-evidence"
    detection_consumer_group: str = "detection-engine"
    detection_consumer_name: str = "backend-1"
    detection_poll_ms: int = 1000
    websocket_consumer_group: str = "ws-bridge"
    websocket_consumer_name: str = "backend-ws"
    startup_tasks_enabled: bool = True
    demo_default_intensity: int = 5
    demo_seed_event_count: int = 180

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost",
            "http://localhost:5173",
            "http://localhost:4173",
        ]
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def resolved_rules_path(self) -> Path:
        path = Path(self.rules_path)
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()

    @property
    def resolved_mitre_bundle_path(self) -> Path:
        path = Path(self.mitre_bundle_path)
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()

    @property
    def resolved_playbooks_path(self) -> Path:
        path = Path(self.playbooks_path)
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()

    @property
    def resolved_evidence_dir(self) -> Path:
        return Path(self.evidence_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()