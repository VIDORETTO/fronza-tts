from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class GenerationRecord(BaseModel):
    id: str
    provider_id: str
    model_id: str | None = None
    voice_id: str | None = None
    language: str | None = None
    input_text: str
    input_characters: int
    output_file_path: str
    output_format: str
    duration_seconds: float | None = None
    status: str
    error_message: str | None = None
    fallback_from: str | None = None
    fallback_chain: list[str] = []
    created_at: datetime
