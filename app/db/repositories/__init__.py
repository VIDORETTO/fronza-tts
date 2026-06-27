from app.utils.logging import logger

from .fallback_repo import FallbackRepo
from .provider_repo import ApiKeyRepo, ProviderRepo
from .quota_repo import QuotaRepo
from .usage_repo import GenerationRepo, UsageRepo

provider_repo = ProviderRepo()
api_key_repo = ApiKeyRepo()
quota_repo = QuotaRepo()
usage_repo = UsageRepo()
generation_repo = GenerationRepo()
fallback_repo = FallbackRepo()

logger.debug("Repositories initialized")
