"""
Chaos Experiment Catalog for INKA Admin.

Each experiment definition is immutable and contains:
- hypothesis: what resilience property we test
- blast_radius: scope of impact
- max_duration_sec: hard ceiling (≤ 300)
- abort_error_rate_pct / abort_p95_latency_ms: auto-stop thresholds
- rollback_trigger: condition that fires rollback
- allowed_envs: where the experiment can run
- requires_compliance: whether prod requires approval token
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Optional


@dataclass(frozen=True)
class ExperimentDefinition:
    name: str
    experiment_type: str
    hypothesis: str
    blast_radius: str
    max_duration_sec: int  # hard cap — MUST be ≤ 300
    abort_error_rate_pct: Optional[float]
    abort_p95_latency_ms: Optional[int]
    rollback_trigger: str
    allowed_envs: FrozenSet[str]
    requires_compliance: bool = False
    description: str = ""


# ---------------------------------------------------------------------------
# The catalog — 9 experiments
# ---------------------------------------------------------------------------

EXPERIMENTS: Dict[str, ExperimentDefinition] = {

    # 1. API latency injection
    "api_latency_injection": ExperimentDefinition(
        name="api_latency_injection",
        experiment_type="api_latency",
        hypothesis=(
            "The system handles +500 ms API latency gracefully — "
            "clients retry correctly and p95 stays below 2000 ms."
        ),
        blast_radius="All inbound HTTP requests to the API service",
        max_duration_sec=300,
        abort_error_rate_pct=10.0,
        abort_p95_latency_ms=2000,
        rollback_trigger="p95 latency > 2000 ms OR error rate > 10%",
        allowed_envs=frozenset({"dev", "stage", "prod"}),
        requires_compliance=False,
        description="Injects 500 ms artificial delay via FastAPI middleware.",
    ),

    # 2. DB connection saturation
    "db_connection_saturation": ExperimentDefinition(
        name="db_connection_saturation",
        experiment_type="db_saturation",
        hypothesis=(
            "The API returns 503 with a clear error message when DB pool is "
            "exhausted, and recovers automatically once load subsides."
        ),
        blast_radius="All API endpoints that use database connections",
        max_duration_sec=180,
        abort_error_rate_pct=10.0,
        abort_p95_latency_ms=5000,
        rollback_trigger="error rate > 10% OR API error responses > 50% for 30 s",
        allowed_envs=frozenset({"dev", "stage", "prod"}),
        requires_compliance=True,
        description="Saturates async DB connection pool by opening max connections.",
    ),

    # 3. Telegram webhook failure
    "telegram_webhook_failure": ExperimentDefinition(
        name="telegram_webhook_failure",
        experiment_type="webhook_failure",
        hypothesis=(
            "Bot commands queue correctly during webhook unavailability "
            "and drain without data loss when restored."
        ),
        blast_radius="All Telegram bot webhook ingestion",
        max_duration_sec=120,
        abort_error_rate_pct=None,
        abort_p95_latency_ms=None,
        rollback_trigger="S1 defect triggered OR bot unavailable > 2 min",
        allowed_envs=frozenset({"dev", "stage"}),
        requires_compliance=False,
        description="Temporarily routes webhook to a black-hole endpoint.",
    ),

    # 4. Booking conflict surge
    "booking_conflict_surge": ExperimentDefinition(
        name="booking_conflict_surge",
        experiment_type="booking_surge",
        hypothesis=(
            "Booking conflict detection remains correct and returns 409 "
            "without data corruption under concurrent surge traffic."
        ),
        blast_radius="Booking API endpoints and DB booking table",
        max_duration_sec=180,
        abort_error_rate_pct=20.0,
        abort_p95_latency_ms=3000,
        rollback_trigger="error rate > 20% OR data integrity check fails",
        allowed_envs=frozenset({"dev", "stage"}),
        requires_compliance=False,
        description="Fires 50 concurrent booking requests with conflicting time slots.",
    ),

    # 5. Random 500 error injection  [DEV / STAGE ONLY]
    "random_500_injection": ExperimentDefinition(
        name="random_500_injection",
        experiment_type="random_500",
        hypothesis=(
            "Clients and the bot handle random 500 errors gracefully "
            "with retry logic and display user-friendly error messages."
        ),
        blast_radius="5% of all HTTP responses from API",
        max_duration_sec=300,
        abort_error_rate_pct=15.0,
        abort_p95_latency_ms=None,
        rollback_trigger="error rate > 15% sustained for 60 s",
        allowed_envs=frozenset({"dev", "stage"}),  # NEVER prod
        requires_compliance=False,
        description="Middleware randomly returns HTTP 500 for ~5% of requests.",
    ),

    # 6. Cloud Run instance kill
    "cloud_run_instance_kill": ExperimentDefinition(
        name="cloud_run_instance_kill",
        experiment_type="instance_kill",
        hypothesis=(
            "Cloud Run auto-scales and restores a replacement instance "
            "within 30 s, with < 5% error rate during the recovery window."
        ),
        blast_radius="One Cloud Run instance of inka-api service",
        max_duration_sec=120,
        abort_error_rate_pct=5.0,
        abort_p95_latency_ms=3000,
        rollback_trigger="error rate > 5% for > 30 s OR no recovery after 90 s",
        allowed_envs=frozenset({"dev", "stage", "prod"}),
        requires_compliance=True,
        description="Sends SIGKILL to one running Cloud Run instance via gcloud.",
    ),

    # 7. Secret rotation simulation
    "secret_rotation_simulation": ExperimentDefinition(
        name="secret_rotation_simulation",
        experiment_type="secret_rotation",
        hypothesis=(
            "Services reload new secrets within their rotation window "
            "without causing auth failures exceeding SLA threshold."
        ),
        blast_radius="Secret Manager secret versions; config reload path",
        max_duration_sec=300,
        abort_error_rate_pct=None,
        abort_p95_latency_ms=None,
        rollback_trigger="auth failure rate > 2% OR secret unavailable > 60 s",
        allowed_envs=frozenset({"dev", "stage", "prod"}),
        requires_compliance=True,
        description="Adds a new secret version and forces app to reload config.",
    ),

    # 8. Network timeout between API and DB
    "network_timeout_api_db": ExperimentDefinition(
        name="network_timeout_api_db",
        experiment_type="network_timeout",
        hypothesis=(
            "The API returns 503 with timeout context when the DB "
            "connection times out, without hanging requests indefinitely."
        ),
        blast_radius="DB connection layer — all API requests that query DB",
        max_duration_sec=180,
        abort_error_rate_pct=15.0,
        abort_p95_latency_ms=5000,
        rollback_trigger="error rate > 15% OR any request hangs > 30 s",
        allowed_envs=frozenset({"dev", "stage", "prod"}),
        requires_compliance=True,
        description="Applies connection timeout of 2 s to DB pool to simulate network partition.",
    ),

    # 9. High concurrency spike (load test)
    "high_concurrency_spike": ExperimentDefinition(
        name="high_concurrency_spike",
        experiment_type="concurrency_spike",
        hypothesis=(
            "The system sustains 500 RPS for 5 minutes with p95 < 3000 ms "
            "and error rate < 5%, demonstrating horizontal scalability."
        ),
        blast_radius="All three services — inka-api, inka-bot, inka-admin",
        max_duration_sec=300,
        abort_error_rate_pct=5.0,
        abort_p95_latency_ms=3000,
        rollback_trigger="p95 > 3000 ms OR error rate > 5% OR S1 defect",
        allowed_envs=frozenset({"dev", "stage", "prod"}),
        requires_compliance=True,
        description="k6 load test ramping to 500 VUs hitting key API endpoints.",
    ),
}


class ExperimentCatalog:
    """Read-only interface to the chaos experiment catalog."""

    def list_all(self) -> list[ExperimentDefinition]:
        return list(EXPERIMENTS.values())

    def get(self, name: str) -> ExperimentDefinition:
        if name not in EXPERIMENTS:
            raise KeyError(f"Unknown experiment: '{name}'. Available: {list(EXPERIMENTS.keys())}")
        return EXPERIMENTS[name]

    def list_for_env(self, env: str) -> list[ExperimentDefinition]:
        return [e for e in EXPERIMENTS.values() if env in e.allowed_envs]

    def names(self) -> list[str]:
        return list(EXPERIMENTS.keys())
