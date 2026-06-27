from datetime import datetime

import httpx

from app.db.repositories import api_key_repo
from app.providers.adapter_base import ProviderAdapter
from app.providers.registry import registry
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.utils.logging import logger

BASE_URL = "https://api.cartesia.ai"

CARTESIA_LANGUAGES = [
    "en", "fr", "de", "es", "pt", "pt-BR", "zh", "ja", "hi", "it",
    "ko", "nl", "pl", "ru", "sv", "tr", "ar", "cs", "el", "fi",
    "hr", "ms", "sk", "da", "ta", "uk", "hu", "no", "vi", "bn",
    "th", "he", "ka", "id", "te", "gu", "kn", "ml", "mr", "pa",
]


class CartesiaProvider(ProviderAdapter):
    provider_id = "cartesia"

    def _get_client(self) -> httpx.Client | None:
        api_key = api_key_repo.get_decrypted("cartesia")
        if not api_key:
            return None
        return httpx.Client(
            base_url=BASE_URL,
            headers={
                "X-API-Key": api_key,
                "Cartesia-Version": "2024-11-13",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

    def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(provider_id=self.provider_id, model_id="sonic-3.5", name="Sonic 3.5", languages=CARTESIA_LANGUAGES, is_default=True),
            ModelInfo(provider_id=self.provider_id, model_id="sonic-3", name="Sonic 3", languages=CARTESIA_LANGUAGES),
            ModelInfo(provider_id=self.provider_id, model_id="sonic-2", name="Sonic 2", languages=CARTESIA_LANGUAGES),
            ModelInfo(provider_id=self.provider_id, model_id="sonic-latest", name="Sonic Latest", languages=CARTESIA_LANGUAGES),
        ]

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        client = self._get_client()
        if not client:
            return self._fallback_voices(language)
        try:
            with client:
                resp = client.get("/voices")
                resp.raise_for_status()
                data = resp.json()
                items = data if isinstance(data, list) else data.get("voices", data.get("data", []))
                if not items:
                    return self._fallback_voices(language)
                return [
                    VoiceInfo(
                        provider_id=self.provider_id,
                        voice_id=v.get("id", ""),
                        name=v.get("name", ""),
                        language=v.get("language") or language,
                    )
                    for v in items
                ]
        except Exception as e:
            logger.warning(f"Cartesia list_voices failed: {e}")
            return self._fallback_voices(language)

    def _fallback_voices(self, language: str | None) -> list[VoiceInfo]:
        return [
            VoiceInfo(provider_id=self.provider_id, voice_id="694f9389-aac1-45b6-b726-9d9369183238", name="Barbershop Man", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="aad81f96-3792-4d13-b105-188e6be3bf5c", name="Gentle Woman", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="bf0a246a-8642-498a-9950-80c35e9276b5", name="American Woman", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="00510a15-4216-4fdc-a0ab-05d74cd9f795", name="British Man", language=language),
        ]

    def get_quota(self) -> QuotaSnapshot:
        try:
            admin_key = api_key_repo.get_decrypted("cartesia", is_admin=True)
            if admin_key:
                with httpx.Client(
                    base_url=BASE_URL,
                    headers={"X-API-Key": admin_key, "Cartesia-Version": "2024-11-13"},
                    timeout=15,
                ) as client:
                    resp = client.get("/account")
                    resp.raise_for_status()
                    data = resp.json()
                    return QuotaSnapshot(
                        provider_id=self.provider_id,
                        unit="credits",
                        used=float(data.get("credits_used", 0)),
                        limit=float(data.get("credits_limit", 20000)),
                        remaining=float(max(0, data.get("credits_limit", 20000) - data.get("credits_used", 0))),
                        reset_policy="monthly_billing_cycle",
                        source="official_api",
                        confidence="high",
                        updated_at=datetime.utcnow(),
                    )
        except Exception as e:
            logger.warning(f"Cartesia quota API failed (admin key may be needed): {e}")
        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="credits",
            used=0, limit=20000, remaining=20000,
            reset_policy="monthly_billing_cycle",
            source="local_ledger",
            confidence="medium",
            updated_at=datetime.utcnow(),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        client = self._get_client()
        if not client:
            raise self._auth_error("Cartesia API key not configured")

        voice_id = request.voice_id or "694f9389-aac1-45b6-b726-9d9369183238"
        model_id = request.model_id or "sonic-3.5"

        output_container = request.output_format or "mp3"
        if output_container == "mp3":
            payload_format = {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000}
        elif output_container == "wav":
            payload_format = {"container": "wav", "encoding": "pcm_f32le", "sample_rate": 44100}
        else:
            payload_format = {"container": output_container, "sample_rate": 44100}

        payload = {
            "transcript": request.text,
            "model_id": model_id,
            "voice": {"mode": "id", "id": voice_id},
            "output_format": payload_format,
            "generation_config": {
                "speed": request.speed or 1.0,
                "emotion": "natural",
            },
        }

        if request.language:
            cartesia_lang = "pt" if request.language.startswith("pt") else request.language.split("-")[0]
            payload["language"] = cartesia_lang

        with client:
            resp = client.post("/tts/bytes", json=payload)
            if resp.status_code == 401:
                raise self._auth_error("Invalid Cartesia API key")
            if resp.status_code == 429:
                raise self._rate_limit_error("Cartesia rate limited")
            resp.raise_for_status()
            audio_data = resp.content

        from app.core.audio_storage import AudioStorage
        storage = AudioStorage()
        file_path = storage.save_audio(audio_data, format=output_container, metadata={
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
            output_format=output_container,
        )

    def supports_language(self, language: str | None) -> bool:
        if language is None:
            return True
        lang_base = language.split("-")[0] if "-" in language else language
        supported = {l.split("-")[0] for l in CARTESIA_LANGUAGES}
        return lang_base in supported

    def _auth_error(self, msg):
        from app.core.errors import AuthError
        return AuthError(msg)

    def _rate_limit_error(self, msg):
        from app.core.errors import RateLimitedError
        return RateLimitedError(msg)


registry.register(CartesiaProvider())
logger.info("Cartesia provider registered")
