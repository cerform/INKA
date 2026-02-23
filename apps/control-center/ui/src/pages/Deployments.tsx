import React, { useState } from 'react';
import {
    Box, Paper, Typography, Table, TableHead, TableRow, TableCell, TableBody,
    Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
    TextField, MenuItem, Select, FormControl, InputLabel, CircularProgress,
    Alert, Tabs, Tab,
} from '@mui/material';
import { RotateCcw, Rocket } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { formatDistanceToNow } from 'date-fns';

const ENV_COLOR: Record<string, 'success' | 'primary' | 'warning' | 'error'> = {
    dev: 'primary',
    stage: 'warning',
    prod: 'success',
};

const Deployments: React.FC = () => {
    const [envTab, setEnvTab] = useState<string>('all');
    const [rollbackDialog, setRollbackDialog] = useState<{ open: boolean; serviceId: string; env: string } | null>(null);
    const [rollbackReason, setRollbackReason] = useState('');
    const qc = useQueryClient();

    const { data: deployments = [], isLoading } = useQuery({
        queryKey: ['deployments', envTab],
        queryFn: () => apiClient.getDeployments(envTab !== 'all' ? { env: envTab } : {}),
        refetchInterval: 15000,
    });

    const rollbackMutation = useMutation({
        mutationFn: () => apiClient.rollback({
            service_id: rollbackDialog!.serviceId,
            env: rollbackDialog!.env,
            reason: rollbackReason,
        }),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['deployments'] });
            setRollbackDialog(null);
            setRollbackReason('');
        },
    });

    return (
        <Box>
            <Typography variant="h4" fontWeight={700} mb={3}>Deployments</Typography>

            <Tabs
                value={envTab}
                onChange={(_, v) => setEnvTab(v)}
                sx={{ mb: 3, '& .MuiTabs-indicator': { bgcolor: 'primary.main' } }}
            >
                <Tab label="All" value="all" />
                <Tab label="Dev" value="dev" />
                <Tab label="Stage" value="stage" />
                <Tab label="Prod" value="prod" />
            </Tabs>

            <Paper>
                {isLoading && <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>}
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Service</TableCell>
                            <TableCell>Env</TableCell>
                            <TableCell>Image Digest</TableCell>
                            <TableCell>Revision</TableCell>
                            <TableCell>Traffic</TableCell>
                            <TableCell>Deployed By</TableCell>
                            <TableCell>Time</TableCell>
                            <TableCell align="right">Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {deployments.map(d => (
                            <TableRow key={d.id} hover sx={{ opacity: d.rollback_of ? 0.75 : 1 }}>
                                <TableCell>
                                    <Typography variant="body2" fontWeight={500}>{d.service_id.slice(0, 8)}…</Typography>
                                    {d.rollback_of && <Chip label="ROLLBACK" size="small" color="warning" sx={{ fontSize: '0.6rem', height: 16, mt: 0.5 }} />}
                                </TableCell>
                                <TableCell>
                                    <Chip label={d.env.toUpperCase()} size="small" color={ENV_COLOR[d.env] ?? 'default'} sx={{ fontWeight: 700 }} />
                                </TableCell>
                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'text.secondary' }}>
                                    {d.image_digest?.slice(0, 24) ?? '—'}…
                                </TableCell>
                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                                    {d.cloud_run_revision ?? '—'}
                                </TableCell>
                                <TableCell>
                                    {d.traffic_config
                                        ? Object.entries(d.traffic_config).map(([k, v]) => (
                                            <Chip key={k} label={`${k}: ${v}%`} size="small" sx={{ mr: 0.5, fontSize: '0.7rem' }} />
                                        ))
                                        : '—'}
                                </TableCell>
                                <TableCell>{d.deployed_by ?? '—'}</TableCell>
                                <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>
                                    {formatDistanceToNow(new Date(d.deployed_at), { addSuffix: true })}
                                </TableCell>
                                <TableCell align="right">
                                    <Button
                                        size="small"
                                        variant="outlined"
                                        color="warning"
                                        startIcon={<RotateCcw size={14} />}
                                        onClick={() => setRollbackDialog({ open: true, serviceId: d.service_id, env: d.env })}
                                    >
                                        Rollback
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                        {!isLoading && deployments.length === 0 && (
                            <TableRow><TableCell colSpan={8} sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>No deployments</TableCell></TableRow>
                        )}
                    </TableBody>
                </Table>
            </Paper>

            {/* Rollback Dialog */}
            <Dialog open={!!rollbackDialog?.open} onClose={() => setRollbackDialog(null)} maxWidth="sm" fullWidth>
                <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <RotateCcw size={20} color="#f59e0b" /> Rollback {rollbackDialog?.env?.toUpperCase()} Deployment
                </DialogTitle>
                <DialogContent>
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        This will trigger the rollback.yml GitHub Actions workflow.
                    </Alert>
                    <TextField
                        fullWidth label="Reason for rollback" multiline rows={3}
                        value={rollbackReason} onChange={e => setRollbackReason(e.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setRollbackDialog(null)}>Cancel</Button>
                    <Button
                        variant="contained" color="warning"
                        disabled={!rollbackReason || rollbackMutation.isPending}
                        onClick={() => rollbackMutation.mutate()}
                    >
                        {rollbackMutation.isPending ? <CircularProgress size={20} /> : 'Execute Rollback'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default Deployments;
