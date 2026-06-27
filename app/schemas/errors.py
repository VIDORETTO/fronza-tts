from typing import Literal

from pydantic import BaseModel


class ProviderError(BaseModel):
    provider_id: str
    error_type: Literal[
        "auth_error",
        "quota_exceeded",
        "rate_limited",
        "billing_required",
        "server_error",
        "timeout",
        "unsupported_language",
        "unsupported_voice",
        "bad_request",
        "unknown",
    ]
    retryable: bool
    fallback_allowed: bool
    raw_status_code: int | None = None
    message: str
