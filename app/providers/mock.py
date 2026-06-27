from datetime import datetime

from app.providers.adapter_base import ProviderAdapter
from app.providers.registry import registry
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult


class MockProviderSuccess(ProviderAdapter):
    provider_id: str

    def __init__(self, provider_id: str = "mock_success"):
        self.provider_id = provider_id

    def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(provider_id=self.provider_id, model_id="mock_model", languages=["pt-BR", "en"])]

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        return [VoiceInfo(provider_id=self.provider_id, voice_id="mock_voice", name="Mock Voice", language=language)]

    def get_quota(self) -> QuotaSnapshot:
        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="characters",
            used=100.0,
            limit=10000.0,
            remaining=9900.0,
            reset_policy="monthly_billing_cycle",
            source="local_ledger",
            confidence="high",
            updated_at=datetime.utcnow(),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        return TTSResult(
            provider_id=self.provider_id,
            model_id="mock_model",
            voice_id=request.voice_id or "mock_voice",
            language=request.language or "pt-BR",
            audio_file_path="mock_audio.mp3",
            output_format=request.output_format,
        )


class MockProviderQuotaExceeded(ProviderAdapter):
    provider_id: str

    def __init__(self, provider_id: str = "mock_quota_exceeded"):
        self.provider_id = provider_id

    def get_quota(self) -> QuotaSnapshot:
        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="characters",
            used=10000.0,
            limit=10000.0,
            remaining=0.0,
            reset_policy="monthly_billing_cycle",
            source="local_ledger",
            confidence="high",
            updated_at=datetime.utcnow(),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        from app.core.errors import QuotaExceededError
        raise QuotaExceededError("Quota exceeded")


class MockProviderRateLimited(ProviderAdapter):
    provider_id: str

    def __init__(self, provider_id: str = "mock_rate_limited"):
        self.provider_id = provider_id

    def get_quota(self) -> QuotaSnapshot:
        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="characters",
            used=500.0,
            limit=10000.0,
            remaining=9500.0,
            reset_policy="monthly_billing_cycle",
            source="local_ledger",
            confidence="high",
            updated_at=datetime.utcnow(),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        from app.core.errors import RateLimitedError
        raise RateLimitedError("Rate limited")


class MockProviderBillingRequired(ProviderAdapter):
    provider_id: str

    def __init__(self, provider_id: str = "mock_billing_required"):
        self.provider_id = provider_id

    def get_quota(self) -> QuotaSnapshot:
        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="characters",
            used=100.0,
            limit=10000.0,
            remaining=9900.0,
            reset_policy="pay_as_you_go",
            source="local_ledger",
            confidence="medium",
            updated_at=datetime.utcnow(),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        from app.core.errors import BillingRequiredError
        raise BillingRequiredError("Billing required")


class MockProviderTimeout(ProviderAdapter):
    provider_id: str

    def __init__(self, provider_id: str = "mock_timeout"):
        self.provider_id = provider_id

    def synthesize(self, request: TTSRequest) -> TTSResult:
        import time
        time.sleep(10)
        raise TimeoutError("Timed out")
