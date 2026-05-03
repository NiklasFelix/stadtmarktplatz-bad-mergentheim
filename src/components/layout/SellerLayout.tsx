import { Outlet, NavLink, Link } from 'react-router-dom'
import {
  LayoutDashboard, Package, ClipboardList, User,
  ArrowLeft, Menu, X, Store
} from 'lucide-react'
import { useState } from 'react'
import { clsx } from 'clsx'
import { useAuthStore } from '../../store/useAuthStore'
import { useDataStore } from '../../store/useDataStore'

const navItems = [
  { to: '/seller', label: 'Dashboard', icon: <LayoutDashboard size={18} />, end: true },
  { to: '/seller/reservierungen', label: 'Reservierungen', icon: <ClipboardList size={18} /> },
  { to: '/seller/produkte', label: 'Produkte', icon: <Package size={18} /> },
  { to: '/seller/profil', label: 'Mein Profil', icon: <User size={18} /> },
]

export function SellerLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { currentUser, currentMerchantId } = useAuthStore()
  const merchants = useDataStore((s) => s.merchants)
  const merchant = merchants.find((m) => m.id === currentMerchantId)

  const reservations = useDataStore((s) =>
    s.reservations.filter((r) => r.merchantId === currentMerchantId && r.status === 'received')
  )

  return (
    <div className="min-h-screen bg-stone-50 flex">
      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 z-40 flex flex-col transition-transform duration-200',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Logo area */}
        <div className="p-5 border-b border-gray-100">
          <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-primary-700 text-xs mb-4 transition-colors">
            <ArrowLeft size={14} />Zur Website
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl overflow-hidden bg-gray-100">
              {merchant?.images.store ? (
                <img src={merchant.images.store} alt={merchant.name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <Store size={20} />
                </div>
              )}
            </div>
            <div>
              <p className="font-semibold text-gray-900 text-sm leading-tight">{merchant?.name ?? 'Händlerbereich'}</p>
              <p className="text-xs text-gray-400 leading-tight">{currentUser?.name}</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-800'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )
              }
            >
              {item.icon}
              <span>{item.label}</span>
              {item.label === 'Reservierungen' && reservations.length > 0 && (
                <span className="ml-auto bg-secondary-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                  {reservations.length}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <p className="text-xs text-gray-400">Händlerbereich v1.0</p>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Top bar */}
        <div className="sticky top-0 z-20 bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100"
          >
            <Menu size={20} />
          </button>
          <span className="font-semibold text-gray-800">Händlerbereich</span>
        </div>

        <main className="flex-1 p-6 max-w-6xl w-full">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
