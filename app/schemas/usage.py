from typing import Literal

from pydantic import BaseModel


class UsageEstimate(BaseModel):
    provider_id: str
    unit: str
    estimated_amount: float
    confidence: Literal["high", "medium", "low"]
    notes: str | None = None
