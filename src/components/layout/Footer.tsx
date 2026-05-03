import { Link } from 'react-router-dom'
import { MapPin, Phone, Mail, ExternalLink, Building2 } from 'lucide-react'

export function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-9 h-9 bg-primary-700 rounded-xl flex items-center justify-center">
                <Building2 size={18} className="text-white" />
              </div>
              <div>
                <div className="font-bold text-white text-sm leading-tight">Stadtmarktplatz</div>
                <div className="text-xs text-gray-400 leading-tight">Bad Mergentheim</div>
              </div>
            </div>
            <p className="text-sm text-gray-400 leading-relaxed">
              Die digitale Plattform für lokale Händler in Bad Mergentheim. Entdecken, reservieren, abholen.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-white font-semibold mb-4 text-sm">Entdecken</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/haendler" className="hover:text-white transition-colors">Alle Händler</Link></li>
              <li><Link to="/produkte" className="hover:text-white transition-colors">Produkte</Link></li>
              <li><Link to="/karte" className="hover:text-white transition-colors">Karte</Link></li>
              <li><Link to="/favoriten" className="hover:text-white transition-colors">Favoriten</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4 text-sm">Händler & Partner</h4>
            <ul className="space-y-2.5 text-sm">
              <li><Link to="/seller" className="hover:text-white transition-colors">Händlerbereich</Link></li>
              <li><a href="#" className="hover:text-white transition-colors">Händler werden</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Click & Collect</a></li>
              <li><a href="#" className="hover:text-white transition-colors">FAQ</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4 text-sm">Kontakt</h4>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start gap-2">
                <MapPin size={14} className="mt-0.5 shrink-0 text-gray-500" />
                <span>Wirtschaftsförderung<br />Bad Mergentheim<br />97980 Bad Mergentheim</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone size={14} className="shrink-0 text-gray-500" />
                <a href="tel:+4979318005" className="hover:text-white transition-colors">07931 / 57-0</a>
              </li>
              <li className="flex items-center gap-2">
                <Mail size={14} className="shrink-0 text-gray-500" />
                <a href="mailto:info@stadtmarktplatz-bm.de" className="hover:text-white transition-colors">info@stadtmarktplatz-bm.de</a>
              </li>
              <li className="flex items-center gap-2">
                <ExternalLink size={14} className="shrink-0 text-gray-500" />
                <a href="#" className="hover:text-white transition-colors">www.bad-mergentheim.de</a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-500">
          <p>© 2026 Stadtmarktplatz Bad Mergentheim – Eine Initiative der Wirtschaftsförderung</p>
          <div className="flex gap-4">
            <a href="#" className="hover:text-gray-300 transition-colors">Datenschutz</a>
            <a href="#" className="hover:text-gray-300 transition-colors">Impressum</a>
            <a href="#" className="hover:text-gray-300 transition-colors">Barrierefreiheit</a>
          </div>
        </div>
      </div>
    </footer>
  )
}
