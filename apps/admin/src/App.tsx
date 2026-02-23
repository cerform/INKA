import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardLayout from '@/layouts/DashboardLayout';
import { useAuthStore } from '@/stores/auth';
import Setup from '@/pages/Setup';
import SalonSetup from '@/pages/SalonSetup';
import CalendarView from '@/pages/CalendarView';
import StaffManagement from '@/pages/StaffManagement';
import ClientManagement from '@/pages/ClientManagement';
import FleetView from '@/pages/FleetView';

// Lazy load pages for performance

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Placeholder components for pages
const Dashboard = () => <h1 className="text-2xl font-bold">Today & This Week</h1>;
const Bookings = () => <h1 className="text-2xl font-bold">Bookings Management</h1>;
const Settings = () => <h1 className="text-2xl font-bold">Settings</h1>;
const SystemHealth = () => <h1 className="text-2xl font-bold">System Health</h1>;
const AuditLogs = () => <h1 className="text-2xl font-bold">Audit Logs</h1>;
const DORAMetrics = () => <h1 className="text-2xl font-bold">DORA Metrics</h1>;
const Login = () => <div className="flex items-center justify-center min-h-screen"><h1 className="text-2xl font-bold">Login Page</h1></div>;

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  // For development, we might want to bypass this or have a default user
  // if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/setup" element={<Setup />} />
          <Route path="/setup/salon" element={<SalonSetup />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="tenants" element={<FleetView />} />
            <Route path="health" element={<SystemHealth />} />
            <Route path="audit" element={<AuditLogs />} />
            <Route path="metrics" element={<DORAMetrics />} />
            <Route path="calendar" element={<CalendarView />} />
            <Route path="clients" element={<ClientManagement />} />
            <Route path="bookings" element={<Bookings />} />
            <Route path="staff" element={<StaffManagement />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
