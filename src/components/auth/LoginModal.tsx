import { useNavigate } from 'react-router-dom'
import { LogIn, Users, Shield, Store } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { useAuthStore } from '../../store/useAuthStore'
import { DEMO_ACCOUNTS } from '../../data/users'

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
}

const roleIcons = {
  customer: <Users size={16} className="text-blue-500" />,
  merchant: <Store size={16} className="text-amber-500" />,
  admin: <Shield size={16} className="text-purple-500" />,
}

const roleLabels = {
  customer: 'Kunde',
  merchant: 'Händler',
  admin: 'Administrator',
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const { switchRole, logout, currentUser } = useAuthStore()
  const navigate = useNavigate()

  function handleLogin(index: number) {
    switchRole(index)
    onClose()
    const account = DEMO_ACCOUNTS[index]
    if (account.role === 'merchant') navigate('/seller')
    else if (account.role === 'admin') navigate('/admin')
    else navigate('/profil')
  }

  function handleLogout() {
    logout()
    onClose()
    navigate('/')
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Demo-Anmeldung" size="sm">
      <div className="space-y-3">
        <p className="text-sm text-gray-500 mb-4">
          Wählen Sie eine Demo-Rolle, um die verschiedenen Bereiche der Plattform zu erkunden:
        </p>

        {DEMO_ACCOUNTS.map((account, index) => (
          <button
            key={index}
            onClick={() => handleLogin(index)}
            className={`w-full text-left p-3.5 rounded-xl border-2 transition-all ${
              currentUser?.role === account.role
                ? 'border-primary-400 bg-primary-50'
                : 'border-gray-100 hover:border-primary-200 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center">
                {roleIcons[account.role]}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-gray-900">{account.label}</span>
                  <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full">
                    {roleLabels[account.role]}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">{account.description}</p>
              </div>
            </div>
          </button>
        ))}

        {currentUser && (
          <button
            onClick={handleLogout}
            className="w-full mt-4 p-3 rounded-xl border border-red-200 text-red-600 text-sm font-medium hover:bg-red-50 transition-colors"
          >
            Abmelden
          </button>
        )}

        <p className="text-xs text-gray-400 text-center pt-2">
          Dies ist ein Demo-System. Keine echten Daten oder Zahlungen.
        </p>
      </div>
    </Modal>
  )
}
