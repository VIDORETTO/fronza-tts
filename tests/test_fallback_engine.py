import pytest
from datetime import datetime

from app.core.fallback_engine import FallbackEngine
from app.db.init_db import init_database
from app.db.repositories import api_key_repo, provider_repo
from app.db.models import Provider
from app.providers.registry import registry
from app.providers.mock import (
    MockProviderSuccess,
    MockProviderQuotaExceeded,
    MockProviderRateLimited,
    MockProviderBillingRequired,
)
from app.schemas.quota import QuotaSnapshot
from app.schemas.tts import TTSRequest
from app.utils.security import encrypt_value


@pytest.fixture(autouse=True)
def setup_db():
    init_database()
    registry._providers.clear()
    for pid in ["mock_success", "mock_quota", "mock_rate"]:
        p = provider_repo.get(pid)
        if not p:
            provider_repo.upsert(Provider(
                id=pid, name=pid, priority=1, enabled=True,
                reset_policy="monthly_billing_cycle", quota_source="local_ledger",
            ))
        encrypted = encrypt_value("test-key")
        if not api_key_repo.has_key(pid):
            api_key_repo.save(pid, encrypted)


class TestFallbackEngine:
    def setup_method(self):
        self.engine = FallbackEngine()
        registry.register(MockProviderSuccess("mock_success"))
        registry.register(MockProviderQuotaExceeded("mock_quota"))
        registry.register(MockProviderRateLimited("mock_rate"))

    def test_rank_providers_returns_list(self):
        request = TTSRequest(text="Hello world", language="en")
        ranking = self.engine.rank_providers(request)
        assert len(ranking) > 0
        assert all(isinstance(r, tuple) and len(r) == 2 for r in ranking)
