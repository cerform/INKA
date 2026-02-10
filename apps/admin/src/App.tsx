import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardLayout from '@/layouts/DashboardLayout';
import { useAuthStore } from '@/stores/auth';
import Setup from '@/pages/Setup';

// Lazy load pages for performance
import { memo } from 'react';

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
const Calendar = () => <h1 className="text-2xl font-bold">Calendar View</h1>;
const Clients = () => <h1 className="text-2xl font-bold">Clients Management</h1>;
const Bookings = () => <h1 className="text-2xl font-bold">Bookings Management</h1>;
const Staff = () => <h1 className="text-2xl font-bold">Staff & Availability</h1>;
const Settings = () => <h1 className="text-2xl font-bold">Settings</h1>;
const Login = () => <div className="flex items-center justify-center min-h-screen"><h1 className="text-2xl font-bold">Login Page</h1></div>;

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
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
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="calendar" element={<Calendar />} />
            <Route path="clients" element={<Clients />} />
            <Route path="bookings" element={<Bookings />} />
            <Route path="staff" element={<Staff />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
