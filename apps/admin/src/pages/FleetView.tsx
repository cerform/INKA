import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Plus,
    ExternalLink,
    Power,
    PowerOff,
    Search,
    Filter,
    ArrowUpRight,
    X
} from 'lucide-react';

interface Tenant {
    id: number;
    name: string;
    slug: string;
    status: 'created' | 'active' | 'suspended' | 'deleted';
    type: string;
    domain?: string;
}

interface CreateTenantForm {
    name: string;
    slug: string;
    type: string;
    domain: string;
    theme_config: {
        primary_color: string;
        secondary_color: string;
        font_family: string;
    };
}

export default function FleetView() {
    const queryClient = useQueryClient();
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState<CreateTenantForm>({
        name: '', slug: '', type: 'beauty', domain: '',
        theme_config: { primary_color: '#4f46e5', secondary_color: '#7c3aed', font_family: 'Inter' }
    });

    const { data: tenants, isLoading } = useQuery<Tenant[]>({
        queryKey: ['tenants'],
        queryFn: async () => {
            const res = await fetch('/api/v1/tenants/');
            return res.json();
        }
    });

    const createMutation = useMutation({
        mutationFn: async (data: CreateTenantForm) => {
            const res = await fetch('/api/v1/tenants/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to create tenant');
            }
            return res.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tenants'] });
            setShowCreate(false);
            setForm({ name: '', slug: '', type: 'beauty', domain: '', theme_config: { primary_color: '#4f46e5', secondary_color: '#7c3aed', font_family: 'Inter' } });
        },
    });

    const statusMutation = useMutation({
        mutationFn: async ({ id, status }: { id: number; status: string }) => {
            const res = await fetch(`/api/v1/tenants/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status }),
            });
            if (!res.ok) throw new Error('Failed to update tenant');
            return res.json();
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tenants'] }),
    });

    if (isLoading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div></div>;

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400">
                        Fleet Management
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Monitor and manage all active salon instances across the platform.
                    </p>
                </div>
                <button
                    onClick={() => setShowCreate(true)}
                    className="flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-all shadow-lg shadow-indigo-200 dark:shadow-none hover:scale-105 active:scale-95"
                >
                    <Plus className="h-5 w-5 mr-2" />
                    Create New Tenant
                </button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total Tenants', value: tenants?.length || 0, color: 'bg-blue-500' },
                    { label: 'Active', value: tenants?.filter(t => t.status === 'active').length || 0, color: 'bg-green-500' },
                    { label: 'Suspended', value: tenants?.filter(t => t.status === 'suspended').length || 0, color: 'bg-yellow-500' },
                    { label: 'System Health', value: '99.9%', color: 'bg-purple-500' },
                ].map((stat, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
                        <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
                        <p className="text-2xl font-bold mt-1 dark:text-white">{stat.value}</p>
                        <div className={`h-1 w-full mt-2 rounded-full ${stat.color} opacity-20`}></div>
                    </div>
                ))}
            </div>

            {/* Filters and Search */}
            <div className="bg-white dark:bg-gray-800 p-2 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-wrap items-center gap-2">
                <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search by name, slug or domain..."
                        className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border-none rounded-lg focus:ring-2 focus:ring-indigo-500 dark:text-white"
                    />
                </div>
                <button className="flex items-center px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                    <Filter className="h-4 w-4 mr-2" />
                    Filters
                </button>
            </div>

            {/* Tenants Table */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-50 dark:bg-gray-900/50 border-b dark:border-gray-700">
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Tenant</th>
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Deployment</th>
                            <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y dark:divide-gray-700">
                        {tenants?.map((tenant) => (
                            <tr key={tenant.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors group">
                                <td className="px-6 py-4">
                                    <div>
                                        <div className="font-semibold text-gray-900 dark:text-white">{tenant.name}</div>
                                        <div className="text-sm text-gray-500 dark:text-gray-400">{tenant.slug}.inka.app</div>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${tenant.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                                        tenant.status === 'suspended' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                                            'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
                                        }`}>
                                        <div className={`h-1.5 w-1.5 rounded-full mr-1.5 ${tenant.status === 'active' ? 'bg-green-500' :
                                            tenant.status === 'suspended' ? 'bg-yellow-500' :
                                                'bg-gray-500'
                                            }`}></div>
                                        {tenant.status.toUpperCase()}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-300">
                                    {tenant.type.charAt(0).toUpperCase() + tenant.type.slice(1)}
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center text-sm text-green-600 dark:text-green-400">
                                        <ArrowUpRight className="h-4 w-4 mr-1" />
                                        Provisioned
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button className="p-2 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" title="Visit portal">
                                            <ExternalLink className="h-4 w-4" />
                                        </button>
                                        {tenant.status === 'active' ? (
                                            <button
                                                onClick={() => statusMutation.mutate({ id: tenant.id, status: 'suspended' })}
                                                className="p-2 text-gray-400 hover:text-yellow-600 dark:hover:text-yellow-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                                                title="Suspend"
                                            >
                                                <PowerOff className="h-4 w-4" />
                                            </button>
                                        ) : (
                                            <button
                                                onClick={() => statusMutation.mutate({ id: tenant.id, status: 'active' })}
                                                className="p-2 text-gray-400 hover:text-green-600 dark:hover:text-green-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                                                title="Activate"
                                            >
                                                <Power className="h-4 w-4" />
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Create Tenant Modal */}
            {showCreate && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4 animate-in zoom-in-95 duration-200">
                        <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
                            <h2 className="text-xl font-bold dark:text-white">Create New Tenant</h2>
                            <button onClick={() => setShowCreate(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                                <X className="h-5 w-5 text-gray-500" />
                            </button>
                        </div>
                        <form
                            onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form); }}
                            className="p-6 space-y-4"
                        >
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                                <input
                                    type="text" required
                                    value={form.name}
                                    onChange={(e) => {
                                        const name = e.target.value;
                                        const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
                                        setForm(f => ({ ...f, name, slug }));
                                    }}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                    placeholder="Midnight Ink Studio"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Slug</label>
                                <div className="flex items-center">
                                    <input
                                        type="text" required
                                        value={form.slug}
                                        onChange={(e) => setForm(f => ({ ...f, slug: e.target.value }))}
                                        className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-l-lg bg-white dark:bg-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                        placeholder="midnight-ink"
                                    />
                                    <span className="px-3 py-2 bg-gray-100 dark:bg-gray-700 border border-l-0 border-gray-300 dark:border-gray-600 rounded-r-lg text-sm text-gray-500 dark:text-gray-400">
                                        .inka.app
                                    </span>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
                                    <select
                                        value={form.type}
                                        onChange={(e) => setForm(f => ({ ...f, type: e.target.value }))}
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
                                    >
                                        <option value="beauty">Beauty</option>
                                        <option value="tattoo">Tattoo</option>
                                        <option value="barbershop">Barbershop</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Primary Color</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="color"
                                            value={form.theme_config.primary_color}
                                            onChange={(e) => setForm(f => ({ ...f, theme_config: { ...f.theme_config, primary_color: e.target.value } }))}
                                            className="h-10 w-10 rounded border-0 cursor-pointer"
                                        />
                                        <span className="text-sm text-gray-500 dark:text-gray-400">{form.theme_config.primary_color}</span>
                                    </div>
                                </div>
                            </div>
                            {createMutation.isError && (
                                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400">
                                    {(createMutation.error as Error).message}
                                </div>
                            )}
                            <div className="flex justify-end gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setShowCreate(false)}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={createMutation.isPending}
                                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 transition-all"
                                >
                                    {createMutation.isPending ? 'Creating...' : 'Create Tenant'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
