import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime

from app.db.init_db import init_database
from app.db.repositories import quota_repo
from app.providers.registry import registry
from app.schemas.quota import QuotaSnapshot
from app.utils.logging import logger


def main():
    init_database()

    import app.providers.elevenlabs  # noqa: F401
    import app.providers.cartesia  # noqa: F401
    import app.providers.smallest  # noqa: F401
    import app.providers.gemini  # noqa: F401
    import app.providers.inworld  # noqa: F401
    import app.providers.async_voice  # noqa: F401

    parser = argparse.ArgumentParser(description="Refresh quota for a provider")
    parser.add_argument("--provider", required=True, help="Provider ID")

    args = parser.parse_args()

    adapter = registry.get(args.provider)
    if not adapter:
        logger.error(f"Provider '{args.provider}' not found. Available: {registry.list_ids()}")
        sys.exit(1)

    logger.info(f"Refreshing quota for: {args.provider}")
    try:
        quota = adapter.get_quota()
        quota_repo.save_snapshot(quota)
        logger.info(f"Quota updated: used={quota.used}, limit={quota.limit}, remaining={quota.remaining}")
        logger.info(f"Reset policy: {quota.reset_policy}, confidence: {quota.confidence}")
        logger.info(f"Source: {quota.source}")
    except Exception as e:
        logger.error(f"Failed to refresh quota: {e}")


if __name__ == "__main__":
    main()
