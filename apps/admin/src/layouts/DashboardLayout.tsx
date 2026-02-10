import React from 'react';
import { Link, useNavigate, Outlet } from 'react-router-dom';
import {
    LayoutDashboard,
    Calendar,
    Users,
    BookOpen,
    UserSquare2,
    Settings,
    LogOut,
    Menu,
    X
} from 'lucide-react';
import { useAuthStore } from '@/stores/auth';

const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Calendar', href: '/calendar', icon: Calendar },
    { name: 'Clients', href: '/clients', icon: Users },
    { name: 'Bookings', href: '/bookings', icon: BookOpen },
    { name: 'Staff', href: '/staff', icon: UserSquare2 },
    { name: 'Settings', href: '/settings', icon: Settings },
];

export default function DashboardLayout() {
    const [sidebarOpen, setSidebarOpen] = React.useState(false);
    const logout = useAuthStore((state) => state.logout);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex">
            {/* Sidebar for mobile */}
            <div className={`fixed inset-0 z-40 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
                <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)}></div>
                <div className="fixed inset-y-0 left-0 flex flex-col w-64 bg-white dark:bg-gray-800 shadow-xl">
                    <div className="p-4 flex items-center justify-between border-b dark:border-gray-700">
                        <span className="text-xl font-bold text-indigo-600">Inka Admin</span>
                        <button onClick={() => setSidebarOpen(false)}>
                            <X className="h-6 w-6 text-gray-500" />
                        </button>
                    </div>
                    <nav className="flex-1 p-4 space-y-1">
                        {navigation.map((item) => (
                            <Link
                                key={item.name}
                                to={item.href}
                                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
                                onClick={() => setSidebarOpen(false)}
                            >
                                <item.icon className="mr-3 h-5 w-5" />
                                {item.name}
                            </Link>
                        ))}
                    </nav>
                </div>
            </div>

            {/* Static sidebar for desktop */}
            <div className="hidden lg:flex lg:flex-shrink-0">
                <div className="flex flex-col w-64 bg-white dark:bg-gray-800 border-r dark:border-gray-700">
                    <div className="p-6">
                        <span className="text-2xl font-bold text-indigo-600">Inka Admin</span>
                    </div>
                    <nav className="flex-1 px-4 space-y-2">
                        {navigation.map((item) => (
                            <Link
                                key={item.name}
                                to={item.href}
                                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                                active-classname="bg-indigo-50 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
                            >
                                <item.icon className="mr-3 h-5 w-5" />
                                {item.name}
                            </Link>
                        ))}
                    </nav>
                    <div className="p-4 border-t dark:border-gray-700">
                        <button
                            onClick={handleLogout}
                            className="flex w-full items-center px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                        >
                            <LogOut className="mr-3 h-5 w-5" />
                            Logout
                        </button>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="flex flex-col flex-1">
                <header className="h-16 bg-white dark:bg-gray-800 border-b dark:border-gray-700 flex items-center px-4 lg:hidden">
                    <button onClick={() => setSidebarOpen(true)}>
                        <Menu className="h-6 w-6 text-gray-500" />
                    </button>
                    <span className="ml-4 text-lg font-semibold dark:text-white">Inka Admin</span>
                </header>
                <main className="p-6 flex-1 overflow-auto">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
