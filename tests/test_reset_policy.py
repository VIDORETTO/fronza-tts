import pytest
from datetime import datetime

from app.core.reset_policy import ResetPolicyEngine
from app.schemas.quota import QuotaSnapshot


class TestResetPolicyEngine:
    def setup_method(self):
        self.engine = ResetPolicyEngine()

    def test_monthly_cycle_no_reset_before_date(self):
        snapshot = QuotaSnapshot(
            provider_id="test",
            unit="characters",
            used=100.0,
            limit=10000.0,
            remaining=9900.0,
            reset_policy="monthly_billing_cycle",
            reset_at=datetime(2026, 7, 27),
            source="official_api",
            confidence="high",
            updated_at=datetime.utcnow(),
        )
        now = datetime(2026, 6, 27)
        assert not self.engine.should_reset("test", snapshot, now)

    def test_monthly_cycle_reset_after_date(self):
        snapshot = QuotaSnapshot(
            provider_id="test",
            unit="characters",
            used=100.0,
            limit=10000.0,
            remaining=9900.0,
            reset_policy="monthly_billing_cycle",
            reset_at=datetime(2026, 6, 15),
            source="official_api",
            confidence="high",
            updated_at=datetime.utcnow(),
        )
        now = datetime(2026, 6, 27)
        assert self.engine.should_reset("test", snapshot, now)

    def test_no_reset_without_snapshot(self):
        assert not self.engine.should_reset("test", None)

    def test_one_time_credit_never_resets(self):
        snapshot = QuotaSnapshot(
            provider_id="test",
            unit="characters",
            used=100.0,
            limit=500.0,
            remaining=400.0,
            reset_policy="one_time_trial_credit",
            source="manual_config",
            confidence="low",
            updated_at=datetime.utcnow(),
        )
        assert not self.engine.should_reset("test", snapshot)
        assert self.engine.get_next_reset_at("one_time_trial_credit") is None

    def test_daily_reset_across_days(self):
        snapshot = QuotaSnapshot(
            provider_id="test",
            unit="requests",
            used=50.0,
            limit=100.0,
            remaining=50.0,
            reset_policy="daily_rate_limit",
            source="official_api",
            confidence="high",
            updated_at=datetime(2026, 6, 26, 23, 0),
        )
        now = datetime(2026, 6, 27, 1, 0)
        assert self.engine.should_reset("test", snapshot, now)

    def test_next_reset_at_monthly(self):
        from datetime import timedelta
        result = self.engine.get_next_reset_at("monthly_billing_cycle")
        assert result is not None
        assert result > datetime.utcnow()

    def test_next_reset_at_daily(self):
        from datetime import timedelta
        result = self.engine.get_next_reset_at("daily_rate_limit")
        assert result is not None
        assert result.day == datetime.utcnow().day or result.day == (datetime.utcnow().day + 1) % 31
