from datetime import datetime

import httpx

from app.core.config import config
from app.db.repositories import api_key_repo
from app.providers.adapter_base import ProviderAdapter
from app.providers.registry import registry
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.utils.logging import logger

BASE_URL = "https://api.elevenlabs.io/v1"


class ElevenLabsProvider(ProviderAdapter):
    provider_id = "elevenlabs"

    def _get_client(self) -> httpx.Client:
        api_key = api_key_repo.get_decrypted("elevenlabs")
        if not api_key:
            api_key = ""
        return httpx.Client(base_url=BASE_URL, headers={"xi-api-key": api_key, "Content-Type": "application/json"}, timeout=30)

    def list_models(self) -> list[ModelInfo]:
        try:
            with self._get_client() as client:
                resp = client.get("/models")
                resp.raise_for_status()
                models = resp.json()
                return [
                    ModelInfo(provider_id=self.provider_id, model_id=m["model_id"], name=m.get("name"))
                    for m in models
                ]
        except Exception as e:
            logger.error(f"ElevenLabs list_models failed: {e}")
            return []

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        try:
            with self._get_client() as client:
                resp = client.get("/voices")
                resp.raise_for_status()
                data = resp.json()
                return [
                    VoiceInfo(provider_id=self.provider_id, voice_id=v["voice_id"], name=v.get("name"))
                    for v in data.get("voices", [])
                ]
        except Exception as e:
            logger.error(f"ElevenLabs list_voices failed: {e}")
            return []

    def get_quota(self) -> QuotaSnapshot:
        try:
            with self._get_client() as client:
                resp = client.get("/user/subscription")
                resp.raise_for_status()
                data = resp.json()
                used = data.get("character_count", 0)
                limit = data.get("character_limit", 0)
                return QuotaSnapshot(
                    provider_id=self.provider_id,
                    unit="characters",
                    used=float(used),
                    limit=float(limit),
                    remaining=float(max(0, limit - used)),
                    reset_policy="monthly_billing_cycle",
                    source="official_api",
                    confidence="high",
                    updated_at=datetime.utcnow(),
                )
        except Exception as e:
            logger.error(f"ElevenLabs get_quota failed: {e}")
            return QuotaSnapshot(
                provider_id=self.provider_id,
                unit="characters",
                reset_policy="monthly_billing_cycle",
                source="unknown",
                confidence="low",
                updated_at=datetime.utcnow(),
            )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        from uuid import uuid4

        voice_id = request.voice_id or "21m00Tcm4TlvDq8ikWAM"
        model_id = request.model_id or "eleven_multilingual_v2"

        payload = {
            "text": request.text,
            "model_id": model_id,
            "output_format": request.output_format or "mp3_44100",
        }

        with self._get_client() as client:
            resp = client.post(f"/text-to-speech/{voice_id}", json=payload)
            if resp.status_code == 401:
                raise self._auth_error("Invalid API key")
            if resp.status_code == 429:
                raise self._rate_limit_error("Rate limited")
            if resp.status_code == 402:
                raise self._billing_error("Billing required")
            resp.raise_for_status()

            audio_data = resp.content

        from app.core.audio_storage import AudioStorage
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

    def _billing_error(self, msg):
        from app.core.errors import BillingRequiredError
        return BillingRequiredError(msg)

    def supports_language(self, language: str | None) -> bool:
        supported = {"pt-BR", "en", "es", "fr", "de", "it", "ja", "ko", "zh", "ar", "ru"}
        if language is None:
            return True
        return language in supported


registry.register(ElevenLabsProvider())
