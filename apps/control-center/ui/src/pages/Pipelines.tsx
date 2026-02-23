import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box, Paper, Typography, TextField, InputAdornment, MenuItem, Select,
    Table, TableHead, TableRow, TableCell, TableBody, IconButton, Tooltip,
    FormControl, InputLabel, CircularProgress,
} from '@mui/material';
import { Search, ExternalLink } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import StatusChip from '../components/StatusChip';
import StageTimeline from '../components/StageTimeline';
import { formatDistanceToNow } from 'date-fns';

const Pipelines: React.FC = () => {
    const navigate = useNavigate();
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [envFilter, setEnvFilter] = useState('');

    const { data: runs = [], isLoading } = useQuery({
        queryKey: ['runs', statusFilter],
        queryFn: () => apiClient.getRuns(statusFilter ? { status: statusFilter } : {}),
        refetchInterval: 10000,
    });

    const filtered = runs.filter(r => {
        const sha = r.commit_sha ?? '';
        const actor = r.actor ?? '';
        return (
            sha.toLowerCase().includes(search.toLowerCase()) ||
            actor.toLowerCase().includes(search.toLowerCase())
        );
    });

    return (
        <Box>
            <Typography variant="h4" fontWeight={700} mb={3}>Pipelines</Typography>

            {/* Filters */}
            <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
                <TextField
                    size="small"
                    placeholder="Search by commit / actor..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    InputProps={{ startAdornment: <InputAdornment position="start"><Search size={16} /></InputAdornment> }}
                    sx={{ minWidth: 260 }}
                />
                <FormControl size="small" sx={{ minWidth: 140 }}>
                    <InputLabel>Status</InputLabel>
                    <Select value={statusFilter} label="Status" onChange={e => setStatusFilter(e.target.value)}>
                        <MenuItem value="">All</MenuItem>
                        <MenuItem value="success">Success</MenuItem>
                        <MenuItem value="in_progress">Running</MenuItem>
                        <MenuItem value="failure">Failed</MenuItem>
                        <MenuItem value="queued">Queued</MenuItem>
                        <MenuItem value="cancelled">Cancelled</MenuItem>
                    </Select>
                </FormControl>
            </Box>

            <Paper>
                {isLoading && <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>}
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Status</TableCell>
                            <TableCell>Commit</TableCell>
                            <TableCell>Actor</TableCell>
                            <TableCell>Stages</TableCell>
                            <TableCell>Image</TableCell>
                            <TableCell>Started</TableCell>
                            <TableCell align="right">Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {filtered.map(run => (
                            <TableRow
                                key={run.id}
                                hover
                                sx={{ cursor: 'pointer' }}
                                onClick={() => navigate(`/pipelines/${run.id}`)}
                            >
                                <TableCell><StatusChip status={run.status} /></TableCell>
                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                    {run.commit_sha?.slice(0, 7) ?? '—'}
                                </TableCell>
                                <TableCell>{run.actor ?? '—'}</TableCell>
                                <TableCell>
                                    {run.stage_json?.length
                                        ? <StageTimeline stages={run.stage_json} />
                                        : <Typography variant="caption" color="text.secondary">—</Typography>
                                    }
                                </TableCell>
                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.7rem', color: 'text.secondary' }}>
                                    {run.image_digest?.slice(0, 20) ?? '—'}
                                </TableCell>
                                <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>
                                    {run.started_at
                                        ? formatDistanceToNow(new Date(run.started_at), { addSuffix: true })
                                        : '—'}
                                </TableCell>
                                <TableCell align="right">
                                    {run.github_run_id && (
                                        <Tooltip title="View on GitHub">
                                            <IconButton
                                                size="small"
                                                onClick={e => { e.stopPropagation(); window.open(`https://github.com/actions/runs/${run.github_run_id}`, '_blank'); }}
                                            >
                                                <ExternalLink size={16} />
                                            </IconButton>
                                        </Tooltip>
                                    )}
                                </TableCell>
                            </TableRow>
                        ))}
                        {!isLoading && filtered.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                                    No pipeline runs found
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </Paper>
        </Box>
    );
};

export default Pipelines;
