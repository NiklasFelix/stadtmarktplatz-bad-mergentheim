import { Link } from 'react-router-dom'
import { Plus, Edit, Power, PowerOff, Eye } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { MERCHANT_STATUS_LABELS, MERCHANT_STATUS_COLORS } from '../../utils/formatters'
import type { MerchantStatus } from '../../types'

export function AdminMerchantsPage() {
  const { merchants, categories, updateMerchant } = useDataStore()

  function toggleStatus(id: string, current: MerchantStatus) {
    const next: MerchantStatus = current === 'active' ? 'inactive' : 'active'
    updateMerchant(id, { status: next })
  }

  function toggleFeatured(id: string, current: boolean) {
    updateMerchant(id, { featured: !current })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Händler verwalten</h1>
          <p className="text-gray-500 mt-1">{merchants.length} Händler auf der Plattform</p>
        </div>
        <Link
          to="/admin/haendler/neu"
          className="flex items-center gap-2 bg-primary-700 text-white px-4 py-2.5 rounded-xl font-medium text-sm hover:bg-primary-800 transition-colors"
        >
          <Plus size={16} />
          Händler anlegen
        </Link>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Händler</th>
                <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden md:table-cell">Kategorien</th>
                <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden lg:table-cell">C&C</th>
                <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden lg:table-cell">Featured</th>
                <th className="px-4 py-3.5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {merchants.map((m) => {
                const merchantCats = categories.filter((c) => m.categoryIds.includes(c.id))
                return (
                  <tr key={m.id} className={`group ${m.status !== 'active' ? 'opacity-60' : ''}`}>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <img src={m.images.store} alt={m.name} className="w-10 h-10 rounded-lg object-cover shrink-0" />
                        <div>
                          <p className="font-medium text-gray-900">{m.name}</p>
                          <p className="text-xs text-gray-400">{m.address.street}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 hidden md:table-cell">
                      <div className="flex flex-wrap gap-1">
                        {merchantCats.slice(0, 2).map((c) => (
                          <span key={c.id} className="text-xs px-1.5 py-0.5 rounded-full" style={{ backgroundColor: `${c.color}20`, color: c.color }}>
                            {c.icon}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${MERCHANT_STATUS_COLORS[m.status]}`}>
                        {MERCHANT_STATUS_LABELS[m.status]}
                      </span>
                    </td>
                    <td className="px-4 py-4 hidden lg:table-cell text-sm">
                      {m.clickAndCollect ? (
                        <span className="text-green-600 font-medium">✓ Aktiv</span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-4 hidden lg:table-cell">
                      <button
                        onClick={() => toggleFeatured(m.id, m.featured)}
                        className={`text-xs px-2 py-1 rounded-full transition-colors cursor-pointer ${m.featured ? 'bg-secondary-100 text-secondary-700' : 'text-gray-400 hover:text-secondary-600'}`}
                      >
                        {m.featured ? '⭐ Featured' : 'Nicht featured'}
                      </button>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1.5 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                        <Link to={`/haendler/${m.slug}`} target="_blank" className="p-1.5 rounded-lg text-gray-400 hover:text-primary-700 hover:bg-primary-50 transition-colors" title="Vorschau">
                          <Eye size={14} />
                        </Link>
                        <Link to={`/admin/haendler/${m.id}/bearbeiten`} className="p-1.5 rounded-lg text-gray-400 hover:text-primary-700 hover:bg-primary-50 transition-colors" title="Bearbeiten">
                          <Edit size={14} />
                        </Link>
                        <button
                          onClick={() => toggleStatus(m.id, m.status)}
                          className={`p-1.5 rounded-lg transition-colors ${m.status === 'active' ? 'text-gray-400 hover:text-red-500 hover:bg-red-50' : 'text-gray-400 hover:text-green-600 hover:bg-green-50'}`}
                          title={m.status === 'active' ? 'Deaktivieren' : 'Aktivieren'}
                        >
                          {m.status === 'active' ? <PowerOff size={14} /> : <Power size={14} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
