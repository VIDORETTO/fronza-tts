from app.core.audio_storage import AudioStorage
from app.core.config import Config
from app.core.fallback_engine import FallbackEngine, TTSService
from app.core.quota_manager import QuotaManager
from app.core.reset_policy import ResetPolicyEngine
from app.core.text_chunker import TextChunker
from app.core.usage_estimator import UsageEstimator
from app.db.init_db import init_database
from app.utils.logging import logger


class TTSRouter:
    def __init__(self, config: Config):
        self.config = config
        self.quota_manager = QuotaManager()
        self.reset_policy_engine = ResetPolicyEngine()
        self.fallback_engine = FallbackEngine()
        self.text_chunker = TextChunker(config.chunk_limits)
        self.audio_storage = AudioStorage()
        self.usage_estimator = UsageEstimator()
        self.tts_service = TTSService()
        logger.info("TTS Router initialized")

    def initialize(self):
        init_database()
        logger.info("System initialized. Free-only mode: {}", self.config.app.free_only_mode)
