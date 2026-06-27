from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class QuotaPolicyConfig(BaseModel):
    warning_threshold_percent: int = 80
    fallback_threshold_percent: int = 90
    hard_stop_threshold_percent: int = 97
    block_uncertain_quota_for_long_text: bool = True
    allow_paid_overage: bool = False
    require_confirmation_for_uncertain_quota: bool = True


class FallbackConfig(BaseModel):
    retry_attempts: int = 2
    timeout_seconds: int = 45
    backoff_seconds: int = 2
    fallback_on: list[str] = [
        "quota_exceeded",
        "rate_limited",
        "timeout",
        "server_error",
        "unsupported_language",
        "unsupported_voice",
        "billing_required",
    ]


class ProviderConfig(BaseModel):
    enabled: bool = True
    priority: int = 99
    reset_policy: str = "unknown"
    quota_source: str = "unknown"
    free_only: bool = True
    require_manual_balance: bool = False
    models: list[str] = []


class AppConfig(BaseModel):
    name: str = "TTS Fallback App"
    free_only_mode: bool = True
    default_language: str = "pt-BR"
    default_output_format: str = "mp3"
    audio_output_dir: str = "data/audio"
    max_text_chars_warning: int = 3000
    max_text_chars_when_quota_unknown: int = 500


class Config(BaseModel):
    app: AppConfig = AppConfig()
    quota_policy: QuotaPolicyConfig = QuotaPolicyConfig()
    fallback: FallbackConfig = FallbackConfig()
    chunk_limits: dict[str, int] = {}
    providers: dict[str, ProviderConfig] = {}

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        if path is None:
            path = Path("config.yaml")
        if not Path(path).exists():
            path = Path("config.example.yaml")
        if Path(path).exists():
            raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
            return cls.model_validate(raw)
        return cls()


config: Config = Config.load()
