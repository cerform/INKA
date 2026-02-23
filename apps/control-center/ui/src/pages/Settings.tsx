import React, { useState } from 'react';
import {
    Box, Paper, Typography, TextField, Button, Table, TableHead, TableRow,
    TableCell, TableBody, Chip, Grid, Alert, CircularProgress, Divider,
} from '@mui/material';
import { Plus, DatabaseZap } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';

const Settings: React.FC = () => {
    const [repoOwner, setRepoOwner] = useState('');
    const [repoName, setRepoName] = useState('');
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const qc = useQueryClient();

    const { data: repos = [], isLoading: reposLoading } = useQuery({
        queryKey: ['repos'],
        queryFn: () => apiClient.getRepos(),
    });

    const { data: services = [] } = useQuery({
        queryKey: ['services'],
        queryFn: () => apiClient.getServices(),
    });

    const registerRepo = useMutation({
        mutationFn: () => apiClient.registerRepo(repoOwner, repoName),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['repos'] });
            setRepoOwner(''); setRepoName('');
            setMessage({ type: 'success', text: `Repository ${repoOwner}/${repoName} registered` });
        },
        onError: (e: unknown) => {
            const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setMessage({ type: 'error', text: msg ?? 'Failed to register repository' });
        },
    });

    return (
        <Box>
            <Typography variant="h4" fontWeight={700} mb={3}>Settings</Typography>

            {message && (
                <Alert severity={message.type} sx={{ mb: 3 }} onClose={() => setMessage(null)}>
                    {message.text}
                </Alert>
            )}

            <Grid container spacing={3}>
                {/* Register Repo */}
                <Grid size={{ xs: 12, md: 6 }}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Plus size={18} /> Register Repository
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <TextField size="small" label="Owner (GitHub org/user)" value={repoOwner} onChange={e => setRepoOwner(e.target.value)} />
                            <TextField size="small" label="Repository name" value={repoName} onChange={e => setRepoName(e.target.value)} />
                            <Button
                                variant="contained"
                                disabled={!repoOwner || !repoName || registerRepo.isPending}
                                onClick={() => registerRepo.mutate()}
                            >
                                {registerRepo.isPending ? <CircularProgress size={20} /> : 'Register'}
                            </Button>
                        </Box>
                    </Paper>
                </Grid>

                {/* Repo List */}
                <Grid size={{ xs: 12, md: 6 }}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2}>Registered Repositories</Typography>
                        {reposLoading ? <CircularProgress size={24} /> : (
                            repos.length === 0
                                ? <Typography color="text.secondary" variant="body2">No repositories registered</Typography>
                                : repos.map(repo => (
                                    <Box key={repo.id} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                                        <Box>
                                            <Typography variant="body2" fontWeight={500}>{repo.owner}/{repo.name}</Typography>
                                            <Typography variant="caption" color="text.secondary">Branch: {repo.default_branch}</Typography>
                                        </Box>
                                        <Chip label={repo.id.slice(0, 8)} size="small" sx={{ fontFamily: 'monospace', fontSize: '0.65rem' }} />
                                    </Box>
                                ))
                        )}
                    </Paper>
                </Grid>

                {/* Services */}
                <Grid size={{ xs: 12 }}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <DatabaseZap size={18} /> Service Mappings (Repo → Cloud Run)
                        </Typography>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Service Name</TableCell>
                                    <TableCell>Cloud Run Service</TableCell>
                                    <TableCell>Environment</TableCell>
                                    <TableCell>Repo ID</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {services.map(svc => (
                                    <TableRow key={svc.id} hover>
                                        <TableCell sx={{ fontWeight: 500 }}>{svc.service_name}</TableCell>
                                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{svc.cloud_run_service}</TableCell>
                                        <TableCell>
                                            <Chip label={svc.env.toUpperCase()} size="small"
                                                color={svc.env === 'prod' ? 'success' : svc.env === 'stage' ? 'warning' : 'primary'}
                                                sx={{ fontWeight: 700 }}
                                            />
                                        </TableCell>
                                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'text.secondary' }}>
                                            {svc.repo_id.slice(0, 8)}…
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {services.length === 0 && (
                                    <TableRow><TableCell colSpan={4} sx={{ textAlign: 'center', py: 3, color: 'text.secondary' }}>No services registered</TableCell></TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </Paper>
                </Grid>

                {/* Env / Secrets info */}
                <Grid size={{ xs: 12 }}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2}>Environment Configuration</Typography>
                        <Alert severity="info" sx={{ mb: 2 }}>
                            Secrets are managed via <strong>Google Secret Manager</strong>. No plaintext secrets are stored in this UI or in environment variables.
                        </Alert>
                        <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.06)' }} />
                        <Typography variant="body2" color="text.secondary" mb={1}>Required secrets in Secret Manager:</Typography>
                        {[
                            'DATABASE_URL — Control Center Cloud SQL connection string',
                            'GITHUB_TOKEN — GitHub PAT with repo + workflow permissions',
                            'GITHUB_WEBHOOK_SECRET — Shared secret for HMAC webhook validation',
                            'GCP_PROJECT_ID — GCP project for Cloud Run & Artifact Registry',
                        ].map(s => (
                            <Box key={s} sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.5 }}>
                                <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main', flexShrink: 0 }} />
                                <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>{s}</Typography>
                            </Box>
                        ))}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default Settings;
