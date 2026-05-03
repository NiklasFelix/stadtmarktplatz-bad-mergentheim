import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'
import L from 'leaflet'
import type { Merchant } from '../../types'
import { useDataStore } from '../../store/useDataStore'

// Fix Leaflet default icon paths broken by Vite
import markerIconUrl from 'leaflet/dist/images/marker-icon.png'
import markerIcon2xUrl from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadowUrl from 'leaflet/dist/images/marker-shadow.png'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIconUrl,
  iconRetinaUrl: markerIcon2xUrl,
  shadowUrl: markerShadowUrl,
})

function createMerchantIcon(highlighted: boolean) {
  return L.divIcon({
    html: `<div style="
      width:32px;height:32px;
      background:${highlighted ? '#d4820a' : '#1b4f8a'};
      border:3px solid white;
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      box-shadow:0 2px 8px rgba(0,0,0,0.3);
      display:flex;align-items:center;justify-content:center;
    ">
      <span style="transform:rotate(45deg);font-size:12px">🏪</span>
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
    className: '',
  })
}

// Sub-component to fly to a highlighted merchant
function MapFlyTo({ merchantId, merchants }: { merchantId: string | null; merchants: Merchant[] }) {
  const map = useMap()
  useEffect(() => {
    if (!merchantId) return
    const m = merchants.find((m) => m.id === merchantId)
    if (m) {
      map.flyTo([m.coordinates.lat, m.coordinates.lng], 16, { duration: 0.8 })
    }
  }, [merchantId, merchants, map])
  return null
}

interface MerchantMapProps {
  merchants?: Merchant[]
  highlightedId?: string | null
  onMarkerClick?: (id: string) => void
  height?: string
  zoom?: number
}

export function MerchantMap({
  merchants,
  highlightedId,
  onMarkerClick,
  height = '500px',
  zoom = 14,
}: MerchantMapProps) {
  const allMerchants = useDataStore((s) => s.merchants)
  const displayMerchants = merchants ?? allMerchants.filter((m) => m.status === 'active')
  const categories = useDataStore((s) => s.categories)

  function getCategoryName(merchant: Merchant) {
    return categories
      .filter((c) => merchant.categoryIds.includes(c.id))
      .map((c) => `${c.icon} ${c.name}`)
      .join(', ')
  }

  return (
    <div style={{ height }} className="rounded-xl overflow-hidden border border-gray-200 shadow-card">
      <MapContainer
        center={[49.4928, 9.7745]}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={19}
        />
        <MapFlyTo merchantId={highlightedId ?? null} merchants={displayMerchants} />
        {displayMerchants.map((merchant) => (
          <Marker
            key={merchant.id}
            position={[merchant.coordinates.lat, merchant.coordinates.lng]}
            icon={createMerchantIcon(merchant.id === highlightedId)}
            eventHandlers={{
              click: () => onMarkerClick?.(merchant.id),
            }}
          >
            <Popup>
              <div className="min-w-[180px] font-sans">
                <div className="aspect-video overflow-hidden rounded-t-md -mx-2 -mt-2 mb-3">
                  <img
                    src={merchant.images.store}
                    alt={merchant.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="px-1 pb-1">
                  <p className="text-xs text-gray-500 mb-0.5">{getCategoryName(merchant)}</p>
                  <h4 className="font-bold text-gray-900 text-sm leading-tight mb-1">{merchant.name}</h4>
                  <p className="text-xs text-gray-500 mb-2">
                    {merchant.address.street}, {merchant.address.city}
                  </p>
                  {merchant.clickAndCollect && (
                    <p className="text-xs text-primary-700 font-medium mb-2">✓ Click & Collect</p>
                  )}
                  <Link
                    to={`/haendler/${merchant.slug}`}
                    className="block text-center text-xs font-semibold bg-primary-700 text-white py-1.5 px-3 rounded-lg hover:bg-primary-800 transition-colors"
                  >
                    Profil ansehen →
                  </Link>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
