from app.providers.base import TTSProvider
from app.utils.logging import logger


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, TTSProvider] = {}

    def register(self, provider: TTSProvider) -> None:
        self._providers[provider.provider_id] = provider
        logger.info(f"Registered provider: {provider.provider_id}")

    def get(self, provider_id: str) -> TTSProvider | None:
        return self._providers.get(provider_id)

    def list_ids(self) -> list[str]:
        return list(self._providers.keys())

    def list_all(self) -> list[TTSProvider]:
        return list(self._providers.values())

    def is_registered(self, provider_id: str) -> bool:
        return provider_id in self._providers


registry = ProviderRegistry()
