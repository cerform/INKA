import React, { useState } from 'react';
import {
    Box, Paper, Typography, Table, TableHead, TableRow, TableCell, TableBody,
    Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
    CircularProgress, Alert, Chip,
} from '@mui/material';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { formatDistanceToNow, format } from 'date-fns';
import StatusChip from '../components/StatusChip';

const Approvals: React.FC = () => {
    const [actionDialog, setActionDialog] = useState<{
        id: string; type: 'approve' | 'reject'; env: string;
    } | null>(null);
    const [reason, setReason] = useState('');
    const qc = useQueryClient();

    const { data: pending = [], isLoading: pendingLoading } = useQuery({
        queryKey: ['approvals', 'pending'],
        queryFn: () => apiClient.getApprovals({ status: 'pending' }),
        refetchInterval: 10000,
    });

    const { data: history = [] } = useQuery({
        queryKey: ['approvals', 'all'],
        queryFn: () => apiClient.getApprovals({}),
        refetchInterval: 30000,
    });

    const approveMutation = useMutation({
        mutationFn: ({ id, type, reason }: { id: string; type: 'approve' | 'reject'; reason?: string }) =>
            type === 'approve' ? apiClient.approveApproval(id, reason) : apiClient.rejectApproval(id, reason),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['approvals'] });
            setActionDialog(null);
            setReason('');
        },
    });

    return (
        <Box>
            <Typography variant="h4" fontWeight={700} mb={3}>Approvals</Typography>

            {pending.length > 0 && (
                <Alert
                    severity="warning"
                    icon={<Clock size={20} />}
                    sx={{ mb: 3, borderRadius: 2 }}
                >
                    {pending.length} deployment{pending.length > 1 ? 's' : ''} require{pending.length === 1 ? 's' : ''} approval
                </Alert>
            )}

            {/* Pending Approvals */}
            <Paper sx={{ mb: 4 }}>
                <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <Typography variant="h6" fontWeight={600}>Pending Approvals</Typography>
                </Box>
                {pendingLoading && <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>}
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Deployment</TableCell>
                            <TableCell>Environment</TableCell>
                            <TableCell>Requested By</TableCell>
                            <TableCell>Requested</TableCell>
                            <TableCell align="right">Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {pending.map(a => (
                            <TableRow key={a.id} hover>
                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{a.deployment_id.slice(0, 12)}…</TableCell>
                                <TableCell>
                                    <Chip label={a.env.toUpperCase()} size="small" color={a.env === 'prod' ? 'success' : 'primary'} sx={{ fontWeight: 700 }} />
                                </TableCell>
                                <TableCell>{a.requested_by}</TableCell>
                                <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>
                                    {formatDistanceToNow(new Date(a.created_at), { addSuffix: true })}
                                </TableCell>
                                <TableCell align="right">
                                    <Button
                                        size="small" variant="contained" color="success"
                                        startIcon={<CheckCircle size={14} />}
                                        sx={{ mr: 1 }}
                                        onClick={() => setActionDialog({ id: a.id, type: 'approve', env: a.env })}
                                    >
                                        Approve
                                    </Button>
                                    <Button
                                        size="small" variant="outlined" color="error"
                                        startIcon={<XCircle size={14} />}
                                        onClick={() => setActionDialog({ id: a.id, type: 'reject', env: a.env })}
                                    >
                                        Reject
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                        {!pendingLoading && pending.length === 0 && (
                            <TableRow><TableCell colSpan={5} sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>No pending approvals ✓</TableCell></TableRow>
                        )}
                    </TableBody>
                </Table>
            </Paper>

            {/* Approval History */}
            <Paper>
                <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <Typography variant="h6" fontWeight={600}>Approval History</Typography>
                </Box>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Status</TableCell>
                            <TableCell>Environment</TableCell>
                            <TableCell>Requested By</TableCell>
                            <TableCell>Decided By</TableCell>
                            <TableCell>Decided At</TableCell>
                            <TableCell>Reason</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {history.filter(a => a.status !== 'pending').slice(0, 20).map(a => (
                            <TableRow key={a.id} hover>
                                <TableCell><StatusChip status={a.status} /></TableCell>
                                <TableCell>{a.env}</TableCell>
                                <TableCell>{a.requested_by}</TableCell>
                                <TableCell>{a.approved_by ?? '—'}</TableCell>
                                <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>
                                    {a.approved_at ? format(new Date(a.approved_at), 'PP p') : '—'}
                                </TableCell>
                                <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem', maxWidth: 200 }}>
                                    {a.reason ?? '—'}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </Paper>

            {/* Approve/Reject Dialog */}
            <Dialog open={!!actionDialog} onClose={() => setActionDialog(null)} maxWidth="sm" fullWidth>
                <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {actionDialog?.type === 'approve'
                        ? <><CheckCircle size={20} color="#22c55e" /> Approve Deployment</>
                        : <><XCircle size={20} color="#ef4444" /> Reject Deployment</>
                    }
                </DialogTitle>
                <DialogContent>
                    {actionDialog?.env === 'prod' && actionDialog.type === 'approve' && (
                        <Alert severity="warning" sx={{ mb: 2 }}>You are approving a PRODUCTION deployment.</Alert>
                    )}
                    <TextField
                        fullWidth label="Reason (optional)" multiline rows={2}
                        value={reason} onChange={e => setReason(e.target.value)}
                        sx={{ mt: 1 }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setActionDialog(null)}>Cancel</Button>
                    <Button
                        variant="contained"
                        color={actionDialog?.type === 'approve' ? 'success' : 'error'}
                        disabled={approveMutation.isPending}
                        onClick={() => approveMutation.mutate({ id: actionDialog!.id, type: actionDialog!.type, reason })}
                    >
                        {approveMutation.isPending ? <CircularProgress size={20} /> : actionDialog?.type === 'approve' ? 'Approve' : 'Reject'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default Approvals;
