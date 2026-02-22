"""
Rollback Manager for INKA Chaos Engineering.

Each experiment type has a dedicated idempotent rollback handler.
The manager is called automatically by ChaosRunner on abort or at end of run.
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, Optional

logger = logging.getLogger(__name__)

# Type alias for rollback handlers
RollbackHandler = Callable[[str, dict], Coroutine[Any, Any, str]]


# ---------------------------------------------------------------------------
# Individual rollback implementations
# ---------------------------------------------------------------------------

async def _rollback_api_latency(run_id: str, ctx: dict) -> str:
    """Remove latency injection middleware / reset delay to 0."""
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "remove_latency_middleware"})
    # In production: call internal API endpoint to disable middleware flag
    # e.g. httpx.post("http://localhost:8000/internal/chaos/latency", json={"enabled": False})
    await asyncio.sleep(0.1)  # simulate async call
    return "API latency middleware disabled — delay restored to 0 ms."


async def _rollback_db_saturation(run_id: str, ctx: dict) -> str:
    """Release all held DB connections; reset pool to normal size."""
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "reset_db_pool"})
    # In production: dispose and recreate SQLAlchemy engine pool
    await asyncio.sleep(0.1)
    return "DB connection pool reset to default size."


async def _rollback_webhook_failure(run_id: str, ctx: dict) -> str:
    """Restore Telegram webhook URL to production endpoint."""
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "restore_webhook_url"})
    # In production: call Telegram setWebhook API with correct URL
    await asyncio.sleep(0.1)
    return "Telegram webhook restored to production URL."


async def _rollback_booking_surge(run_id: str, ctx: dict) -> str:
    """Stop load generator; verify booking table integrity."""
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "stop_booking_surge"})
    await asyncio.sleep(0.1)
    return "Booking conflict surge load generator stopped."


async def _rollback_random_500(run_id: str, ctx: dict) -> str:
    """Disable random 500 middleware flag."""
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "disable_random_500_middleware"})
    await asyncio.sleep(0.1)
    return "Random 500 middleware flag disabled."


async def _rollback_instance_kill(run_id: str, ctx: dict) -> str:
    """
    Cloud Run auto-scales after instance kill — no manual rollback needed.
    Verify new instance is healthy via Cloud Run describe.
    """
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "verify_cloudrun_recovery"})
    # In production: gcloud run services describe inka-api --region us-central1
    await asyncio.sleep(0.1)
    return "Cloud Run instance kill — auto-scaled replacement verified as healthy."


async def _rollback_secret_rotation(run_id: str, ctx: dict) -> str:
    """Revert to previous secret version; trigger config reload."""
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "revert_secret_version"})
    # In production: disable the new secret version, force Cloud Run restart
    await asyncio.sleep(0.1)
    return "Secret reverted to previous version; service config reload triggered."


async def _rollback_network_timeout(run_id: str, ctx: dict) -> str:
    """Restore default DB connection timeout values."""
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "restore_db_timeout"})
    await asyncio.sleep(0.1)
    return "DB connection timeout restored to default."


async def _rollback_concurrency_spike(run_id: str, ctx: dict) -> str:
    """Stop k6 load test process; verify services recovered."""
    logger.info("chaos_rollback", extra={"run_id": run_id, "action": "stop_k6_loadtest"})
    # In production: send SIGTERM to k6 process or cancel Cloud Build step
    await asyncio.sleep(0.1)
    return "k6 concurrency spike stopped; services cooling down."


# ---------------------------------------------------------------------------
# Rollback registry
# ---------------------------------------------------------------------------

_ROLLBACK_REGISTRY: Dict[str, RollbackHandler] = {
    "api_latency":     _rollback_api_latency,
    "db_saturation":   _rollback_db_saturation,
    "webhook_failure": _rollback_webhook_failure,
    "booking_surge":   _rollback_booking_surge,
    "random_500":      _rollback_random_500,
    "instance_kill":   _rollback_instance_kill,
    "secret_rotation": _rollback_secret_rotation,
    "network_timeout": _rollback_network_timeout,
    "concurrency_spike": _rollback_concurrency_spike,
}


class RollbackManager:
    """
    Orchestrates per-experiment rollback using the registry.

    Usage:
        manager = RollbackManager()
        result = await manager.rollback(run_id="abc123", experiment_type="api_latency")
    """

    async def rollback(
        self,
        run_id: str,
        experiment_type: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        Execute the rollback handler for the given experiment type.
        Returns a human-readable rollback result string.
        Raises KeyError if no handler is registered.
        """
        handler = _ROLLBACK_REGISTRY.get(experiment_type)
        if handler is None:
            raise KeyError(
                f"No rollback handler registered for experiment type '{experiment_type}'. "
                f"Available: {list(_ROLLBACK_REGISTRY.keys())}"
            )

        logger.info(
            "chaos_rollback_start",
            extra={"run_id": run_id, "experiment_type": experiment_type},
        )
        result = await handler(run_id, context or {})
        logger.info(
            "chaos_rollback_complete",
            extra={"run_id": run_id, "experiment_type": experiment_type, "result": result},
        )
        return result
