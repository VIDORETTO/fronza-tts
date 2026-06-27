from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class QuotaSnapshot(BaseModel):
    provider_id: str
    unit: Literal[
        "characters", "credits", "tokens", "minutes", "usd", "requests", "unknown"
    ]
    used: float | None = None
    limit: float | None = None
    remaining: float | None = None
    reset_policy: Literal[
        "monthly_billing_cycle",
        "daily_rate_limit",
        "per_minute_rate_limit",
        "one_time_trial_credit",
        "manual_balance",
        "paid_topup",
        "pay_as_you_go",
        "unknown",
    ]
    reset_at: datetime | None = None
    source: Literal[
        "official_api", "response_metadata", "local_ledger", "manual_config", "portal_manual", "unknown"
    ]
    confidence: Literal["high", "medium", "low"]
    updated_at: datetime = Field(default_factory=datetime.utcnow)
