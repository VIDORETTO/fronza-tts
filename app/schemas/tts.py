import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str
    language: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    voice_id: str | None = None
    output_format: str = "mp3"
    speed: float | None = None
    emotion: str | None = None
    style: str | None = None
    stream: bool = False
    timestamps: bool = False
    force_provider: bool = False
    free_only: bool = True


class UsageRecord(BaseModel):
    unit: str
    amount: float
    estimated: bool = True


class TTSResult(BaseModel):
    generation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    model_id: str | None = None
    voice_id: str | None = None
    language: str | None = None
    audio_file_path: str
    output_format: str = "mp3"
    duration_seconds: float | None = None
    usage: UsageRecord | None = None
    fallback_chain: list[str] = []
    warnings: list[str] = []
    raw_response: dict | None = None
