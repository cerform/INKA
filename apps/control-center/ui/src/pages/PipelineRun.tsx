import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box, Paper, Typography, Grid, Divider, Button, Chip, CircularProgress,
    Alert,
} from '@mui/material';
import { ArrowLeft, ExternalLink, Package, FileText, TestTube, Image } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { formatDistanceToNow, format } from 'date-fns';
import StatusChip from '../components/StatusChip';
import StageTimeline from '../components/StageTimeline';

const InfoRow: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
    <Box sx={{ display: 'flex', gap: 2, py: 1, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <Typography sx={{ color: 'text.secondary', minWidth: 160, fontSize: '0.875rem' }}>{label}</Typography>
        <Typography sx={{ fontSize: '0.875rem', wordBreak: 'break-all' }}>{value}</Typography>
    </Box>
);

const PipelineRun: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const { data: run, isLoading, error } = useQuery({
        queryKey: ['run', id],
        queryFn: () => apiClient.getRun(id!),
        enabled: !!id,
        refetchInterval: run => run?.status === 'in_progress' ? 5000 : false,
    });

    if (isLoading) return <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>;
    if (error || !run) return <Alert severity="error">Run not found</Alert>;

    const duration = run.started_at && run.finished_at
        ? Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000)
        : null;

    return (
        <Box>
            <Button
                startIcon={<ArrowLeft size={16} />}
                onClick={() => navigate('/pipelines')}
                sx={{ mb: 2, color: 'text.secondary' }}
                variant="text"
            >
                Back to Pipelines
            </Button>

            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <StatusChip status={run.status} size="medium" />
                <Typography variant="h5" fontWeight={700}>
                    Run {run.id.slice(0, 8)}
                </Typography>
                {run.github_run_id && (
                    <Button
                        size="small"
                        endIcon={<ExternalLink size={14} />}
                        href={`https://github.com/actions/runs/${run.github_run_id}`}
                        target="_blank"
                        variant="outlined"
                    >
                        View on GitHub
                    </Button>
                )}
            </Box>

            <Grid container spacing={3}>
                {/* Stage Timeline */}
                <Grid item xs={12}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2}>Stage Timeline</Typography>
                        {run.stage_json?.length ? (
                            <StageTimeline stages={run.stage_json} />
                        ) : (
                            <Typography color="text.secondary" variant="body2">No stage data available yet</Typography>
                        )}
                    </Paper>
                </Grid>

                {/* Run Details */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2}>Run Details</Typography>
                        <InfoRow label="Commit SHA" value={
                            <code style={{ fontSize: '0.85rem' }}>{run.commit_sha ?? '—'}</code>
                        } />
                        <InfoRow label="Actor" value={run.actor ?? '—'} />
                        <InfoRow label="Started" value={run.started_at ? format(new Date(run.started_at), 'PPpp') : '—'} />
                        <InfoRow label="Finished" value={run.finished_at ? format(new Date(run.finished_at), 'PPpp') : 'Still running'} />
                        <InfoRow label="Duration" value={duration ? `${duration}s` : '—'} />
                        <InfoRow label="GitHub Run ID" value={run.github_run_id ?? '—'} />
                    </Paper>
                </Grid>

                {/* Artifacts */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2}>Artifacts</Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)' }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                    <Image size={16} color="#6366f1" />
                                    <Typography variant="body2" fontWeight={600}>Image Digest</Typography>
                                </Box>
                                <Typography variant="caption" sx={{ fontFamily: 'monospace', wordBreak: 'break-all', color: 'text.secondary' }}>
                                    {run.image_digest ?? 'Not available'}
                                </Typography>
                            </Box>
                            {run.sbom_ref && (
                                <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.2)' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                        <Package size={16} color="#22c55e" />
                                        <Typography variant="body2" fontWeight={600}>SBOM</Typography>
                                    </Box>
                                    <Button size="small" href={run.sbom_ref} target="_blank" endIcon={<ExternalLink size={12} />}>
                                        View SBOM
                                    </Button>
                                </Box>
                            )}
                            {run.test_report_ref && (
                                <Box sx={{ p: 2, borderRadius: 2, bgcolor: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                        <TestTube size={16} color="#f59e0b" />
                                        <Typography variant="body2" fontWeight={600}>Test Report</Typography>
                                    </Box>
                                    <Button size="small" href={run.test_report_ref} target="_blank" endIcon={<ExternalLink size={12} />}>
                                        View Report
                                    </Button>
                                </Box>
                            )}
                        </Box>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default PipelineRun;
