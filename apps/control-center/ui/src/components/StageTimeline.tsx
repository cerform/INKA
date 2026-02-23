import React from 'react';
import { Box, Typography, Tooltip, CircularProgress } from '@mui/material';
import { CheckCircle, XCircle, Clock, Circle, Ban } from 'lucide-react';

export interface Stage {
    name: string;
    status: string;
    duration_seconds?: number;
}

const ICON_MAP: Record<string, React.ReactNode> = {
    success: <CheckCircle size={18} color="#22c55e" />,
    failure: <XCircle size={18} color="#ef4444" />,
    in_progress: <CircularProgress size={16} thickness={5} sx={{ color: '#6366f1' }} />,
    queued: <Clock size={18} color="#94a3b8" />,
    cancelled: <Ban size={18} color="#64748b" />,
};

const STAGE_LABELS: Record<string, string> = {
    lint: 'Lint',
    test: 'Test',
    build: 'Build',
    scan: 'Scan',
    sbom: 'SBOM',
    push: 'Push',
    deploy: 'Deploy',
};

interface StageTimelineProps {
    stages: Stage[];
}

const StageTimeline: React.FC<StageTimelineProps> = ({ stages }) => {
    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0, flexWrap: 'wrap' }}>
            {stages.map((stage, idx) => (
                <React.Fragment key={stage.name}>
                    <Tooltip
                        title={
                            stage.duration_seconds
                                ? `${STAGE_LABELS[stage.name] ?? stage.name}: ${stage.duration_seconds}s`
                                : STAGE_LABELS[stage.name] ?? stage.name
                        }
                    >
                        <Box
                            sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: 0.5,
                                px: 1,
                                py: 0.5,
                                borderRadius: 2,
                                cursor: 'default',
                                minWidth: 60,
                                '&:hover': { bgcolor: 'rgba(99,102,241,0.08)' },
                            }}
                        >
                            {ICON_MAP[stage.status] ?? <Circle size={18} color="#64748b" />}
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem' }}>
                                {STAGE_LABELS[stage.name] ?? stage.name}
                            </Typography>
                        </Box>
                    </Tooltip>
                    {idx < stages.length - 1 && (
                        <Box sx={{ width: 24, height: 2, bgcolor: 'rgba(255,255,255,0.1)', flexShrink: 0 }} />
                    )}
                </React.Fragment>
            ))}
        </Box>
    );
};

export default StageTimeline;
