from datetime import datetime
from typing import Any

from app.core.config import config
from app.core.errors import (
    AuthError, BillingRequiredError, ProviderUnavailableError,
    QuotaExceededError, RateLimitedError, UnknownProviderError,
    UnsupportedLanguageError, UnsupportedVoiceError,
)
from app.db.models import FallbackEvent, Generation, Provider, UsageLedger
from app.db.repositories import (
    api_key_repo, fallback_repo, generation_repo, provider_repo, quota_repo, usage_repo,
)
from app.providers.registry import registry
from app.schemas.provider import ProviderInfo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.schemas.usage import UsageEstimate
from app.utils.hashing import hash_text
from app.utils.logging import logger

from .quota_manager import QuotaManager


class FallbackEngine:
    ERROR_SCORES = {
        BillingRequiredError: -200,
        AuthError: -100,
        QuotaExceededError: -80,
        RateLimitedError: -50,
        ProviderUnavailableError: -40,
        UnsupportedLanguageError: -30,
        UnsupportedVoiceError: -20,
    }

    def calculate_score(
        self,
        provider_id: str,
        provider_info: ProviderInfo,
        quota: QuotaSnapshot | None,
        estimate: UsageEstimate | None,
        request: TTSRequest,
    ) -> float:
        score = float(max(0, 110 - provider_info.priority * 10))

        adapter = registry.get(provider_id)
        if adapter and request.language:
            if adapter.supports_language(request.language):
                score += 20
            else:
                score -= 50

        if quota:
            if quota.source in ("official_api", "response_metadata"):
                score += 25
            if quota.reset_policy == "monthly_billing_cycle":
                score += 20
            if quota.remaining is not None and quota.limit is not None and quota.limit > 0:
                pct = quota.remaining / quota.limit * 100
                score += min(30, pct * 0.3)

            if quota.reset_policy in ("unknown", "one_time_trial_credit"):
                score -= 30
            if quota.confidence == "low":
                score -= 20
            if quota.reset_policy in ("pay_as_you_go", "paid_topup"):
                score -= 200
        else:
            score -= 30

        if provider_info.last_error:
            score -= 50

        if provider_info.status == "blocked":
            score -= 200

        return score

    def rank_providers(self, request: TTSRequest) -> list[tuple[str, float]]:
        scores = []
        for pid in registry.list_ids():
            provider_info = provider_repo.get(pid)
            if not provider_info or not provider_info.enabled:
                continue

            if not api_key_repo.has_key(pid):
                continue

            adapter = registry.get(pid)
            if adapter and request.language and not adapter.supports_language(request.language):
                logger.debug(f"Skipping {pid}: unsupported language {request.language}")
                continue

            quota_mgr = QuotaManager()
            quota = quota_mgr.get_snapshot(pid)
            estimate = quota_mgr.estimate_request_usage(pid, request)

            pinfo = ProviderInfo(
                id=provider_info.id,
                name=provider_info.name,
                enabled=provider_info.enabled,
                priority=provider_info.priority,
                free_only=provider_info.free_only,
                status=provider_info.status,
                reset_policy=provider_info.reset_policy,
                quota_source=provider_info.quota_source,
                last_error=provider_info.last_error,
                api_key_configured=True,
            )

            score = self.calculate_score(pid, pinfo, quota, estimate, request)
            scores.append((pid, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def normalize_error(self, provider_id: str, error: Exception) -> str:
        error_map: dict[type, str] = {
            AuthError: "auth_error",
            QuotaExceededError: "quota_exceeded",
            RateLimitedError: "rate_limited",
            BillingRequiredError: "billing_required",
            ProviderUnavailableError: "server_error",
            UnsupportedLanguageError: "unsupported_language",
            UnsupportedVoiceError: "unsupported_voice",
        }
        for err_type, code in error_map.items():
            if isinstance(error, err_type):
                return code
        return "unknown"


class TTSService:
    def __init__(self):
        self.quota_manager = QuotaManager()
        self.fallback_engine = FallbackEngine()

    def generate(self, request: TTSRequest) -> TTSResult:
        if request.provider_id and request.force_provider:
            return self._generate_single(request, request.provider_id)

        ranking = self.fallback_engine.rank_providers(request)
        if not ranking:
            raise RuntimeError("No providers available to generate audio.")

        last_error: Exception | None = None
        fallback_chain: list[str] = []
        first_provider = ranking[0][0] if ranking else None

        for provider_id, _score in ranking:
            try:
                result = self._generate_single(request, provider_id)
                result.fallback_chain = fallback_chain
                self._record_generation(result, request, fallback_chain)
                if fallback_chain:
                    logger.info(f"Fallback succeeded: {' -> '.join(fallback_chain)} -> {provider_id}")
                return result
            except (QuotaExceededError, RateLimitedError, BillingRequiredError,
                    ProviderUnavailableError, UnsupportedLanguageError,
                    UnsupportedVoiceError, AuthError) as e:
                error_code = self.fallback_engine.normalize_error(provider_id, e)
                self._record_fallback_event(first_provider, provider_id, error_code)
                fallback_chain.append(provider_id)
                last_error = e
                logger.warning(f"Fallback from {provider_id}: {error_code} - {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error from {provider_id}: {e}")
                fallback_chain.append(provider_id)
                last_error = e
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    def _generate_single(self, request: TTSRequest, provider_id: str) -> TTSResult:
        adapter = registry.get(provider_id)
        if not adapter:
            provider_repo.set_status(provider_id, "error", "Provider not registered")
            raise UnknownProviderError(f"Provider '{provider_id}' not found.")

        quota = self.quota_manager.get_snapshot(provider_id)
        estimate = self.quota_manager.estimate_request_usage(provider_id, request)
        decision = self.quota_manager.can_use(provider_id, request, estimate, quota)

        if not decision.allowed:
            provider_repo.set_status(provider_id, "blocked", decision.reason)
            raise QuotaExceededError(f"Provider {provider_id} blocked: {decision.reason}")

        try:
            result = adapter.synthesize(request)
            self.quota_manager.record_usage(result)
            self._update_quota_after_usage(provider_id, result, request)
            provider_repo.set_status(provider_id, "ok")
            return result
        except (AuthError, QuotaExceededError, RateLimitedError, BillingRequiredError,
                ProviderUnavailableError, UnsupportedLanguageError, UnsupportedVoiceError) as e:
            error_code = self.fallback_engine.normalize_error(provider_id, e)
            provider_repo.set_status(provider_id, "error", error_code)
            raise

    def _update_quota_after_usage(self, provider_id: str, result: TTSResult, request: TTSRequest) -> None:
        snapshot = quota_repo.get_latest_snapshot(provider_id)
        if snapshot and snapshot.remaining is not None:
            chars = float(len(request.text))
            snapshot.used = (snapshot.used or 0) + chars
            snapshot.remaining = max(0, (snapshot.remaining or 0) - chars)
            quota_repo.save_snapshot(snapshot)

    def _record_generation(self, result: TTSResult, request: TTSRequest, fallback_chain: list[str]) -> None:
        gen = Generation(
            id=result.generation_id,
            provider_id=result.provider_id,
            model_id=result.model_id,
            voice_id=result.voice_id,
            language=result.language or request.language,
            input_text=request.text,
            input_characters=len(request.text),
            output_file_path=result.audio_file_path,
            output_format=request.output_format,
            duration_seconds=result.duration_seconds,
            status="success",
            fallback_from=fallback_chain[0] if fallback_chain else None,
            fallback_chain=",".join(fallback_chain) if fallback_chain else None,
            created_at=datetime.utcnow(),
        )
        generation_repo.save(gen)

    def _record_fallback_event(self, from_provider: str | None, to_provider: str, reason: str) -> None:
        event = FallbackEvent(
            from_provider=from_provider,
            to_provider=to_provider,
            reason=reason,
            error_code=reason,
            created_at=datetime.utcnow(),
        )
        fallback_repo.record(event)
