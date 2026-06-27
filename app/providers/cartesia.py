from datetime import datetime
from uuid import uuid4

import httpx

from app.core.audio_storage import AudioStorage
from app.db.repositories import api_key_repo
from app.providers.adapter_base import ProviderAdapter
from app.providers.registry import registry
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.utils.logging import logger

BASE_URL = "https://api.cartesia.ai"


class CartesiaProvider(ProviderAdapter):
    provider_id = "cartesia"

    def _get_client(self) -> httpx.Client:
        api_key = api_key_repo.get_decrypted("cartesia")
        if not api_key:
            api_key = ""
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
            ModelInfo(provider_id=self.provider_id, model_id="sonic-2", name="Sonic 2", languages=["en", "pt-BR", "es", "fr", "de", "it", "ja", "ko", "zh"]),
            ModelInfo(provider_id=self.provider_id, model_id="sonic-3.5", name="Sonic 3.5", languages=["en", "pt-BR", "es", "fr", "de", "it", "ja"]),
        ]

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        try:
            with self._get_client() as client:
                resp = client.get("/voices")
                resp.raise_for_status()
                data = resp.json()
                voices = []
                for v in data.get("voices", []):
                    voices.append(
                        VoiceInfo(
                            provider_id=self.provider_id,
                            voice_id=v["id"],
                            name=v.get("name"),
                            language=v.get("language"),
                        )
                    )
                return voices
        except Exception as e:
            logger.error(f"Cartesia list_voices failed: {e}")
            return [
                VoiceInfo(provider_id=self.provider_id, voice_id="694f9389-aac1-45b6-b726-9d9369183238", name="Barbershop Man"),
                VoiceInfo(provider_id=self.provider_id, voice_id="aad81f96-3792-4d13-b105-188e6be3bf5c", name="Gentle Woman"),
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
            logger.warning(f"Cartesia quota API failed (admin key may be missing): {e}")

        return QuotaSnapshot(
            provider_id=self.provider_id,
            unit="credits",
            used=0,
            limit=20000,
            remaining=20000,
            reset_policy="monthly_billing_cycle",
            source="local_ledger",
            confidence="medium",
            updated_at=datetime.utcnow(),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        voice_id = request.voice_id or "694f9389-aac1-45b6-b726-9d9369183238"
        model_id = request.model_id or "sonic-2"

        output_format = {
            "container": request.output_format or "wav",
            "encoding": "pcm_f32le",
            "sample_rate": 44100,
        }

        payload = {
            "transcript": request.text,
            "model_id": model_id,
            "voice": {"mode": "id", "id": voice_id},
            "output_format": output_format,
        }

        with self._get_client() as client:
            resp = client.post("/tts/bytes", json=payload)
            if resp.status_code == 401:
                raise self._auth_error("Invalid Cartesia API key")
            if resp.status_code == 429:
                raise self._rate_limit_error("Cartesia rate limited")
            resp.raise_for_status()
            audio_data = resp.content

        storage = AudioStorage()
        file_path = storage.save_audio(audio_data, format=request.output_format or "wav", metadata={
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
            output_format=request.output_format or "wav",
        )

    def _auth_error(self, msg):
        from app.core.errors import AuthError
        return AuthError(msg)

    def _rate_limit_error(self, msg):
        from app.core.errors import RateLimitedError
        return RateLimitedError(msg)

    def supports_language(self, language: str | None) -> bool:
        supported = {"pt-BR", "en", "es", "fr", "de", "it", "ja"}
        if language is None:
            return True
        return language in supported


registry.register(CartesiaProvider())
logger.info("Cartesia provider registered")
