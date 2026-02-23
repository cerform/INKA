"""
Sentry error-tracking configuration.

- No-op when DSN is empty (safe for local dev)
- Integrates FastAPI, SQLAlchemy breadcrumbs
- Adjustable sample rate per environment
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def setup_sentry(
    dsn: str | None = None,
    environment: str = "development",
    version: str = "0.1.0",
) -> None:
    """
    Initialise Sentry SDK.

    If `dsn` is falsy the function is a complete no-op so local
    development never phones home.
    """
    if not dsn:
        logger.info("Sentry DSN not set – error tracking disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=version,
            traces_sample_rate=0.1 if environment == "production" else 1.0,
            profiles_sample_rate=0.1 if environment == "production" else 0.0,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            send_default_pii=False,
        )
        logger.info("Sentry initialised for %s (env=%s)", version, environment)

    except ImportError:
        logger.warning("sentry-sdk not installed – error tracking disabled")
    except Exception:
        logger.warning("Sentry init failed", exc_info=True)
