from app.providers.base import TTSProvider
from app.core.errors import (
    AudioGenerationError,
    AuthError,
    BillingRequiredError,
    ProviderUnavailableError,
    QuotaExceededError,
    RateLimitedError,
    UnknownProviderError,
    UnsupportedLanguageError,
    UnsupportedVoiceError,
)
from app.schemas.errors import ProviderError
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.schemas.usage import UsageEstimate


class ProviderAdapter:
    provider_id: str = "base"

    def list_models(self) -> list[ModelInfo]:
        return []

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        return []

    def estimate_usage(self, request: TTSRequest) -> UsageEstimate:
        return UsageEstimate(
            provider_id=self.provider_id,
            unit="characters",
            estimated_amount=float(len(request.text)),
            confidence="medium",
        )

    def get_quota(self) -> QuotaSnapshot:
        raise NotImplementedError

    def synthesize(self, request: TTSRequest) -> TTSResult:
        raise NotImplementedError

    def normalize_error(self, error: Exception) -> ProviderError:
        return ProviderError(
            provider_id=self.provider_id,
            error_type="unknown",
            retryable=False,
            fallback_allowed=False,
            message=str(error),
        )

    def supports_language(self, language: str | None) -> bool:
        return True

    def supports_output_format(self, output_format: str) -> bool:
        return output_format in ("mp3", "wav", "ogg", "pcm")
