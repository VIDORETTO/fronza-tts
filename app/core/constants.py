from typing import Literal

ResetPolicy = Literal[
    "monthly_billing_cycle",
    "daily_rate_limit",
    "per_minute_rate_limit",
    "one_time_trial_credit",
    "manual_balance",
    "paid_topup",
    "pay_as_you_go",
    "unknown",
]

QuotaSource = Literal[
    "official_api",
    "response_metadata",
    "local_ledger",
    "manual_config",
    "portal_manual",
    "unknown",
]

Confidence = Literal["high", "medium", "low"]

RiskLevel = Literal["low", "medium", "high", "blocked"]

ErrorType = Literal[
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

OutputFormat = Literal["mp3", "wav", "ogg", "pcm"]

PROVIDER_IDS = [
    "elevenlabs",
    "cartesia",
    "smallest",
    "gemini",
    "inworld",
    "async_voice",
]

BADGES = {
    "safe": "SEGURO",
    "low_quota": "COTA BAIXA",
    "nearly_exhausted": "QUASE ESGOTADO",
    "blocked": "BLOQUEADO",
    "reset_monthly": "RESET MENSAL",
    "reset_daily": "RESET DIÁRIO",
    "trial_credit": "CRÉDITO INICIAL",
    "manual": "MANUAL",
    "uncertain": "INCERTO",
    "billing_risk": "RISCO DE COBRANÇA",
}

FREE_ONLY_MODE_WARN = (
    "Modo gratuito ativo. O app nunca usará provedores pagos automaticamente."
)
