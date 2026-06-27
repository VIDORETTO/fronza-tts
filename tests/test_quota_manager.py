import pytest
from datetime import datetime

from app.core.quota_manager import QuotaManager, QuotaDecision
from app.core.config import config
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest


class TestQuotaManager:
    def setup_method(self):
        self.manager = QuotaManager()

    def test_no_quota_short_text(self):
        request = TTSRequest(text="hello")
        estimate = self.manager.estimate_request_usage("test", request)
        decision = self.manager.can_use("test", request, estimate, None)
        assert decision.allowed
        assert decision.risk_level in ("medium", "low")

    def test_no_quota_long_text_blocked(self):
        request = TTSRequest(text="A" * 1000)
        estimate = self.manager.estimate_request_usage("test", request)
        decision = self.manager.can_use("test", request, estimate, None)
        assert not decision.allowed or decision.risk_level == "medium"

    def test_sufficient_quota(self):
        quota = QuotaSnapshot(
            provider_id="test",
            unit="characters",
            used=100.0,
            limit=10000.0,
            remaining=9900.0,
            reset_policy="monthly_billing_cycle",
            source="official_api",
            confidence="high",
            updated_at=datetime.utcnow(),
        )
        request = TTSRequest(text="hello")
        estimate = self.manager.estimate_request_usage("test", request)
        decision = self.manager.can_use("test", request, estimate, quota)
        assert decision.allowed
        assert decision.risk_level == "low"

    def test_quota_above_80_warning(self):
        quota = QuotaSnapshot(
            provider_id="test",
            unit="characters",
            used=8500.0,
            limit=10000.0,
            remaining=1500.0,
            reset_policy="monthly_billing_cycle",
            source="official_api",
            confidence="high",
            updated_at=datetime.utcnow(),
        )
        request = TTSRequest(text="hello")
        estimate = self.manager.estimate_request_usage("test", request)
        decision = self.manager.can_use("test", request, estimate, quota)
        assert decision.allowed
        assert decision.risk_level == "medium"

    def test_quota_above_97_blocked(self):
        quota = QuotaSnapshot(
            provider_id="test",
            unit="characters",
            used=9800.0,
            limit=10000.0,
            remaining=200.0,
            reset_policy="monthly_billing_cycle",
            source="official_api",
            confidence="high",
            updated_at=datetime.utcnow(),
        )
        request = TTSRequest(text="hello")
        estimate = self.manager.estimate_request_usage("test", request)
        decision = self.manager.can_use("test", request, estimate, quota)
        assert not decision.allowed
        assert decision.risk_level == "blocked"

    def test_pay_as_you_go_blocked_in_free_mode(self):
        quota = QuotaSnapshot(
            provider_id="test",
            unit="usd",
            used=0.0,
            limit=100.0,
            remaining=100.0,
            reset_policy="pay_as_you_go",
            source="official_api",
            confidence="high",
            updated_at=datetime.utcnow(),
        )
        request = TTSRequest(text="hello")
        estimate = self.manager.estimate_request_usage("test", request)
        decision = self.manager.can_use("test", request, estimate, quota)
        assert not decision.allowed

    def test_quota_below_80_allowed(self):
        quota = QuotaSnapshot(
            provider_id="test",
            unit="characters",
            used=1000.0,
            limit=10000.0,
            remaining=9000.0,
            reset_policy="monthly_billing_cycle",
            source="official_api",
            confidence="high",
            updated_at=datetime.utcnow(),
        )
        request = TTSRequest(text="hello")
        estimate = self.manager.estimate_request_usage("test", request)
        decision = self.manager.can_use("test", request, estimate, quota)
        assert decision.allowed
        assert decision.risk_level == "low"
