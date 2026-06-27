from app.core.config import config
from app.core.constants import RiskLevel
from app.db.repositories import quota_repo
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest, TTSResult
from app.schemas.usage import UsageEstimate
from app.utils.logging import logger


class QuotaDecision:
    allowed: bool
    reason: str
    risk_level: RiskLevel
    requires_confirmation: bool

    def __init__(self, allowed: bool, reason: str, risk_level: RiskLevel, requires_confirmation: bool = False):
        self.allowed = allowed
        self.reason = reason
        self.risk_level = risk_level
        self.requires_confirmation = requires_confirmation


class QuotaManager:
    def get_snapshot(self, provider_id: str) -> QuotaSnapshot | None:
        return quota_repo.get_latest_snapshot(provider_id)

    def refresh_quota(self, provider_id: str) -> QuotaSnapshot | None:
        return self.get_snapshot(provider_id)

    def estimate_request_usage(self, provider_id: str, request: TTSRequest) -> UsageEstimate:
        chars = len(request.text)
        return UsageEstimate(
            provider_id=provider_id,
            unit="characters",
            estimated_amount=float(chars),
            confidence="high",
            notes="Characters count",
        )

    def can_use(self, provider_id: str, request: TTSRequest, estimate: UsageEstimate, quota: QuotaSnapshot | None) -> QuotaDecision:
        policy = config.quota_policy

        if quota is None:
            if len(request.text) > config.app.max_text_chars_when_quota_unknown:
                return QuotaDecision(
                    allowed=False,
                    reason="Quota unknown and text is too long. Blocking in free mode.",
                    risk_level="blocked",
                )
            if policy.require_confirmation_for_uncertain_quota:
                return QuotaDecision(
                    allowed=True,
                    reason="Quota unknown but text is short. Confirmation required.",
                    risk_level="medium",
                    requires_confirmation=True,
                )
            return QuotaDecision(
                allowed=True,
                reason="Quota unknown. Using with caution.",
                risk_level="medium",
            )

        if quota.reset_policy in ("pay_as_you_go", "paid_topup") and config.app.free_only_mode:
            return QuotaDecision(
                allowed=False,
                reason=f"Provider uses '{quota.reset_policy}' policy. Blocked in free_only mode.",
                risk_level="blocked",
            )

        if quota.remaining is not None and quota.limit is not None:
            pct_used = (quota.used or 0) / quota.limit * 100 if quota.limit > 0 else 0

            if pct_used >= policy.hard_stop_threshold_percent:
                return QuotaDecision(
                    allowed=False,
                    reason=f"Quota {pct_used:.0f}% used. Hard stop threshold ({policy.hard_stop_threshold_percent}%) reached.",
                    risk_level="blocked",
                )

            if pct_used >= policy.fallback_threshold_percent:
                return QuotaDecision(
                    allowed=True,
                    reason=f"Quota {pct_used:.0f}% used. Above fallback threshold, will be skipped in auto mode.",
                    risk_level="high",
                )

            if pct_used >= policy.warning_threshold_percent:
                return QuotaDecision(
                    allowed=True,
                    reason=f"Quota {pct_used:.0f}% used. Warning threshold reached.",
                    risk_level="medium",
                )

            return QuotaDecision(
                allowed=True,
                reason=f"Quota {pct_used:.0f}% used. Sufficient available.",
                risk_level="low",
            )

        return QuotaDecision(
            allowed=True,
            reason="Quota status uncertain but no usage data available.",
            risk_level="medium",
        )

    def record_usage(self, result: TTSResult) -> None:
        logger.info(f"Recording usage for {result.provider_id}: gen_id={result.generation_id}")
