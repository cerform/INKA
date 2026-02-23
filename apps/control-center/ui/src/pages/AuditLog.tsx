import React, { useState } from 'react';
import {
    Box, Paper, Typography, Table, TableHead, TableRow, TableCell, TableBody,
    TextField, InputAdornment, Select, MenuItem, FormControl, InputLabel,
    Chip, CircularProgress, Tooltip,
} from '@mui/material';
import { Search } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { format } from 'date-fns';

const ACTION_COLOR: Record<string, string> = {
    'repo.register': '#6366f1',
    'service.register': '#8b5cf6',
    'run.trigger': '#06b6d4',
    'deployment.trigger': '#22c55e',
    'deployment.rollback': '#f59e0b',
    'approval.request': '#64748b',
    'approval.approve': '#22c55e',
    'approval.reject': '#ef4444',
    'webhook.workflow_run': '#94a3b8',
};

const AuditLog: React.FC = () => {
    const [search, setSearch] = useState('');
    const [actionFilter, setActionFilter] = useState('');

    const { data: entries = [], isLoading } = useQuery({
        queryKey: ['audit', actionFilter],
        queryFn: () => apiClient.getAuditLog(actionFilter ? { action: actionFilter } : {}),
        refetchInterval: 30000,
    });

    const filtered = entries.filter(e =>
        e.actor.toLowerCase().includes(search.toLowerCase()) ||
        e.action.toLowerCase().includes(search.toLowerCase()) ||
        (e.target_id ?? '').toLowerCase().includes(search.toLowerCase())
    );

    const uniqueActions = [...new Set(entries.map(e => e.action.split('.')[0]))];

    return (
        <Box>
            <Typography variant="h4" fontWeight={700} mb={3}>Audit Log</Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
                <TextField
                    size="small"
                    placeholder="Search actor, action, target..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    InputProps={{ startAdornment: <InputAdornment position="start"><Search size={16} /></InputAdornment> }}
                    sx={{ minWidth: 280 }}
                />
                <FormControl size="small" sx={{ minWidth: 160 }}>
                    <InputLabel>Category</InputLabel>
                    <Select value={actionFilter} label="Category" onChange={e => setActionFilter(e.target.value)}>
                        <MenuItem value="">All</MenuItem>
                        {uniqueActions.map(a => <MenuItem key={a} value={a}>{a}</MenuItem>)}
                    </Select>
                </FormControl>
            </Box>

            <Paper>
                {isLoading && <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>}
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Timestamp</TableCell>
                            <TableCell>Actor</TableCell>
                            <TableCell>Action</TableCell>
                            <TableCell>Target</TableCell>
                            <TableCell>Details</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filtered.map(entry => (
                            <TableRow key={entry.id} hover>
                                <TableCell sx={{ color: 'text.secondary', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                                    {format(new Date(entry.timestamp), 'PP HH:mm:ss')}
                                </TableCell>
                                <TableCell>
                                    <Typography variant="body2" fontWeight={500}>{entry.actor}</Typography>
                                </TableCell>
                                <TableCell>
                                    <Chip
                                        label={entry.action}
                                        size="small"
                                        sx={{
                                            fontSize: '0.7rem',
                                            fontFamily: 'monospace',
                                            bgcolor: `${ACTION_COLOR[entry.action] ?? '#64748b'}22`,
                                            color: ACTION_COLOR[entry.action] ?? '#94a3b8',
                                            border: `1px solid ${ACTION_COLOR[entry.action] ?? '#64748b'}44`,
                                        }}
                                    />
                                </TableCell>
                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'text.secondary' }}>
                                    {entry.target_type && `${entry.target_type}:`}
                                    {entry.target_id?.slice(0, 12)}
                                    {entry.target_id && '…'}
                                </TableCell>
                                <TableCell>
                                    {entry.details_json && Object.keys(entry.details_json).length > 0 && (
                                        <Tooltip title={<pre style={{ fontSize: '0.75rem', margin: 0 }}>{JSON.stringify(entry.details_json, null, 2)}</pre>}>
                                            <Chip label="details" size="small" sx={{ fontSize: '0.65rem', cursor: 'help' }} />
                                        </Tooltip>
                                    )}
                                </TableCell>
                            </TableRow>
                        ))}
                        {!isLoading && filtered.length === 0 && (
                            <TableRow><TableCell colSpan={5} sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>No audit entries</TableCell></TableRow>
                        )}
                    </TableBody>
                </Table>
            </Paper>
        </Box>
    );
};

export default AuditLog;
