"""SQLAlchemy ORM models for the chaos engineering subsystem."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

try:
    from packages.core.database import Base  # type: ignore
except ImportError:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):  # type: ignore  # noqa: E302
        pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExperimentType(str, PyEnum):
    API_LATENCY = "api_latency"
    DB_SATURATION = "db_saturation"
    WEBHOOK_FAILURE = "webhook_failure"
    BOOKING_SURGE = "booking_surge"
    RANDOM_500 = "random_500"
    INSTANCE_KILL = "instance_kill"
    SECRET_ROTATION = "secret_rotation"
    NETWORK_TIMEOUT = "network_timeout"
    CONCURRENCY_SPIKE = "concurrency_spike"


class RunStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class Environment(str, PyEnum):
    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------


class ChaosExperiment(Base):
    """Definition of a chaos experiment (from catalog — stored for audit)."""

    __tablename__ = "chaos_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), unique=True, nullable=False, index=True)
    experiment_type = Column(Enum(ExperimentType), nullable=False)
    hypothesis = Column(Text, nullable=False)
    blast_radius = Column(String(256), nullable=False)
    max_duration_sec = Column(Integer, nullable=False, default=300)
    abort_error_rate_pct = Column(Float, nullable=True)
    abort_p95_latency_ms = Column(Integer, nullable=True)
    allowed_envs = Column(String(64), nullable=False, default="dev,stage,prod")
    requires_compliance = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    runs = relationship("ChaosRun", back_populates="experiment", cascade="all, delete-orphan")


class ChaosRun(Base):
    """A single execution of a chaos experiment."""

    __tablename__ = "chaos_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("chaos_experiments.id"), nullable=False)
    experiment_name = Column(String(128), nullable=False)
    environment = Column(Enum(Environment), nullable=False)
    status = Column(Enum(RunStatus), nullable=False, default=RunStatus.PENDING)
    requester = Column(String(128), nullable=False)  # telegram username or "ci-system"
    compliance_approved = Column(Boolean, nullable=False, default=False)
    abort_reason = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    experiment = relationship("ChaosExperiment", back_populates="runs")
    metrics = relationship("ChaosMetric", back_populates="run", cascade="all, delete-orphan")

    @property
    def duration_sec(self) -> Optional[float]:
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None


class ChaosMetric(Base):
    """Point-in-time metric snapshot during a chaos run."""

    __tablename__ = "chaos_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("chaos_runs.id"), nullable=False)
    error_rate_pct = Column(Float, nullable=True)
    p95_latency_ms = Column(Integer, nullable=True)
    active_connections = Column(Integer, nullable=True)
    auto_recovered = Column(Boolean, nullable=True)
    mttr_sec = Column(Float, nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    run = relationship("ChaosRun", back_populates="metrics")
