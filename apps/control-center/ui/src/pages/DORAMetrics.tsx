import React, { useState } from 'react';
import {
    Box, Paper, Typography, Grid, CircularProgress, Alert,
    ToggleButtonGroup, ToggleButton, Divider, LinearProgress,
} from '@mui/material';
import { Activity, Zap, Timer, AlertTriangle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { DORAMetrics } from '../api/client';

const PERIODS = [7, 30, 90];

interface MetricCardProps {
    title: string;
    value: string | number;
    unit: string;
    icon: React.ReactNode;
    color: string;
    description: string;
    quality?: 'elite' | 'high' | 'medium' | 'low';
}

const QUALITY_COLOR: Record<string, string> = {
    elite: '#22c55e',
    high: '#6366f1',
    medium: '#f59e0b',
    low: '#ef4444',
};

const MetricCard: React.FC<MetricCardProps> = ({ title, value, unit, icon, color, description, quality }) => (
    <Paper sx={{ p: 3, height: '100%', position: 'relative', overflow: 'hidden' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', textTransform: 'uppercase', letterSpacing: 1 }}>
                    {title}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5, mt: 0.5 }}>
                    <Typography variant="h3" sx={{ fontWeight: 800, color }}>{value}</Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>{unit}</Typography>
                </Box>
                {quality && (
                    <Typography variant="caption" sx={{ color: QUALITY_COLOR[quality], fontWeight: 600, mt: 0.5, display: 'block' }}>
                        {quality.toUpperCase()} performer
                    </Typography>
                )}
            </Box>
            <Box sx={{ color, opacity: 0.8 }}>{icon}</Box>
        </Box>
        <Divider sx={{ my: 1.5, borderColor: 'rgba(255,255,255,0.06)' }} />
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>{description}</Typography>
    </Paper>
);

function freqQuality(freq: number): MetricCardProps['quality'] {
    if (freq >= 1) return 'elite';
    if (freq >= 1 / 7) return 'high';
    if (freq >= 1 / 30) return 'medium';
    return 'low';
}

function cfrQuality(rate: number): MetricCardProps['quality'] {
    if (rate <= 0.05) return 'elite';
    if (rate <= 0.1) return 'high';
    if (rate <= 0.15) return 'medium';
    return 'low';
}

const DORAMetricsPage: React.FC = () => {
    const [period, setPeriod] = useState(30);

    const { data: metrics, isLoading, error } = useQuery<DORAMetrics>({
        queryKey: ['dora', period],
        queryFn: () => apiClient.getDORAMetrics(period),
        refetchInterval: 60000,
    });

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Box>
                    <Typography variant="h4" fontWeight={700}>DORA Metrics</Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
                        DevOps Research &amp; Assessment performance indicators
                    </Typography>
                </Box>
                <ToggleButtonGroup
                    value={period}
                    exclusive
                    onChange={(_, v) => v && setPeriod(v)}
                    size="small"
                >
                    {PERIODS.map(p => <ToggleButton key={p} value={p}>{p}d</ToggleButton>)}
                </ToggleButtonGroup>
            </Box>

            {isLoading && <CircularProgress />}
            {error && <Alert severity="error">Failed to load DORA metrics</Alert>}

            {metrics && (
                <>
                    <Grid container spacing={3} mb={4}>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <MetricCard
                                title="Deployment Frequency"
                                value={metrics.deployment_frequency < 1
                                    ? `${(metrics.deployment_frequency * period).toFixed(0)}`
                                    : metrics.deployment_frequency.toFixed(1)}
                                unit={metrics.deployment_frequency < 1 ? `/ ${period}d` : 'per day'}
                                icon={<Zap size={28} />}
                                color="#6366f1"
                                description={metrics.deployment_frequency_label}
                                quality={freqQuality(metrics.deployment_frequency)}
                            />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <MetricCard
                                title="Lead Time for Changes"
                                value={metrics.lead_time_hours.toFixed(1)}
                                unit="hours"
                                icon={<Timer size={28} />}
                                color="#22c55e"
                                description="Commit to production deployment"
                                quality={metrics.lead_time_hours < 1 ? 'elite' : metrics.lead_time_hours < 24 ? 'high' : metrics.lead_time_hours < 168 ? 'medium' : 'low'}
                            />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <MetricCard
                                title="MTTR"
                                value={metrics.mean_time_to_restore_hours.toFixed(1)}
                                unit="hours"
                                icon={<Activity size={28} />}
                                color="#f59e0b"
                                description="Mean time to restore after incident"
                                quality={metrics.mean_time_to_restore_hours < 1 ? 'elite' : metrics.mean_time_to_restore_hours < 24 ? 'high' : 'medium'}
                            />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                            <MetricCard
                                title="Change Failure Rate"
                                value={`${(metrics.change_failure_rate * 100).toFixed(1)}`}
                                unit="%"
                                icon={<AlertTriangle size={28} />}
                                color={cfrQuality(metrics.change_failure_rate) === 'elite' ? '#22c55e' : '#ef4444'}
                                description="Deployments causing rollback"
                                quality={cfrQuality(metrics.change_failure_rate)}
                            />
                        </Grid>
                    </Grid>

                    {/* Summary Stats */}
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" fontWeight={600} mb={2}>
                            Summary — Last {period} days
                        </Typography>
                        <Grid container spacing={3}>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography variant="body2" color="text.secondary">Total Deployments</Typography>
                                <Typography variant="h5" fontWeight={700}>{metrics.total_deployments}</Typography>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography variant="body2" color="text.secondary">Rollbacks</Typography>
                                <Typography variant="h5" fontWeight={700} color="warning.main">{metrics.rollbacks}</Typography>
                            </Grid>
                            <Grid size={{ xs: 12, sm: 4 }}>
                                <Typography variant="body2" color="text.secondary">Success Rate</Typography>
                                <Typography variant="h5" fontWeight={700} color="success.main">
                                    {metrics.total_deployments > 0
                                        ? `${(((metrics.total_deployments - metrics.rollbacks) / metrics.total_deployments) * 100).toFixed(1)}%`
                                        : 'N/A'}
                                </Typography>
                            </Grid>
                        </Grid>
                        <Box sx={{ mt: 2 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                                Deployment success rate
                            </Typography>
                            <LinearProgress
                                variant="determinate"
                                value={metrics.total_deployments > 0
                                    ? ((metrics.total_deployments - metrics.rollbacks) / metrics.total_deployments) * 100
                                    : 0}
                                sx={{ height: 8, borderRadius: 4, bgcolor: 'rgba(255,255,255,0.06)', '& .MuiLinearProgress-bar': { bgcolor: '#22c55e' } }}
                            />
                        </Box>
                    </Paper>
                </>
            )}
        </Box>
    );
};

export default DORAMetricsPage;
