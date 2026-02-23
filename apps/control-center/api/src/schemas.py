"""Pydantic request/response schemas for the CI/CD Control Center API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr

from .models import RunStatus, Environment, ApprovalStatus, UserRole


# ──────────────────────────────────────────────────────────────────────────────
# Shared
# ──────────────────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


# ──────────────────────────────────────────────────────────────────────────────
# Repos
# ──────────────────────────────────────────────────────────────────────────────

class RepoCreate(BaseModel):
    owner: str
    name: str
    default_branch: str = "main"


class RepoResponse(BaseModel):
    id: str
    owner: str
    name: str
    default_branch: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Services
# ──────────────────────────────────────────────────────────────────────────────

class ServiceCreate(BaseModel):
    repo_id: str
    service_name: str
    cloud_run_service: str
    env: Environment


class ServiceResponse(BaseModel):
    id: str
    repo_id: str
    service_name: str
    cloud_run_service: str
    env: Environment
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline Runs
# ──────────────────────────────────────────────────────────────────────────────

class TriggerRunRequest(BaseModel):
    repo_id: str
    service_id: Optional[str] = None
    workflow_file: str = "ci-control.yml"
    ref: str = "main"
    inputs: dict[str, Any] = {}


class TriggerRunResponse(BaseModel):
    run_id: str
    github_run_id: Optional[str]
    status: RunStatus
    message: str


class StageInfo(BaseModel):
    name: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class PipelineRunResponse(BaseModel):
    id: str
    repo_id: str
    service_id: Optional[str]
    github_run_id: Optional[str]
    commit_sha: Optional[str]
    status: RunStatus
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    actor: Optional[str]
    stage_json: Optional[list[dict[str, Any]]]
    image_digest: Optional[str]
    sbom_ref: Optional[str]
    test_report_ref: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Deployments
# ──────────────────────────────────────────────────────────────────────────────

class DeployRequest(BaseModel):
    service_id: str
    env: Environment
    image_digest: str
    workflow_file: str = "deploy-with-callback.yml"
    notify: bool = True


class RollbackRequest(BaseModel):
    service_id: str
    env: Environment
    to_revision: Optional[str] = None
    to_image_digest: Optional[str] = None
    reason: str


class DeploymentResponse(BaseModel):
    id: str
    service_id: str
    env: Environment
    image_digest: str
    cloud_run_revision: Optional[str]
    traffic_config: Optional[dict[str, Any]]
    deployed_at: datetime
    deployed_by: Optional[str]
    rollback_of: Optional[str]

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Approvals
# ──────────────────────────────────────────────────────────────────────────────

class ApprovalRequest(BaseModel):
    deployment_id: str
    env: Environment
    requested_by: str


class ApprovalDecision(BaseModel):
    reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: str
    deployment_id: str
    env: Environment
    status: ApprovalStatus
    requested_by: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# RBAC Users
# ──────────────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    role: UserRole = UserRole.VIEWER


class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Audit Log
# ──────────────────────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: str
    actor: str
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    timestamp: datetime
    details_json: Optional[dict[str, Any]]

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# DORA Metrics
# ──────────────────────────────────────────────────────────────────────────────

class DORAMetricsResponse(BaseModel):
    period_days: int
    deployment_frequency: float           # deploys per day
    deployment_frequency_label: str       # "Multiple per day" etc.
    lead_time_hours: float                # commit → deploy
    mean_time_to_restore_hours: float     # incident → stable
    change_failure_rate: float            # 0.0–1.0
    total_deployments: int
    failed_deployments: int
    rollbacks: int


# ──────────────────────────────────────────────────────────────────────────────
# GitHub Webhook
# ──────────────────────────────────────────────────────────────────────────────

class WebhookAck(BaseModel):
    received: bool
    event: str
    action: Optional[str] = None
