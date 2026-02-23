import React from 'react';
import {
    Box, Grid, Paper, Typography, Chip, CircularProgress, Alert,
    Table, TableHead, TableBody, TableRow, TableCell,
} from '@mui/material';
import { Activity, CheckCircle, Clock, AlertTriangle, Rocket, ShieldCheck } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import StatusChip from '../components/StatusChip';
import { formatDistanceToNow } from 'date-fns';

const StatCard: React.FC<{
    title: string; value: number | string; icon: React.ReactNode;
    color: string; subtitle?: string;
}> = ({ title, value, icon, color, subtitle }) => (
    <Paper sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 1, position: 'relative', overflow: 'hidden' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
                <Typography variant="body2" sx={{ color: 'text.secondary', mb: 0.5 }}>{title}</Typography>
                <Typography variant="h3" sx={{ fontWeight: 800, color }}>{value}</Typography>
                {subtitle && <Typography variant="caption" sx={{ color: 'text.secondary' }}>{subtitle}</Typography>}
            </Box>
            <Box sx={{ color, opacity: 0.8 }}>{icon}</Box>
        </Box>
        <Box sx={{
            position: 'absolute', right: -20, bottom: -20, opacity: 0.05,
            transform: 'scale(4)', color,
        }}>
            {icon}
        </Box>
    </Paper>
);

const Dashboard: React.FC = () => {
    const { data: runs = [], isLoading: runsLoading } = useQuery({
        queryKey: ['runs'],
        queryFn: () => apiClient.getRuns({}),
        refetchInterval: 15000,
    });
    const { data: approvals = [] } = useQuery({
        queryKey: ['approvals'],
        queryFn: () => apiClient.getApprovals({ status: 'pending' }),
        refetchInterval: 15000,
    });
    const { data: deployments = [] } = useQuery({
        queryKey: ['deployments'],
        queryFn: () => apiClient.getDeployments({}),
        refetchInterval: 15000,
    });

    const active = runs.filter(r => r.status === 'in_progress').length;
    const failed = runs.filter(r => r.status === 'failure').length;
    const success = runs.filter(r => r.status === 'success').length;

    return (
        <Box>
            <Typography variant="h4" fontWeight={700} mb={3}>Dashboard</Typography>

            {runsLoading && <CircularProgress size={24} sx={{ mb: 2 }} />}

            <Grid container spacing={2} mb={4}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard title="Active Runs" value={active} icon={<Activity size={28} />} color="#6366f1" />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard title="Successful Runs" value={success} icon={<CheckCircle size={28} />} color="#22c55e" />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard title="Failed Runs" value={failed} icon={<AlertTriangle size={28} />} color="#ef4444" />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Pending Approvals" value={approvals.length}
                        icon={<ShieldCheck size={28} />} color="#f59e0b"
                        subtitle="Require action"
                    />
                </Grid>
            </Grid>

            {approvals.length > 0 && (
                <Alert severity="warning" sx={{ mb: 3, borderRadius: 2 }}>
                    {approvals.length} deployment{approvals.length > 1 ? 's' : ''} pending approval
                </Alert>
            )}

            <Grid container spacing={3}>
                <Grid item xs={12} lg={8}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2}>Recent Runs</Typography>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Status</TableCell>
                                    <TableCell>Commit</TableCell>
                                    <TableCell>Actor</TableCell>
                                    <TableCell>Started</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {runs.slice(0, 10).map(run => (
                                    <TableRow key={run.id} hover>
                                        <TableCell><StatusChip status={run.status} /></TableCell>
                                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                                            {run.commit_sha?.slice(0, 7) ?? '—'}
                                        </TableCell>
                                        <TableCell>{run.actor ?? '—'}</TableCell>
                                        <TableCell sx={{ color: 'text.secondary', fontSize: '0.8rem' }}>
                                            {run.started_at
                                                ? formatDistanceToNow(new Date(run.started_at), { addSuffix: true })
                                                : '—'}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </Paper>
                </Grid>
                <Grid item xs={12} lg={4}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2}>Recent Deployments</Typography>
                        {deployments.slice(0, 5).map(d => (
                            <Box key={d.id} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                                <Box>
                                    <Typography variant="body2" fontWeight={500}>{d.service_id.slice(0, 8)}…</Typography>
                                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>{d.env}</Typography>
                                </Box>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    {d.rollback_of && <Chip label="ROL" size="small" color="warning" sx={{ fontSize: '0.6rem', height: 18 }} />}
                                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                        {formatDistanceToNow(new Date(d.deployed_at), { addSuffix: true })}
                                    </Typography>
                                </Box>
                            </Box>
                        ))}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default Dashboard;
