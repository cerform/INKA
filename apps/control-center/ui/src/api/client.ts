import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export const api = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
});

// Types
export interface Repo {
    id: string;
    owner: string;
    name: string;
    default_branch: string;
    created_at: string;
}

export interface Service {
    id: string;
    repo_id: string;
    service_name: string;
    cloud_run_service: string;
    env: 'dev' | 'stage' | 'prod';
    created_at: string;
}

export interface StageInfo {
    name: string;
    status: string;
    started_at?: string;
    finished_at?: string;
    duration_seconds?: number;
}

export interface PipelineRun {
    id: string;
    repo_id: string;
    service_id?: string;
    github_run_id?: string;
    commit_sha?: string;
    status: 'queued' | 'in_progress' | 'success' | 'failure' | 'cancelled';
    started_at?: string;
    finished_at?: string;
    actor?: string;
    stage_json?: StageInfo[];
    image_digest?: string;
    sbom_ref?: string;
    test_report_ref?: string;
    created_at: string;
}

export interface Deployment {
    id: string;
    service_id: string;
    env: string;
    image_digest: string;
    cloud_run_revision?: string;
    traffic_config?: Record<string, number>;
    deployed_at: string;
    deployed_by?: string;
    rollback_of?: string;
}

export interface Approval {
    id: string;
    deployment_id: string;
    env: string;
    status: 'pending' | 'approved' | 'rejected';
    requested_by: string;
    approved_by?: string;
    approved_at?: string;
    reason?: string;
    created_at: string;
}

export interface AuditEntry {
    id: string;
    actor: string;
    action: string;
    target_type?: string;
    target_id?: string;
    timestamp: string;
    details_json?: Record<string, unknown>;
}

export interface DORAMetrics {
    period_days: number;
    deployment_frequency: number;
    deployment_frequency_label: string;
    lead_time_hours: number;
    mean_time_to_restore_hours: number;
    change_failure_rate: number;
    total_deployments: number;
    failed_deployments: number;
    rollbacks: number;
}

// API methods
export const apiClient = {
    // Repos
    getRepos: () => api.get<Repo[]>('/api/repos').then(r => r.data),
    registerRepo: (owner: string, name: string, defaultBranch = 'main') =>
        api.post<Repo>('/api/repos/register', { owner, name, default_branch: defaultBranch }).then(r => r.data),

    // Services
    getServices: (params?: { repo_id?: string; env?: string }) =>
        api.get<Service[]>('/api/services', { params }).then(r => r.data),

    // Runs
    getRuns: (params?: { repo_id?: string; service_id?: string; status?: string }) =>
        api.get<PipelineRun[]>('/api/runs', { params }).then(r => r.data),
    getRun: (id: string) => api.get<PipelineRun>(`/api/runs/${id}`).then(r => r.data),

    // Deployments
    getDeployments: (params?: { service_id?: string; env?: string }) =>
        api.get<Deployment[]>('/api/deployments', { params }).then(r => r.data),
    deploy: (payload: { service_id: string; env: string; image_digest: string }) =>
        api.post<Deployment>('/api/deploy', payload).then(r => r.data),
    rollback: (payload: { service_id: string; env: string; to_revision?: string; reason: string }) =>
        api.post<Deployment>('/api/rollback', payload).then(r => r.data),

    // Approvals
    getApprovals: (params?: { status?: string; env?: string }) =>
        api.get<Approval[]>('/api/approvals', { params }).then(r => r.data),
    requestApproval: (deployment_id: string, env: string, requested_by: string) =>
        api.post<Approval>('/api/approvals/request', { deployment_id, env, requested_by }).then(r => r.data),
    approveApproval: (id: string, reason?: string) =>
        api.post<Approval>(`/api/approvals/${id}/approve`, { reason }).then(r => r.data),
    rejectApproval: (id: string, reason?: string) =>
        api.post<Approval>(`/api/approvals/${id}/reject`, { reason }).then(r => r.data),

    // Audit
    getAuditLog: (params?: { actor?: string; action?: string; since?: string }) =>
        api.get<AuditEntry[]>('/api/audit', { params }).then(r => r.data),

    // DORA
    getDORAMetrics: (period_days = 30) =>
        api.get<DORAMetrics>('/api/dora/metrics', { params: { period_days } }).then(r => r.data),

    // Health
    health: () => api.get('/health').then(r => r.data),
};
