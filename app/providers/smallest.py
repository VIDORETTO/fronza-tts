from datetime import datetime

import httpx

from app.db.repositories import api_key_repo
from app.providers.adapter_base import ProviderAdapter
from app.providers.registry import registry
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.utils.logging import logger

BASE_URL = "https://waves-api.smallest.ai/api/v1"

SMALLEST_LANGUAGES = ["en", "hi", "mr", "kn", "ta", "te", "gu", "bn", "ml"]

SMALLEST_MODELS = [
    ModelInfo(provider_id="smallest", model_id="lightning", name="Lightning", languages=SMALLEST_LANGUAGES, is_default=True),
    ModelInfo(provider_id="smallest", model_id="lightning-large", name="Lightning Large", languages=SMALLEST_LANGUAGES),
    ModelInfo(provider_id="smallest", model_id="lightning-v2", name="Lightning V2", languages=SMALLEST_LANGUAGES),
]

FALLBACK_VOICES = [
    VoiceInfo(provider_id="smallest", voice_id="emily", name="Emily"),
    VoiceInfo(provider_id="smallest", voice_id="lakshya", name="Lakshya"),
    VoiceInfo(provider_id="smallest", voice_id="nyah", name="Nyah"),
    VoiceInfo(provider_id="smallest", voice_id="aravind", name="Aravind"),
    VoiceInfo(provider_id="smallest", voice_id="ramya", name="Ramya"),
]


class SmallestProvider(ProviderAdapter):
    provider_id = "smallest"

    def _get_client(self) -> httpx.Client | None:
        api_key = api_key_repo.get_decrypted("smallest")
        if not api_key:
            return None
        return httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=30,
        )

    def list_models(self) -> list[ModelInfo]:
        client = self._get_client()
        if not client:
            return SMALLEST_MODELS
        try:
            with client:
                resp = client.get("/models")
                resp.raise_for_status()
                data = resp.json()
                models = data if isinstance(data, list) else data.get("models", [])
                if models:
                    return [ModelInfo(
                        provider_id=self.provider_id,
                        model_id=m.get("model_id", m.get("name", "")),
                        name=m.get("name", m.get("model_id", "")),
                        languages=m.get("languages", SMALLEST_LANGUAGES),
                    ) for m in models]
        except Exception as e:
            logger.warning(f"Smallest list_models via API failed: {e}")
        return SMALLEST_MODELS

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        client = self._get_client()
        if not client:
            return FALLBACK_VOICES
        try:
            with client:
                resp = client.get("/voices")
                resp.raise_for_status()
                data = resp.json()
                items = data if isinstance(data, list) else data.get("voices", [])
                if items:
                    return [VoiceInfo(
                        provider_id=self.provider_id,
                        voice_id=v.get("voiceId", v.get("name", "")),
                        name=v.get("name", v.get("voiceId", "")),
                        language=v.get("language", language),
                    ) for v in items]
        except Exception as e:
            logger.warning(f"Smallest list_voices via API failed: {e}")
        return FALLBACK_VOICES

    def get_quota(self) -> QuotaSnapshot:
        manual = self._get_manual_balance()
        if manual:
            return QuotaSnapshot(
                provider_id=self.provider_id,
                unit="characters",
                used=0,
                limit=manual,
                remaining=manual,
                reset_policy="one_time_trial_credit",
                source="manual_config",
                confidence="medium",
                updated_at=datetime.utcnow(),
            )
        client = self._get_client()
        if not client:
            fallback = QuotaSnapshot(
                provider_id=self.provider_id,
                unit="characters", used=0, limit=0, remaining=0,
                reset_policy="one_time_trial_credit",
                source="manual_config",
                confidence="low",
                updated_at=datetime.utcnow(),
            )
            return fallback
        try:
            with client:
                resp = client.get("/account/usage")
                resp.raise_for_status()
                data = resp.json()
                used = float(data.get("characters_used", 0))
                limit = float(data.get("characters_limit", 50000))
                return QuotaSnapshot(
                    provider_id=self.provider_id,
                    unit="characters",
                    used=used, limit=limit, remaining=max(0, limit - used),
                    reset_policy="one_time_trial_credit",
                    source="official_api",
                    confidence="medium",
                    updated_at=datetime.utcnow(),
                )
        except Exception as e:
            logger.warning(f"Smallest quota check failed: {e}")
            return QuotaSnapshot(
                provider_id=self.provider_id,
                unit="characters", used=0, limit=0, remaining=0,
                reset_policy="one_time_trial_credit",
                source="manual_config",
                confidence="low",
                updated_at=datetime.utcnow(),
            )

    def _get_manual_balance(self) -> float | None:
        from app.db.repositories import quota_repo
        balance = quota_repo.get_manual_balance("smallest")
        return balance.balance if balance else None

    def synthesize(self, request: TTSRequest) -> TTSResult:
        client = self._get_client()
        if not client:
            raise self._auth_error("Smallest API key not configured")

        voice_id = request.voice_id or "emily"
        model_id = request.model_id or "lightning-large"

        payload = {
            "text": request.text,
            "voice_id": voice_id,
            "model": model_id,
            "sample_rate": 24000,
            "speed": request.speed or 1.0,
            "output_format": request.output_format or "mp3",
        }

        if model_id == "lightning-large":
            payload["enhancement"] = 1
            payload["consistency"] = 0.5
            payload["similarity"] = 0.0

        if request.language:
            payload["language"] = request.language.split("-")[0]

        with client:
            resp = client.post("/lightning/tts", json=payload)
            if resp.status_code == 401:
                raise self._auth_error("Invalid Smallest API key")
            if resp.status_code == 429:
                raise self._rate_limit_error("Smallest rate limited")
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

    def supports_language(self, language: str | None) -> bool:
        if language is None:
            return True
        lang = language.split("-")[0]
        supported = {l.split("-")[0] for l in SMALLEST_LANGUAGES}
        return lang in supported

    def _auth_error(self, msg):
        from app.core.errors import AuthError
        return AuthError(msg)

    def _rate_limit_error(self, msg):
        from app.core.errors import RateLimitedError
        return RateLimitedError(msg)


registry.register(SmallestProvider())
logger.info("Smallest provider registered")
