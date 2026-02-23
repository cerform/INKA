"""Pydantic schemas for the chaos engineering API domain."""

import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class EnvironmentEnum(str, Enum):
    dev = "dev"
    stage = "stage"
    prod = "prod"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RunExperimentRequest(BaseModel):
    experiment_name: str = Field(
        ...,
        description="Name of the experiment from the catalog.",
        examples=["api_latency_injection"],
    )
    environment: EnvironmentEnum = Field(
        ...,
        description="Target environment.",
    )
    compliance_approved: bool = Field(
        default=False,
        description="Explicitly pass True for prod experiments with compliance approval.",
    )
    requester: str = Field(
        default="api",
        description="Identity of the requester (telegram username or 'ci-system').",
    )


class StopExperimentRequest(BaseModel):
    reason: str = Field(
        default="manual stop",
        description="Human-readable reason for stopping the experiment.",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ExperimentSummary(BaseModel):
    name: str
    experiment_type: str
    hypothesis: str
    blast_radius: str
    max_duration_sec: int
    abort_error_rate_pct: Optional[float]
    abort_p95_latency_ms: Optional[int]
    rollback_trigger: str
    allowed_envs: List[str]
    requires_compliance: bool
    description: str

    class Config:
        from_attributes = True


class RunResponse(BaseModel):
    run_id: str
    experiment_name: str
    environment: str
    status: str
    requester: str
    compliance_approved: bool
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    abort_reason: Optional[str]
    duration_sec: Optional[float]
    message: str

    class Config:
        from_attributes = True


class MetricSnapshot(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    error_rate_pct: Optional[float]
    p95_latency_ms: Optional[int]
    active_connections: Optional[int]
    auto_recovered: Optional[bool]
    recorded_at: datetime

    class Config:
        from_attributes = True


class HistoryItem(BaseModel):
    run_id: uuid.UUID
    experiment_name: str
    environment: str
    status: str
    requester: str
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_sec: Optional[float]
    abort_reason: Optional[str]

    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    window_days: int
    avg_mttr_sec: float
    auto_recovery_rate_pct: float
    rollback_frequency: int
    failed_resilience_tests: int
    total_runs: int
