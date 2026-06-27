import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse

from app.db.init_db import init_database
from app.providers.registry import registry
from app.utils.logging import logger


def main():
    init_database()

    import app.providers.elevenlabs  # noqa: F401
    import app.providers.cartesia  # noqa: F401
    import app.providers.smallest  # noqa: F401
    import app.providers.gemini  # noqa: F401
    import app.providers.inworld  # noqa: F401
    import app.providers.async_voice  # noqa: F401

    parser = argparse.ArgumentParser(description="Test a TTS provider")
    parser.add_argument("--provider", required=True, help="Provider ID")
    parser.add_argument("--text", default="This is a quick test of text to speech.", help="Text to synthesize")

    args = parser.parse_args()

    adapter = registry.get(args.provider)
    if not adapter:
        logger.error(f"Provider '{args.provider}' not found. Available: {registry.list_ids()}")
        sys.exit(1)

    logger.info(f"Testing provider: {args.provider}")
    logger.info(f"Text: {args.text}")

    from app.schemas.tts import TTSRequest

    request = TTSRequest(text=args.text, language="en")

    try:
        logger.info(f"Listing models...")
        models = adapter.list_models()
        logger.info(f"Models: {[m.model_id for m in models]}")

        logger.info(f"Listing voices...")
        voices = adapter.list_voices()
        logger.info(f"Voices: {[v.name or v.voice_id for v in voices]}")

        logger.info(f"Checking quota...")
        quota = adapter.get_quota()
        logger.info(f"Quota: {quota}")

        logger.info(f"Generating audio...")
        result = adapter.synthesize(request)
        logger.info(f"Success! Audio saved to: {result.audio_file_path}")

    except NotImplementedError as e:
        logger.error(f"Provider not fully implemented: {e}")
    except Exception as e:
        logger.error(f"Error testing provider: {e}", exc_info=True)


if __name__ == "__main__":
    main()
