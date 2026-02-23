import React from 'react';
import { Chip } from '@mui/material';

type Status = 'success' | 'in_progress' | 'queued' | 'failure' | 'cancelled' | 'pending' | 'approved' | 'rejected' | string;

const STATUS_MAP: Record<string, { label: string; color: 'success' | 'primary' | 'warning' | 'error' | 'default' }> = {
    success: { label: 'Success', color: 'success' },
    approved: { label: 'Approved', color: 'success' },
    in_progress: { label: 'Running', color: 'primary' },
    queued: { label: 'Queued', color: 'warning' },
    failure: { label: 'Failed', color: 'error' },
    cancelled: { label: 'Cancelled', color: 'default' },
    pending: { label: 'Pending', color: 'warning' },
    rejected: { label: 'Rejected', color: 'error' },
};

interface StatusChipProps {
    status: Status;
    size?: 'small' | 'medium';
}

const StatusChip: React.FC<StatusChipProps> = ({ status, size = 'small' }) => {
    const config = STATUS_MAP[status] ?? { label: status.toUpperCase(), color: 'default' as const };
    return (
        <Chip
            label={config.label}
            color={config.color}
            size={size}
            sx={{ fontWeight: 700, fontSize: '0.7rem' }}
        />
    );
};

export default StatusChip;
