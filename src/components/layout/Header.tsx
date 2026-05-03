import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import {
  MapPin, ShoppingBag, User, Heart, LogIn, LogOut,
  Menu, X, Store, Shield, ChevronDown, Building2
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuthStore } from '../../store/useAuthStore'
import { LoginModal } from '../auth/LoginModal'

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [loginOpen, setLoginOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const { currentUser, logout } = useAuthStore()
  const navigate = useNavigate()

  const navLinks = [
    { to: '/haendler', label: 'Händler', icon: <Store size={15} /> },
    { to: '/produkte', label: 'Produkte', icon: <ShoppingBag size={15} /> },
    { to: '/karte', label: 'Karte', icon: <MapPin size={15} /> },
  ]

  return (
    <>
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 shrink-0">
              <div className="w-9 h-9 bg-primary-700 rounded-xl flex items-center justify-center shadow-sm">
                <Building2 size={18} className="text-white" />
              </div>
              <div className="hidden sm:block">
                <div className="font-bold text-primary-800 text-sm leading-tight">Stadtmarktplatz</div>
                <div className="text-xs text-gray-500 leading-tight">Bad Mergentheim</div>
              </div>
            </Link>

            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-800'
                        : 'text-gray-600 hover:text-primary-700 hover:bg-gray-50'
                    )
                  }
                >
                  {link.icon}
                  {link.label}
                </NavLink>
              ))}
            </nav>

            {/* Right actions */}
            <div className="flex items-center gap-2">
              {/* Favoriten */}
              {currentUser?.role === 'customer' && (
                <Link
                  to="/favoriten"
                  className="hidden sm:flex p-2 rounded-lg text-gray-500 hover:text-red-500 hover:bg-red-50 transition-colors"
                  title="Meine Favoriten"
                >
                  <Heart size={18} />
                </Link>
              )}

              {/* Seller area shortcut */}
              {currentUser?.role === 'merchant' && (
                <Link
                  to="/seller"
                  className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-secondary-500 text-white text-xs font-medium hover:bg-secondary-600 transition-colors"
                >
                  <Store size={14} />
                  Händlerbereich
                </Link>
              )}

              {/* Admin area shortcut */}
              {currentUser?.role === 'admin' && (
                <Link
                  to="/admin"
                  className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 text-white text-xs font-medium hover:bg-purple-700 transition-colors"
                >
                  <Shield size={14} />
                  Admin
                </Link>
              )}

              {/* User menu */}
              {currentUser ? (
                <div className="relative">
                  <button
                    onClick={() => setProfileOpen(!profileOpen)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <img
                      src={currentUser.avatarUrl ?? `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=1b4f8a&color=fff`}
                      alt={currentUser.name}
                      className="w-7 h-7 rounded-full object-cover"
                    />
                    <span className="hidden sm:block text-sm font-medium text-gray-700 max-w-[120px] truncate">
                      {currentUser.name}
                    </span>
                    <ChevronDown size={14} className="text-gray-400" />
                  </button>

                  {profileOpen && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setProfileOpen(false)} />
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 z-20 overflow-hidden">
                        <div className="px-4 py-3 border-b border-gray-100">
                          <p className="text-sm font-medium text-gray-900 truncate">{currentUser.name}</p>
                          <p className="text-xs text-gray-500 truncate">{currentUser.email}</p>
                        </div>
                        <div className="py-1">
                          {currentUser.role === 'customer' && (
                            <>
                              <Link to="/profil" onClick={() => setProfileOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                                <User size={14} />Mein Profil
                              </Link>
                              <Link to="/favoriten" onClick={() => setProfileOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                                <Heart size={14} />Favoriten
                              </Link>
                            </>
                          )}
                          {currentUser.role === 'merchant' && (
                            <Link to="/seller" onClick={() => setProfileOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                              <Store size={14} />Händlerbereich
                            </Link>
                          )}
                          {currentUser.role === 'admin' && (
                            <Link to="/admin" onClick={() => setProfileOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                              <Shield size={14} />Adminbereich
                            </Link>
                          )}
                          <button
                            onClick={() => { logout(); setProfileOpen(false); navigate('/') }}
                            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                          >
                            <LogOut size={14} />Abmelden
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => setLoginOpen(true)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary-700 text-white text-sm font-medium hover:bg-primary-800 transition-colors"
                >
                  <LogIn size={15} />
                  <span className="hidden sm:inline">Anmelden</span>
                </button>
              )}

              {/* Mobile menu toggle */}
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="md:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
              >
                {menuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>

          {/* Mobile Nav */}
          {menuOpen && (
            <div className="md:hidden border-t border-gray-100 py-3 space-y-1">
              {navLinks.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  onClick={() => setMenuOpen(false)}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium',
                      isActive ? 'bg-primary-50 text-primary-800' : 'text-gray-700 hover:bg-gray-50'
                    )
                  }
                >
                  {link.icon}{link.label}
                </NavLink>
              ))}
              {currentUser?.role === 'customer' && (
                <NavLink to="/favoriten" onClick={() => setMenuOpen(false)} className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
                  <Heart size={15} />Favoriten
                </NavLink>
              )}
              {!currentUser && (
                <button onClick={() => { setMenuOpen(false); setLoginOpen(true) }} className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-primary-700 w-full">
                  <LogIn size={15} />Anmelden
                </button>
              )}
            </div>
          )}
        </div>
      </header>

      <LoginModal isOpen={loginOpen} onClose={() => setLoginOpen(false)} />
    </>
  )
}
