import { Outlet, NavLink, Link } from 'react-router-dom'
import {
  LayoutDashboard, Store, Tag, FileText, ArrowLeft, Menu, Shield
} from 'lucide-react'
import { useState } from 'react'
import { clsx } from 'clsx'
import { useAuthStore } from '../../store/useAuthStore'

const navItems = [
  { to: '/admin', label: 'Dashboard', icon: <LayoutDashboard size={18} />, end: true },
  { to: '/admin/haendler', label: 'Händler', icon: <Store size={18} /> },
  { to: '/admin/kategorien', label: 'Kategorien', icon: <Tag size={18} /> },
  { to: '/admin/inhalte', label: 'Startseite', icon: <FileText size={18} /> },
]

export function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { currentUser } = useAuthStore()

  return (
    <div className="min-h-screen bg-stone-50 flex">
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside
        className={clsx(
          'fixed top-0 left-0 h-full w-64 bg-gray-900 text-gray-200 z-40 flex flex-col transition-transform duration-200',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className="p-5 border-b border-gray-800">
          <Link to="/" className="flex items-center gap-2 text-gray-500 hover:text-white text-xs mb-4 transition-colors">
            <ArrowLeft size={14} />Zur Website
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-600 flex items-center justify-center">
              <Shield size={18} className="text-white" />
            </div>
            <div>
              <p className="font-semibold text-white text-sm">Adminbereich</p>
              <p className="text-xs text-gray-400">{currentUser?.name}</p>
            </div>
          </div>
        </div>

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
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                )
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <p className="text-xs text-gray-600">Wirtschaftsförderung Bad Mergentheim</p>
        </div>
      </aside>

      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        <div className="sticky top-0 z-20 bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 lg:hidden">
          <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg text-gray-500 hover:bg-gray-100">
            <Menu size={20} />
          </button>
          <span className="font-semibold text-gray-800">Adminbereich</span>
        </div>
        <main className="flex-1 p-6 max-w-6xl w-full">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
