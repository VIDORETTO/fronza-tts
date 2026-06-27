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

BASE_URL = "https://waves-api.smallest.ai/api/v1"


class SmallestProvider(ProviderAdapter):
    provider_id = "smallest"

    def _get_client(self) -> httpx.Client:
        api_key = api_key_repo.get_decrypted("smallest")
        if not api_key:
            api_key = ""
        return httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

    def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(provider_id=self.provider_id, model_id="lightning", name="Lightning", languages=["en", "hi", "mr", "kn", "ta", "te"]),
            ModelInfo(provider_id=self.provider_id, model_id="lightning-large", name="Lightning Large", languages=["en", "hi", "mr", "kn", "ta", "te"]),
            ModelInfo(provider_id=self.provider_id, model_id="lightning-v2", name="Lightning V2", languages=["en", "hi", "mr", "kn", "ta", "te"]),
        ]

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        try:
            with self._get_client() as client:
                resp = client.get("/lightning/voices")
                resp.raise_for_status()
                data = resp.json()
                return [
                    VoiceInfo(
                        provider_id=self.provider_id,
                        voice_id=v.get("voiceId") or v.get("name", ""),
                        name=v.get("name", v.get("voiceId")),
                        language=language,
                    )
                    for v in (data if isinstance(data, list) else data.get("voices", []))
                ]
        except Exception as e:
            logger.warning(f"Smallest list_voices failed: {e}")
            return [
                VoiceInfo(provider_id=self.provider_id, voice_id="emily", name="Emily"),
                VoiceInfo(provider_id=self.provider_id, voice_id="lakshya", name="Lakshya"),
                VoiceInfo(provider_id=self.provider_id, voice_id="nyah", name="Nyah"),
            ]

    def get_quota(self) -> QuotaSnapshot:
        manual = self._get_manual_balance()
        if manual:
            return QuotaSnapshot(
                provider_id=self.provider_id,
                unit="characters",
                used=manual.get("used", 0),
                limit=manual.get("balance", 50000),
                remaining=max(0, manual.get("balance", 50000) - manual.get("used", 0)),
                reset_policy="one_time_trial_credit",
                source="manual_config",
                confidence="medium",
                updated_at=datetime.utcnow(),
            )
        try:
            with self._get_client() as client:
                resp = client.get("/account/usage")
                resp.raise_for_status()
                data = resp.json()
                used = float(data.get("characters_used", 0))
                limit = float(data.get("characters_limit", 50000))
                return QuotaSnapshot(
                    provider_id=self.provider_id,
                    unit="characters",
                    used=used,
                    limit=limit,
                    remaining=max(0, limit - used),
                    reset_policy="one_time_trial_credit",
                    source="official_api",
                    confidence="medium",
                    updated_at=datetime.utcnow(),
                )
        except Exception as e:
            logger.warning(f"Smallest quota check failed: {e}")
            return QuotaSnapshot(
                provider_id=self.provider_id,
                unit="characters",
                used=0,
                limit=0,
                remaining=0,
                reset_policy="one_time_trial_credit",
                source="manual_config",
                confidence="low",
                updated_at=datetime.utcnow(),
            )

    def _get_manual_balance(self) -> dict | None:
        from app.db.repositories import quota_repo
        balance = quota_repo.get_manual_balance("smallest")
        if balance:
            return {"balance": balance.balance, "used": 0}
        return None

    def synthesize(self, request: TTSRequest) -> TTSResult:
        voice_id = request.voice_id or "emily"
        model_id = request.model_id or "lightning"

        payload = {
            "text": request.text,
            "model": model_id,
            "voice_id": voice_id,
            "sample_rate": 24000,
            "speed": request.speed or 1.0,
            "output_format": request.output_format or "wav",
        }

        with self._get_client() as client:
            resp = client.post("/lightning/tts", json=payload)
            if resp.status_code == 401:
                raise self._auth_error("Invalid Smallest API key")
            if resp.status_code == 429:
                raise self._rate_limit_error("Smallest rate limited")
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
        supported = {"en", "hi", "mr", "kn", "ta", "te", "gu", "bn"}
        if language is None:
            return True
        lang = language.split("-")[0] if "-" in language else language
        return lang in supported


registry.register(SmallestProvider())
logger.info("Smallest provider registered")
