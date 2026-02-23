"""
Control Center — SQLAlchemy models.

Tables:
  repos, services, pipeline_runs, deployments, approvals, rbac_users, audit_log
"""
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    Enum, JSON, func,
)
from sqlalchemy.orm import relationship
from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ──────────────────────────────────────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────────────────────────────────────

class RunStatus(str, PyEnum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class Environment(str, PyEnum):
    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"


class ApprovalStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserRole(str, PyEnum):
    ADMIN = "admin"
    DEPLOYER = "deployer"
    VIEWER = "viewer"


# ──────────────────────────────────────────────────────────────────────────────
# repos
# ──────────────────────────────────────────────────────────────────────────────

class Repo(Base):
    __tablename__ = "repos"

    id = Column(String(36), primary_key=True, default=_uuid)
    owner = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    default_branch = Column(String(255), nullable=False, default="main")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    services = relationship("Service", back_populates="repo", cascade="all, delete-orphan")
    pipeline_runs = relationship("PipelineRun", back_populates="repo", cascade="all, delete-orphan")


# ──────────────────────────────────────────────────────────────────────────────
# services
# ──────────────────────────────────────────────────────────────────────────────

class Service(Base):
    __tablename__ = "services"

    id = Column(String(36), primary_key=True, default=_uuid)
    repo_id = Column(String(36), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String(255), nullable=False)
    cloud_run_service = Column(String(255), nullable=False)
    env = Column(Enum(Environment), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    repo = relationship("Repo", back_populates="services")
    pipeline_runs = relationship("PipelineRun", back_populates="service")
    deployments = relationship("Deployment", back_populates="service", cascade="all, delete-orphan")


# ──────────────────────────────────────────────────────────────────────────────
# pipeline_runs
# ──────────────────────────────────────────────────────────────────────────────

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    repo_id = Column(String(36), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(String(36), ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    github_run_id = Column(String(50), nullable=True, index=True)
    commit_sha = Column(String(40), nullable=True)
    status = Column(Enum(RunStatus), nullable=False, default=RunStatus.QUEUED)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    actor = Column(String(255), nullable=True)
    # JSON: [{"name": "lint", "status": "success", "started_at": ..., "finished_at": ...}]
    stage_json = Column(JSON, nullable=True)
    image_digest = Column(String(255), nullable=True)
    sbom_ref = Column(String(512), nullable=True)
    test_report_ref = Column(String(512), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    repo = relationship("Repo", back_populates="pipeline_runs")
    service = relationship("Service", back_populates="pipeline_runs")


# ──────────────────────────────────────────────────────────────────────────────
# deployments
# ──────────────────────────────────────────────────────────────────────────────

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(String(36), primary_key=True, default=_uuid)
    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    env = Column(Enum(Environment), nullable=False)
    image_digest = Column(String(255), nullable=False)
    cloud_run_revision = Column(String(255), nullable=True)
    # e.g. {"latest": 100} or {"canary": 10, "stable": 90}
    traffic_config = Column(JSON, nullable=True)
    deployed_at = Column(DateTime, server_default=func.now())
    deployed_by = Column(String(255), nullable=True)
    rollback_of = Column(String(36), ForeignKey("deployments.id", ondelete="SET NULL"), nullable=True)

    service = relationship("Service", back_populates="deployments")
    approvals = relationship("Approval", back_populates="deployment", cascade="all, delete-orphan")
    rollback_source = relationship("Deployment", remote_side="Deployment.id")


# ──────────────────────────────────────────────────────────────────────────────
# approvals
# ──────────────────────────────────────────────────────────────────────────────

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=_uuid)
    deployment_id = Column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False)
    env = Column(Enum(Environment), nullable=False)
    status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    requested_by = Column(String(255), nullable=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    deployment = relationship("Deployment", back_populates="approvals")


# ──────────────────────────────────────────────────────────────────────────────
# rbac_users
# ──────────────────────────────────────────────────────────────────────────────

class RBACUser(Base):
    __tablename__ = "rbac_users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ──────────────────────────────────────────────────────────────────────────────
# audit_log
# ──────────────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=_uuid)
    actor = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=True)
    target_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    details_json = Column(JSON, nullable=True)
