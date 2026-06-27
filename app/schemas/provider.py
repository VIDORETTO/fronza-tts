from pydantic import BaseModel


class ProviderInfo(BaseModel):
    id: str
    name: str
    enabled: bool = True
    priority: int = 99
    free_only: bool = True
    status: str = "unknown"
    reset_policy: str = "unknown"
    quota_source: str = "unknown"
    last_error: str | None = None
    api_key_configured: bool = False


class ModelInfo(BaseModel):
    provider_id: str
    model_id: str
    name: str | None = None
    languages: list[str] = []
    is_default: bool = False


class VoiceInfo(BaseModel):
    provider_id: str
    voice_id: str
    name: str | None = None
    language: str | None = None
    is_default: bool = False
