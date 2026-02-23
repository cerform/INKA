import React, { createContext, useContext, useEffect, useState } from 'react';

interface TenantConfig {
    id: number;
    name: string;
    slug: string;
    theme_config: {
        primary_color: string;
        secondary_color: string;
        logo_url: string | null;
        font_family: string;
    };
    type: string;
}

const TenantContext = createContext<{
    tenant: TenantConfig | null;
    loading: boolean;
    error: string | null
}>({ tenant: null, loading: true, error: null });

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [tenant, setTenant] = useState<TenantConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const resolveTenant = async () => {
            try {
                const hostname = window.location.hostname;
                // For local dev, we might use a query param or a hardcoded slug
                // e.g. localhost:5173 -> demo
                const slug = hostname === 'localhost' || hostname === '127.0.0.1'
                    ? 'demo'
                    : hostname.split('.')[0];

                const response = await fetch(`/api/v1/tenants/config/${slug}`);
                if (!response.ok) throw new Error('Failed to load tenant configuration');

                const data = await response.json();
                setTenant(data);

                // Apply theme
                document.documentElement.style.setProperty('--primary-color', data.theme_config.primary_color);
                document.documentElement.style.setProperty('--secondary-color', data.theme_config.secondary_color);
                document.body.style.fontFamily = data.theme_config.font_family;

            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        resolveTenant();
    }, []);

    return (
        <TenantContext.Provider value={{ tenant, loading, error }}>
            {children}
        </TenantContext.Provider>
    );
};

export const useTenant = () => useContext(TenantContext);
