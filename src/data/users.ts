import type { User } from '../types'

// Demo-Benutzer für die Simulation
// Passwörter sind hier nur für die Demo-Anzeige – kein echtes Auth-System
export const DEMO_USERS: User[] = [
  {
    id: 'user-1',
    email: 'anna.weber@example.de',
    name: 'Anna Weber',
    role: 'customer',
    avatarUrl: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80',
    createdAt: '2024-03-15T10:00:00.000Z',
  },
  {
    id: 'user-2',
    email: 'buchhandlung@stadtmarkt-bm.de',
    name: 'Klaus Leser',
    role: 'merchant',
    avatarUrl: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=100&q=80',
    createdAt: '2024-01-10T09:00:00.000Z',
  },
  {
    id: 'user-3',
    email: 'mode-zimmermann@stadtmarkt-bm.de',
    name: 'Sabine Zimmermann',
    role: 'merchant',
    avatarUrl: 'https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=100&q=80',
    createdAt: '2024-01-12T09:00:00.000Z',
  },
  {
    id: 'user-4',
    email: 'feinkost@stadtmarkt-bm.de',
    name: 'Thomas Maier',
    role: 'merchant',
    avatarUrl: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&q=80',
    createdAt: '2024-01-14T09:00:00.000Z',
  },
  {
    id: 'user-5',
    email: 'admin@stadtmarkt-bm.de',
    name: 'Maria Stadtler',
    role: 'admin',
    avatarUrl: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&q=80',
    createdAt: '2023-12-01T09:00:00.000Z',
  },
  {
    id: 'user-6',
    email: 'blumen@stadtmarkt-bm.de',
    name: 'Lisa Rose',
    role: 'merchant',
    avatarUrl: 'https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=100&q=80',
    createdAt: '2024-01-20T09:00:00.000Z',
  },
  {
    id: 'user-7',
    email: 'spielzeug@stadtmarkt-bm.de',
    name: 'Peter König',
    role: 'merchant',
    avatarUrl: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80',
    createdAt: '2024-02-01T09:00:00.000Z',
  },
]

// Demo-Login-Accounts für Rollenwechsel
export const DEMO_ACCOUNTS = [
  {
    label: 'Kunde (Anna Weber)',
    userId: 'user-1',
    role: 'customer' as const,
    description: 'Kundenprofil mit Reservierungen & Favoriten',
  },
  {
    label: 'Händler: Buchhandlung Lesezeit',
    userId: 'user-2',
    role: 'merchant' as const,
    merchantId: 'merchant-1',
    description: 'Händler-Dashboard mit Reservierungen & Produkten',
  },
  {
    label: 'Händler: Modehaus Zimmermann',
    userId: 'user-3',
    role: 'merchant' as const,
    merchantId: 'merchant-2',
    description: 'Händler-Dashboard mit Reservierungen & Produkten',
  },
  {
    label: 'Admin (Wirtschaftsförderung)',
    userId: 'user-5',
    role: 'admin' as const,
    description: 'Vollzugriff auf Plattformverwaltung',
  },
]
