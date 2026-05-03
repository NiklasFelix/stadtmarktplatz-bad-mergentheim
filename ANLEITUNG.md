# Stadtmarktplatz Bad Mergentheim – Startanleitung

## Voraussetzung: Node.js installieren

Node.js ist auf diesem System noch nicht installiert. Bitte zuerst installieren:

**Option 1 – Winget (empfohlen):**
```powershell
winget install OpenJS.NodeJS.LTS
```

**Option 2 – Download:**
Gehen Sie auf https://nodejs.org und laden Sie die LTS-Version herunter und installieren Sie sie.

Nach der Installation PowerShell neu starten, damit npm verfügbar ist.

---

## Projekt starten

```bash
# 1. In Projektordner wechseln
cd C:\Users\nfppi\stadtmarktplatz-bad-mergentheim

# 2. Abhängigkeiten installieren (einmalig)
npm install

# 3. Entwicklungsserver starten
npm run dev
```

Die App öffnet sich unter: **http://localhost:5173**

---

## Demo-Rollen

Klicken Sie oben rechts auf "Anmelden" und wählen Sie eine Demo-Rolle:

| Rolle | Bereich | Zugang |
|-------|---------|--------|
| **Kunde (Anna Weber)** | Öffentliche Seite, Profil, Favoriten | / , /profil, /favoriten |
| **Händler: Buchhandlung Lesezeit** | Händler-Dashboard | /seller |
| **Händler: Modehaus Zimmermann** | Händler-Dashboard | /seller |
| **Admin (Wirtschaftsförderung)** | Admin-Bereich | /admin |

---

## Projektstruktur

```
stadtmarktplatz-bad-mergentheim/
├── src/
│   ├── data/               ← Mock-Daten (Händler, Produkte, Reservierungen)
│   │   ├── merchants.ts    ← 8 Händler mit Koordinaten für Bad Mergentheim
│   │   ├── products.ts     ← 24 Produkte mit Bildern und Beschreibungen
│   │   ├── reservations.ts ← 8 Demo-Reservierungen in verschiedenen Status
│   │   ├── categories.ts   ← 9 Kategorien
│   │   └── users.ts        ← Demo-Benutzer für Rollenwechsel
│   ├── store/              ← Zustand-Stores (Zustand-Library)
│   │   ├── useAuthStore.ts ← Authentifizierung & Rollen
│   │   ├── useDataStore.ts ← Alle Daten (Händler, Produkte, Reservierungen)
│   │   └── useCustomerStore.ts ← Favoriten & gemerkte Produkte
│   ├── services/
│   │   └── api.ts          ← Mock-Service-Layer (für echtes Backend ersetzen)
│   ├── components/         ← Wiederverwendbare UI-Komponenten
│   ├── pages/              ← Seitenkomponenten nach Bereich
│   │   ├── public/         ← Öffentliche Seiten
│   │   ├── seller/         ← Händlerbereich
│   │   └── admin/          ← Adminbereich
│   └── types/index.ts      ← TypeScript-Typen (vollständiges Datenmodell)
```

---

## Echtes Backend anbinden

Die Datei `src/services/api.ts` enthält alle API-Funktionen als Mock-Implementierungen.
Um ein echtes Backend anzubinden:

1. `VITE_API_URL=https://ihre-api.de` in `.env` setzen
2. In `src/services/api.ts` die Mock-Logik durch `fetch()` / `axios()` ersetzen:

```typescript
// Vorher (Mock):
export async function getMerchants() {
  return useDataStore.getState().merchants
}

// Nachher (echtes Backend):
export async function getMerchants() {
  const res = await fetch(`${import.meta.env.VITE_API_URL}/merchants`)
  return res.json()
}
```

---

## Build für Produktion

```bash
npm run build
# Ausgabe liegt in dist/ – kann auf jeden Static-Host deployed werden
```

---

## Technologie-Stack

- **React 18 + TypeScript** – Komponenten-Framework
- **Vite** – Build-Tool (schnell, modular)
- **React Router v6** – Client-seitiges Routing
- **Zustand** – State-Management
- **Tailwind CSS 3** – Utility-first Styling
- **React Leaflet + Leaflet** – OpenStreetMap-Karte
- **React Hook Form** – Formularvalidierung
- **Lucide React** – Icon-Library
- **date-fns** – Datumsformatierung
