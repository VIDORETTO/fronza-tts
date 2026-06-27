import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import config
from app.core.fallback_engine import TTSService
from app.db.init_db import init_database
from app.providers.registry import registry
from app.schemas.tts import TTSRequest
from app.utils.logging import logger


def main():
    init_database()

    import app.providers.elevenlabs  # noqa: F401
    import app.providers.cartesia  # noqa: F401
    import app.providers.smallest  # noqa: F401
    import app.providers.gemini  # noqa: F401
    import app.providers.inworld  # noqa: F401
    import app.providers.async_voice  # noqa: F401
    import app.providers.mock  # noqa: F401

    logger.info("=" * 60)
    logger.info("FALLBACK TEST")
    logger.info("=" * 60)
    logger.info(f"Registered providers: {registry.list_ids()}")
    logger.info(f"Free-only mode: {config.app.free_only_mode}")

    service = TTSService()

    test_cases = [
        ("Short text in English", "Hello, this is a test of the fallback system."),
        ("Short text in Portuguese", "Olá, isto é um teste do sistema de fallback."),
    ]

    for name, text in test_cases:
        logger.info(f"\n--- Test: {name} ---")
        request = TTSRequest(text=text, language="en")
        try:
            result = service.generate(request)
            logger.info(f"SUCCESS: provider={result.provider_id}, file={result.audio_file_path}")
            if result.fallback_chain:
                logger.info(f"Fallback chain: {' -> '.join(result.fallback_chain)}")
        except Exception as e:
            logger.error(f"FAILED: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("Fallback test completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
