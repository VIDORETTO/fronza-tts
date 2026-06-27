from datetime import datetime, timedelta

from app.db.repositories import quota_repo
from app.schemas.quota import QuotaSnapshot
from app.utils.logging import logger


class ResetPolicyEngine:
    def should_reset(self, provider_id: str, last_snapshot: QuotaSnapshot | None, now: datetime | None = None) -> bool:
        if last_snapshot is None:
            return False
        if now is None:
            now = datetime.utcnow()

        policy = last_snapshot.reset_policy

        if policy == "monthly_billing_cycle":
            if last_snapshot.reset_at and now >= last_snapshot.reset_at:
                return True
            return False

        if policy == "daily_rate_limit":
            if last_snapshot.reset_at and now >= last_snapshot.reset_at:
                return True
            if last_snapshot.updated_at.date() < now.date():
                return True
            return False

        if policy in ("per_minute_rate_limit",):
            return False

        if policy in ("one_time_trial_credit", "manual_balance", "paid_topup", "pay_as_you_go", "unknown"):
            return False

        return False

    def get_next_reset_at(self, reset_policy: str, last_reset_at: datetime | None = None) -> datetime | None:
        now = datetime.utcnow()

        if reset_policy == "monthly_billing_cycle":
            if last_reset_at:
                next_month = last_reset_at.replace(day=1) + timedelta(days=32)
                return next_month.replace(day=min(last_reset_at.day, 28))
            return (now.replace(day=1) + timedelta(days=32)).replace(day=1)

        if reset_policy == "daily_rate_limit":
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        if reset_policy == "per_minute_rate_limit":
            return now + timedelta(minutes=1)

        return None

    def apply_reset(self, provider_id: str) -> QuotaSnapshot | None:
        last = quota_repo.get_latest_snapshot(provider_id)
        if last and self.should_reset(provider_id, last):
            logger.info(f"Resetting quota for provider: {provider_id}")
            if last.reset_policy == "daily_rate_limit":
                new_snapshot = last.model_copy(update={
                    "used": 0.0,
                    "remaining": last.limit,
                    "updated_at": datetime.utcnow(),
                })
                quota_repo.save_snapshot(new_snapshot)
                return new_snapshot
        return last
