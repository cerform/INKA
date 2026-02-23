# Zero-Trust Access Controller — INKA Admin
**System:** INKA Admin
**Version:** 1.0 | **Updated:** 2026-02-22

---

## 1) Zero-Trust Model
- **Default deny** for all users, services, and internal components.
- **Continuous verification** on every request (identity, device posture, session state, and risk signals).
- **Least privilege** via role-based access with scoped permissions.
- **Short-lived access** with expiring sessions and rotating tokens.
- **Strict environment isolation** (dev/stage/prod) with separate identities and secrets.

## 2) Enforcement Mechanisms
- **RBAC + scoped permissions**
  - Roles map to explicit permissions (e.g., `access:read`, `access:revoke`, `session:read`).
  - All commands and APIs enforce permission checks at handler and service layers.
- **Break-glass approval flow**
  - Temporary elevation requires justification, approval, time-bound access, and audit logging.
  - Automatic revocation on expiry with explicit closure.
- **Session expiration**
  - Max session lifetime and idle timeout.
  - Re-authentication required for sensitive actions.
- **IP/device anomaly detection**
  - Risk scoring on new IP, geo anomalies, device fingerprint mismatch, or velocity spikes.
  - Adaptive enforcement: MFA re-check or temporary deny.
- **Rate-limited sensitive endpoints**
  - Strict per-user and per-service limits for access changes and break-glass requests.
  - Circuit breakers for repeated failures.
- **Service-to-service identity verification**
  - mTLS or signed JWT with aud/iss checks.
  - SPIFFE/SPIRE or workload identity where supported.

### Telegram Commands (Access Control)
- `/access audit` — summary of access policies, active roles, and recent changes.
- `/access drift` — report detected drift signals and remediation status.
- `/access revoke {user}` — revoke access for a user or service principal.
- `/access sessions` — list active sessions, expiry, and risk flags.

## 3) Drift Detection Plan
- **Orphan roles**
  - Detect roles with no bound users/services or unused for 30+ days.
- **Privilege creep**
  - Identify incremental permission additions without approved change records.
- **Expired debug sessions not revoked**
  - Validate break-glass sessions against TTL; auto-revoke on expiry.
- **RBAC mismatches**
  - Diff intended policy vs. effective permissions in runtime.

**Signals & Actions**
- Daily drift scan + on-change scan.
- Auto-remediation for expired sessions and orphan roles.
- Alerting to security channel with audit trail and rollback guidance.

## 4) IAM Structure
- **Separate service accounts per environment**
  - `inka-dev-*`, `inka-stage-*`, `inka-prod-*` with non-overlapping scopes.
- **Least privilege IAM**
  - Each role grants minimum required actions only.
  - No wildcard permissions on sensitive resources.
- **Secret access restricted by environment**
  - Environment-scoped secret stores and access policies.
- **Token rotation policy**
  - Automated rotation every 30 days; immediate rotation on incident.
  - Enforce short-lived tokens (<= 1 hour) for high-privilege roles.

## 5) Compliance Mapping
- **SOC 2**: CC6.1, CC6.2 (logical access), CC7.2 (monitoring), CC7.3 (response).
- **ISO 27001**: A.9 (access control), A.12 (operations security), A.16 (incident management).
- **NIST 800-53**: AC-2, AC-3, AC-6, AC-12, IA-5, AU-2, AU-6.

---

## Implementation Notes
- Enforce checks in bot handlers and backend services with centralized RBAC.
- All access decisions logged with user, role, resource, action, and reason.
- Store approvals and revocations with immutable audit logs.
