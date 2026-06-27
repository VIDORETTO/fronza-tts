from typing import Protocol

from app.schemas.errors import ProviderError
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.schemas.usage import UsageEstimate


class TTSProvider(Protocol):
    provider_id: str

    def list_models(self) -> list[ModelInfo]:
        ...

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        ...

    def estimate_usage(self, request: TTSRequest) -> UsageEstimate:
        ...

    def get_quota(self) -> QuotaSnapshot:
        ...

    def synthesize(self, request: TTSRequest) -> TTSResult:
        ...

    def normalize_error(self, error: Exception) -> ProviderError:
        ...

    def supports_language(self, language: str | None) -> bool:
        ...

    def supports_output_format(self, output_format: str) -> bool:
        ...
