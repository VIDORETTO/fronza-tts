import base64
from datetime import datetime

import httpx

from app.db.repositories import api_key_repo
from app.providers.adapter_base import ProviderAdapter
from app.providers.registry import registry
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.utils.logging import logger

BASE_URL = "https://api.inworld.ai"

INWORLD_LANGUAGES = [
    "en", "en-US", "en-GB", "pt-BR", "pt", "es", "es-ES", "fr", "fr-FR",
    "de", "de-DE", "it", "it-IT", "ja", "ja-JP", "ko", "ko-KR",
    "zh", "zh-CN", "ru", "ar", "nl", "pl", "tr", "vi", "th",
]

INWORLD_VOICES = [
    VoiceInfo(provider_id="inworld", voice_id="Craig", name="Craig"),
    VoiceInfo(provider_id="inworld", voice_id="Dennis", name="Dennis"),
    VoiceInfo(provider_id="inworld", voice_id="Arlene", name="Arlene"),
    VoiceInfo(provider_id="inworld", voice_id="Maya", name="Maya"),
    VoiceInfo(provider_id="inworld", voice_id="Serena", name="Serena"),
    VoiceInfo(provider_id="inworld", voice_id="Ashley", name="Ashley"),
    VoiceInfo(provider_id="inworld", voice_id="Patrick", name="Patrick"),
    VoiceInfo(provider_id="inworld", voice_id="Michelle", name="Michelle"),
]

INWORLD_MODELS = [
    ModelInfo(provider_id="inworld", model_id="inworld-tts-2", name="TTS-2", languages=INWORLD_LANGUAGES, is_default=True),
    ModelInfo(provider_id="inworld", model_id="inworld-tts-1.5-max", name="TTS 1.5 Max", languages=INWORLD_LANGUAGES),
    ModelInfo(provider_id="inworld", model_id="inworld-tts-1.5-mini", name="TTS 1.5 Mini", languages=INWORLD_LANGUAGES),
]


class InworldProvider(ProviderAdapter):
    provider_id = "inworld"

    def _get_api_key(self) -> str:
        return api_key_repo.get_decrypted("inworld") or ""

    def list_models(self) -> list[ModelInfo]:
        return INWORLD_MODELS

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        return [v.model_copy(update={"language": language}) for v in INWORLD_VOICES]

    def get_quota(self) -> QuotaSnapshot:
        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="minutes",
            used=0, limit=60, remaining=60,
            reset_policy="monthly_or_on_demand",
            source="portal_manual",
            confidence="medium",
            updated_at=datetime.utcnow(),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        api_key = self._get_api_key()
        if not api_key:
            raise self._auth_error("Inworld API key not configured")

        voice_id = request.voice_id or "Maya"
        model_id = request.model_id or "inworld-tts-2"

        payload = {
            "text": request.text,
            "voiceId": voice_id,
            "modelId": model_id,
            "audioConfig": {
                "audioEncoding": "MP3",
                "sampleRateHertz": 48000,
            },
        }

        if model_id == "inworld-tts-2":
            payload["deliveryMode"] = "CREATIVE"

        if request.language:
            payload["language"] = request.language

        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{BASE_URL}/v1/tts/synthesize-speech",
                json=payload,
                auth=(api_key, ""),
            )
            if resp.status_code in (401, 403):
                raise self._auth_error(f"Inworld auth error: {resp.text}")
            if resp.status_code == 429:
                raise self._rate_limit_error("Inworld rate limited")
            resp.raise_for_status()
            data = resp.json()

            audio_b64 = data.get("audioContent")
            if not audio_b64:
                raise self._generation_error("No audio content in Inworld response")
            audio_data = base64.b64decode(audio_b64)

        from app.core.audio_storage import AudioStorage
        storage = AudioStorage()
        file_path = storage.save_audio(audio_data, format="mp3", metadata={
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
            output_format="mp3",
        )

    def supports_language(self, language: str | None) -> bool:
        if language is None:
            return True
        supported = {"en", "pt", "es", "fr", "de", "it", "ja", "ko", "zh", "ru", "ar", "nl", "pl", "tr", "vi", "th"}
        lang_base = language.split("-")[0]
        return lang_base in supported

    def _auth_error(self, msg):
        from app.core.errors import AuthError
        return AuthError(msg)

    def _rate_limit_error(self, msg):
        from app.core.errors import RateLimitedError
        return RateLimitedError(msg)

    def _generation_error(self, msg):
        from app.core.errors import AudioGenerationError
        return AudioGenerationError(msg)


registry.register(InworldProvider())
logger.info("Inworld provider registered")
