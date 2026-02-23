import { TenantProvider, useTenant } from './context/TenantContext';
import {
  Calendar,
  Clock,
  User,
  CheckCircle2,
  ChevronRight,
  Star
} from 'lucide-react';

const BookingPage = () => {
  const { tenant, loading, error } = useTenant();

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="animate-pulse flex flex-col items-center">
        <div className="h-12 w-12 rounded-full bg-indigo-200 mb-4"></div>
        <div className="h-4 w-48 bg-gray-200 rounded"></div>
      </div>
    </div>
  );

  if (error || !tenant) return (
    <div className="min-h-screen flex items-center justify-center bg-red-50 p-4 text-center">
      <div>
        <h1 className="text-2xl font-bold text-red-600 mb-2">Service Unavailable</h1>
        <p className="text-red-500">{error || 'Tenant not found. Please check the URL.'}</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 selection:bg-indigo-100">
      {/* Header / Hero */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {tenant.theme_config.logo_url ? (
              <img src={tenant.theme_config.logo_url} alt={tenant.name} className="h-8 w-auto" />
            ) : (
              <div className="h-10 w-10 rounded-xl flex items-center justify-center text-white text-xl font-bold"
                style={{ backgroundColor: tenant.theme_config.primary_color }}>
                {tenant.name.charAt(0)}
              </div>
            )}
            <div>
              <h1 className="font-bold text-gray-900 leading-tight">{tenant.name}</h1>
              <div className="flex items-center text-xs text-gray-500">
                <Star className="h-3 w-3 text-yellow-500 fill-yellow-500 mr-1" />
                <span>4.9 (120+ reviews)</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Intro Section */}
        <section className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold mb-4">Book an Appointment</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-start gap-4 p-4 rounded-xl transition-all cursor-pointer hover:bg-gray-50 border-2 border-transparent hover:border-indigo-100">
              <div className="p-3 rounded-lg bg-indigo-50 text-indigo-600">
                <User className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold">Professional</h3>
                <p className="text-sm text-gray-500">Choose your favorite artist</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-xl transition-all cursor-pointer hover:bg-gray-50 border-2 border-transparent hover:border-indigo-100">
              <div className="p-3 rounded-lg bg-purple-50 text-purple-600">
                <Calendar className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold">Date & Time</h3>
                <p className="text-sm text-gray-500">Picked from available slots</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-xl transition-all cursor-pointer hover:bg-gray-50 border-2 border-transparent hover:border-indigo-100">
              <div className="p-3 rounded-lg bg-green-50 text-green-600">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold">Confirm</h3>
                <p className="text-sm text-gray-500">Instant SMS confirmation</p>
              </div>
            </div>
          </div>
        </section>

        {/* Popular Services */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Popular Services</h2>
            <button className="text-sm font-medium text-indigo-600 hover:text-indigo-700 flex items-center">
              View all <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { name: 'Standard Session', price: '$80', duration: '60 min', desc: 'Consultation and premium service' },
              { name: 'Detailed Art', price: '$150', duration: '120 min', desc: 'Detailed custom work with depth' },
            ].map((s, i) => (
              <div key={i} className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow group cursor-pointer relative overflow-hidden">
                <div className="absolute top-0 right-0 h-1 w-full scale-x-0 group-hover:scale-x-100 transition-transform origin-left" style={{ backgroundColor: tenant.theme_config.primary_color }}></div>
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-bold text-gray-900">{s.name}</h3>
                  <span className="font-bold text-lg" style={{ color: tenant.theme_config.primary_color }}>{s.price}</span>
                </div>
                <p className="text-sm text-gray-500 mb-4">{s.desc}</p>
                <div className="flex items-center text-xs text-gray-400 font-medium">
                  <Clock className="h-3 w-3 mr-1" />
                  {s.duration}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center py-8">
          <p className="text-sm text-gray-400">© 2026 {tenant.name} • Powered by Inka SaaS</p>
        </footer>
      </main>
    </div>
  );
};

function App() {
  return (
    <TenantProvider>
      <BookingPage />
    </TenantProvider>
  )
}

export default App
