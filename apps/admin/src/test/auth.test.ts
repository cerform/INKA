import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/stores/auth';

describe('useAuthStore', () => {
    beforeEach(() => {
        // Reset store before each test if needed
        localStorage.clear();
    });

    it('should initialize with default values', () => {
        const state = useAuthStore.getState();
        expect(state.user).toBeNull();
        expect(state.isAuthenticated).toBe(false);
        expect(state.token).toBeNull();
    });

    it('should set authentication data', () => {
        const user = { id: '1', name: 'Admin', role: 'admin' };
        const token = 'fake-token';

        useAuthStore.getState().setAuth(user, token);

        const state = useAuthStore.getState();
        expect(state.user).toEqual(user);
        expect(state.isAuthenticated).toBe(true);
        expect(state.token).toBe(token);
        expect(localStorage.getItem('auth_token')).toBe(token);
    });

    it('should logout and clear data', () => {
        const user = { id: '1', name: 'Admin', role: 'admin' };
        const token = 'fake-token';

        useAuthStore.getState().setAuth(user, token);
        useAuthStore.getState().logout();

        const state = useAuthStore.getState();
        expect(state.user).toBeNull();
        expect(state.isAuthenticated).toBe(false);
        expect(state.token).toBeNull();
        expect(localStorage.getItem('auth_token')).toBeNull();
    });
});
