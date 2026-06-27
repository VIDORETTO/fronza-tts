from app.core.config import Config, config as app_config
from app.core.router import TTSRouter
from app.utils.logging import logger


def create_router(config: Config | None = None) -> TTSRouter:
    cfg = config or app_config
    router = TTSRouter(cfg)
    router.initialize()
    return router
