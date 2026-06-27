import base64
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

BASE_URL = "https://generativelanguage.googleapis.com"


class GeminiProvider(ProviderAdapter):
    provider_id = "gemini"

    def _get_api_key(self) -> str:
        return api_key_repo.get_decrypted("gemini") or ""

    def list_models(self) -> list[ModelInfo]:
        api_key = self._get_api_key()
        if not api_key:
            return [
                ModelInfo(provider_id=self.provider_id, model_id="gemini-3.1-flash-tts-preview", name="Gemini 3.1 Flash TTS Preview"),
            ]
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"{BASE_URL}/v1beta/models",
                    params={"key": api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    name = m.get("name", "")
                    if "tts" in name.lower():
                        model_id = name.split("/")[-1]
                        models.append(
                            ModelInfo(
                                provider_id=self.provider_id,
                                model_id=model_id,
                                name=m.get("displayName", model_id),
                            )
                        )
                return models or [
                    ModelInfo(provider_id=self.provider_id, model_id="gemini-3.1-flash-tts-preview", name="Gemini 3.1 Flash TTS Preview"),
                ]
        except Exception as e:
            logger.warning(f"Gemini list_models failed: {e}")
            return [
                ModelInfo(provider_id=self.provider_id, model_id="gemini-3.1-flash-tts-preview", name="Gemini 3.1 Flash TTS Preview"),
            ]

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        return [
            VoiceInfo(provider_id=self.provider_id, voice_id="Kore", name="Kore"),
            VoiceInfo(provider_id=self.provider_id, voice_id="Puck", name="Puck"),
            VoiceInfo(provider_id=self.provider_id, voice_id="Charon", name="Charon"),
            VoiceInfo(provider_id=self.provider_id, voice_id="Aoede", name="Aoede"),
            VoiceInfo(provider_id=self.provider_id, voice_id="Fenrir", name="Fenrir"),
        ]

    def get_quota(self) -> QuotaSnapshot:
        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="requests",
            used=0,
            limit=1500,
            remaining=1500,
            reset_policy="daily_rate_limit",
            source="response_metadata",
            confidence="medium",
            updated_at=datetime.utcnow(),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        api_key = self._get_api_key()
        if not api_key:
            raise self._auth_error("Gemini API key not configured")

        model_id = request.model_id or "gemini-3.1-flash-tts-preview"
        voice_id = request.voice_id or "Kore"

        payload = {
            "model": model_id,
            "input": request.text,
            "response_format": {"type": "audio"},
            "generation_config": {
                "speech_config": [{"voice": voice_id}]
            },
            "stream": False,
        }

        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{BASE_URL}/v1beta/interactions",
                params={"key": api_key},
                json=payload,
            )
            if resp.status_code == 401 or resp.status_code == 403:
                raise self._auth_error(f"Gemini auth error: {resp.text}")
            if resp.status_code == 429:
                raise self._rate_limit_error("Gemini rate limited")
            resp.raise_for_status()
            data = resp.json()

            audio_b64 = data.get("output_audio", {}).get("data")
            if not audio_b64:
                raise self._generation_error("No audio data in Gemini response")

            audio_data = base64.b64decode(audio_b64)

        storage = AudioStorage()
        file_path = storage.save_audio(audio_data, format="wav", metadata={
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
            output_format="wav",
        )

    def _auth_error(self, msg):
        from app.core.errors import AuthError
        return AuthError(msg)

    def _rate_limit_error(self, msg):
        from app.core.errors import RateLimitedError
        return RateLimitedError(msg)

    def _generation_error(self, msg):
        from app.core.errors import AudioGenerationError
        return AudioGenerationError(msg)

    def supports_language(self, language: str | None) -> bool:
        return True


registry.register(GeminiProvider())
logger.info("Gemini provider registered")
