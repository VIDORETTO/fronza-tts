from datetime import datetime

import httpx

from app.core.audio_storage import AudioStorage
from app.db.repositories import api_key_repo
from app.providers.adapter_base import ProviderAdapter
from app.providers.registry import registry
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.utils.logging import logger

BASE_URL = "https://api.async-voice.com/v1"


class AsyncVoiceProvider(ProviderAdapter):
    provider_id = "async_voice"

    def _get_client(self) -> httpx.Client:
        api_key = api_key_repo.get_decrypted("async_voice")
        if not api_key:
            api_key = ""
        return httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

    def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(provider_id=self.provider_id, model_id="async_flash_v1.5", name="Async Flash 1.5", languages=["en", "pt-BR", "es", "fr", "de", "it", "ja"]),
            ModelInfo(provider_id=self.provider_id, model_id="async_pro_v1.0", name="Async Pro 1.0", languages=["en", "pt-BR", "es", "fr", "de", "it", "ja"]),
            ModelInfo(provider_id=self.provider_id, model_id="async_flash_v1.0", name="Async Flash 1.0", languages=["en", "pt-BR", "es", "fr", "de", "it", "ja"]),
        ]

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        return [
            VoiceInfo(provider_id=self.provider_id, voice_id="default-male", name="Default Male"),
            VoiceInfo(provider_id=self.provider_id, voice_id="default-female", name="Default Female"),
        ]

    def get_quota(self) -> QuotaSnapshot:
        manual = self._get_manual_balance()
        if manual:
            return QuotaSnapshot(
                provider_id=self.provider_id,
                unit="credits",
                used=0,
                limit=manual,
                remaining=manual,
                reset_policy="billing_cycle_or_topup",
                source="manual_config",
                confidence="low",
                updated_at=datetime.utcnow(),
            )

        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="credits",
            used=0,
            limit=0,
            remaining=0,
            reset_policy="billing_cycle_or_topup",
            source="manual_config",
            confidence="low",
            updated_at=datetime.utcnow(),
        )

    def _get_manual_balance(self) -> float | None:
        from app.db.repositories import quota_repo
        balance = quota_repo.get_manual_balance("async_voice")
        if balance:
            return balance.balance
        return None

    def synthesize(self, request: TTSRequest) -> TTSResult:
        api_key = self._get_client()

        voice_id = request.voice_id or "default-male"
        model_id = request.model_id or "async_flash_v1.5"

        payload = {
            "text": request.text,
            "voice": voice_id,
            "model": model_id,
            "format": request.output_format or "mp3",
        }

        with self._get_client() as client:
            resp = client.post("/tts", json=payload)
            if resp.status_code == 401:
                raise self._auth_error("Invalid Async Voice API key")
            if resp.status_code == 429:
                raise self._rate_limit_error("Async Voice rate limited")
            resp.raise_for_status()
            audio_data = resp.content

        storage = AudioStorage()
        file_path = storage.save_audio(audio_data, format=request.output_format or "mp3", metadata={
            "provider": self.provider_id,
            "model": model_id,
            "voice_id": voice_id,
            "language": request.language,
            "characters": len(request.text),
        })

        return TTSResult(
            provider_id=self.provider_id,
            model_id=model_id,
            voice_id=voice_id,
            language=request.language,
            audio_file_path=file_path,
            output_format=request.output_format or "mp3",
        )

    def _auth_error(self, msg):
        from app.core.errors import AuthError
        return AuthError(msg)

    def _rate_limit_error(self, msg):
        from app.core.errors import RateLimitedError
        return RateLimitedError(msg)

    def supports_language(self, language: str | None) -> bool:
        return True


registry.register(AsyncVoiceProvider())
logger.info("Async Voice provider registered")
