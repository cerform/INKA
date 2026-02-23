import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    AppBar, Box, CssBaseline, Drawer, List, ListItem,
    ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography,
    Tooltip, Divider,
} from '@mui/material';
import {
    LayoutDashboard, PlayCircle, Rocket, ShieldCheck, Activity,
    ClipboardList, Settings, GitBranch,
} from 'lucide-react';

const DRAWER_WIDTH = 232;

const NAV = [
    { label: 'Dashboard', icon: <LayoutDashboard size={20} />, path: '/' },
    { label: 'Pipelines', icon: <PlayCircle size={20} />, path: '/pipelines' },
    { label: 'Deployments', icon: <Rocket size={20} />, path: '/deployments' },
    { label: 'Approvals', icon: <ShieldCheck size={20} />, path: '/approvals' },
    { label: 'DORA Metrics', icon: <Activity size={20} />, path: '/dora' },
    { label: 'Audit Log', icon: <ClipboardList size={20} />, path: '/audit' },
    { label: 'Settings', icon: <Settings size={20} />, path: '/settings' },
];

interface LayoutProps {
    children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
    const { pathname } = useLocation();

    return (
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
            <CssBaseline />

            {/* ── Top AppBar ───────────────────────────────────────────────── */}
            <AppBar
                position="fixed"
                sx={{
                    zIndex: t => t.zIndex.drawer + 1,
                    bgcolor: 'background.paper',
                    borderBottom: '1px solid rgba(255,255,255,0.08)',
                    boxShadow: 'none',
                }}
            >
                <Toolbar sx={{ gap: 1.5 }}>
                    <GitBranch size={22} color="#6366f1" />
                    <Typography
                        variant="h6"
                        sx={{ fontWeight: 800, letterSpacing: '-0.5px', color: 'primary.main', flexGrow: 1 }}
                    >
                        INKA CONTROL CENTER
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        v1.0.0
                    </Typography>
                </Toolbar>
            </AppBar>

            {/* ── Sidebar Drawer ────────────────────────────────────────────── */}
            <Drawer
                variant="permanent"
                sx={{
                    width: DRAWER_WIDTH,
                    flexShrink: 0,
                    [`& .MuiDrawer-paper`]: {
                        width: DRAWER_WIDTH,
                        boxSizing: 'border-box',
                        bgcolor: 'background.default',
                        borderRight: '1px solid rgba(255,255,255,0.06)',
                    },
                }}
            >
                <Toolbar />
                <Box sx={{ overflow: 'auto', pt: 1 }}>
                    <List dense>
                        {NAV.map(item => {
                            const active = pathname === item.path || (item.path !== '/' && pathname.startsWith(item.path));
                            return (
                                <ListItem key={item.label} disablePadding sx={{ px: 1, mb: 0.5 }}>
                                    <Tooltip title={item.label} placement="right" disableHoverListener>
                                        <ListItemButton
                                            component={Link}
                                            to={item.path}
                                            selected={active}
                                            sx={{
                                                borderRadius: 2,
                                                '&.Mui-selected': {
                                                    bgcolor: 'rgba(99,102,241,0.15)',
                                                    color: 'primary.light',
                                                    '& .MuiListItemIcon-root': { color: 'primary.light' },
                                                },
                                                '&:hover': { bgcolor: 'rgba(99,102,241,0.08)' },
                                            }}
                                        >
                                            <ListItemIcon sx={{ minWidth: 36, color: active ? 'primary.light' : 'text.secondary' }}>
                                                {item.icon}
                                            </ListItemIcon>
                                            <ListItemText
                                                primary={item.label}
                                                primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: active ? 600 : 400 }}
                                            />
                                        </ListItemButton>
                                    </Tooltip>
                                </ListItem>
                            );
                        })}
                    </List>
                    <Divider sx={{ mx: 2, mt: 2, borderColor: 'rgba(255,255,255,0.06)' }} />
                </Box>
            </Drawer>

            {/* ── Main Content ──────────────────────────────────────────────── */}
            <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default', p: 3 }}>
                <Toolbar />
                {children}
            </Box>
        </Box>
    );
};

export default Layout;
