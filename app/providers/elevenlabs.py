from datetime import datetime

import httpx

from app.db.repositories import api_key_repo
from app.providers.adapter_base import ProviderAdapter
from app.providers.registry import registry
from app.schemas.provider import ModelInfo, VoiceInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.utils.logging import logger

BASE_URL = "https://api.elevenlabs.io/v1"

LANGUAGE_MAP = {
    "pt-BR": "pt", "pt": "pt", "en": "en", "es": "es", "fr": "fr",
    "de": "de", "it": "it", "ja": "ja", "ko": "ko", "zh": "zh",
    "ar": "ar", "ru": "ru", "nl": "nl", "pl": "pl", "vi": "vi",
    "tr": "tr", "hi": "hi",
}

ELEVENLABS_LANGUAGES = list(LANGUAGE_MAP.keys())


class ElevenLabsProvider(ProviderAdapter):
    provider_id = "elevenlabs"

    def _get_client(self) -> httpx.Client | None:
        api_key = api_key_repo.get_decrypted("elevenlabs")
        if not api_key:
            return None
        return httpx.Client(
            base_url=BASE_URL,
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            timeout=30,
        )

    def list_models(self) -> list[ModelInfo]:
        client = self._get_client()
        if not client:
            return self._fallback_models()
        try:
            with client:
                resp = client.get("/models")
                resp.raise_for_status()
                models = resp.json()
                result = []
                for m in models:
                    if m.get("can_do_text_to_speech", False):
                        langs = m.get("languages", [])
                        lang_codes = [l.get("language_code", "") for l in langs] if langs else ELEVENLABS_LANGUAGES
                        result.append(ModelInfo(
                            provider_id=self.provider_id,
                            model_id=m["model_id"],
                            name=m.get("name"),
                            languages=lang_codes,
                            is_default=m["model_id"] == "eleven_multilingual_v2",
                        ))
                return result
        except Exception as e:
            logger.error(f"ElevenLabs list_models failed: {e}")
            return self._fallback_models()

    def _fallback_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(provider_id=self.provider_id, model_id="eleven_multilingual_v2", name="Eleven Multilingual v2", languages=ELEVENLABS_LANGUAGES, is_default=True),
            ModelInfo(provider_id=self.provider_id, model_id="eleven_flash_v2_5", name="Eleven Flash v2.5", languages=ELEVENLABS_LANGUAGES),
            ModelInfo(provider_id=self.provider_id, model_id="eleven_turbo_v2_5", name="Eleven Turbo v2.5", languages=["en"]),
        ]

    def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        client = self._get_client()
        if not client:
            return self._fallback_voices(language)
        try:
            params = {}
            if language:
                el_lang = LANGUAGE_MAP.get(language, language.split("-")[0] if "-" in language else language)
                params["language"] = el_lang
            with client:
                resp = client.get("/voices", params=params)
                resp.raise_for_status()
                data = resp.json()
                return [
                    VoiceInfo(
                        provider_id=self.provider_id,
                        voice_id=v["voice_id"],
                        name=v.get("name"),
                        language=language,
                        preview_url=v.get("preview_url") or None,
                        labels=v.get("labels", {}),
                    )
                    for v in data.get("voices", [])
                ]
        except Exception as e:
            logger.error(f"ElevenLabs list_voices failed: {e}")
            return self._fallback_voices(language)

    def _fallback_voices(self, language: str | None) -> list[VoiceInfo]:
        return [
            VoiceInfo(provider_id=self.provider_id, voice_id="21m00Tcm4TlvDq8ikWAM", name="Rachel", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="AZnzlk1XvdvUeBnXmlld", name="Domi", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="EXAVITQu4vrVxnDb2I", name="Bella", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="ErXwobaYiN019PkySv", name="Antoni", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="MF3mGyEYCl7XYWbV9V", name="Elli", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="TxGEqnHWrfWFTfGW9XjT", name="Josh", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="VR6AewLTigWG4xSOZn", name="Sonia", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="pNInz6obpgDQGcFmaJgB", name="Adam", language=language),
            VoiceInfo(provider_id=self.provider_id, voice_id="yoZ06aMxZJJ28mfd3POQ", name="Sam", language=language),
        ]

    def get_quota(self) -> QuotaSnapshot:
        client = self._get_client()
        if not client:
            return QuotaSnapshot(
                provider_id=self.provider_id, unit="characters",
                reset_policy="monthly_billing_cycle",
                source="unknown", confidence="low",
                updated_at=datetime.utcnow(),
            )
        try:
            with client:
                resp = client.get("/user/subscription")
                resp.raise_for_status()
                data = resp.json()
                used = float(data.get("character_count", 0))
                limit = float(data.get("character_limit", 0))
                return QuotaSnapshot(
                    provider_id=self.provider_id,
                    unit="characters",
                    used=used,
                    limit=limit,
                    remaining=max(0, limit - used),
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
        client = self._get_client()
        if not client:
            raise self._auth_error("ElevenLabs API key not configured")

        voice_id = request.voice_id or "21m00Tcm4TlvDq8ikWAM"
        model_id = request.model_id or "eleven_multilingual_v2"

        payload: dict = {
            "text": request.text,
            "model_id": model_id,
        }

        if request.language:
            el_lang = LANGUAGE_MAP.get(request.language)
            if el_lang:
                payload["language_code"] = el_lang

        default_settings = {
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.33,
            "use_speaker_boost": True,
        }

        if model_id in ("eleven_multilingual_v2", "eleven_v3", "eleven_flash_v2_5"):
            payload["voice_settings"] = default_settings

        output_format = request.output_format or "mp3"
        fmt_map = {"mp3": "mp3_44100_128", "wav": "pcm_44100", "ogg": "opus_48000_128", "pcm": "pcm_44100"}
        fmt = fmt_map.get(output_format, "mp3_44100_128")

        with client:
            resp = client.post(f"/text-to-speech/{voice_id}?output_format={fmt}", json=payload)
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
        file_path = storage.save_audio(audio_data, format=output_format, metadata={
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
            output_format=output_format,
        )

    def supports_language(self, language: str | None) -> bool:
        if language is None:
            return True
        lang = LANGUAGE_MAP.get(language, language)
        supported_codes = set(LANGUAGE_MAP.values())
        return lang in supported_codes or language.split("-")[0] in supported_codes

    def _auth_error(self, msg):
        from app.core.errors import AuthError
        return AuthError(msg)

    def _rate_limit_error(self, msg):
        from app.core.errors import RateLimitedError
        return RateLimitedError(msg)

    def _billing_error(self, msg):
        from app.core.errors import BillingRequiredError
        return BillingRequiredError(msg)


registry.register(ElevenLabsProvider())
