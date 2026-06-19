import { useEffect, useRef, useState } from 'react'
import {
  Upload, Download, FileSpreadsheet, X, AlertTriangle, CheckCircle2, Sparkles, Database, Loader2,
} from 'lucide-react'
import { clsx } from 'clsx'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/ui/EmptyState'
import {
  MAX_FIELD_LENGTH,
  REF1_STORAGE_KEY,
  REF2_STORAGE_KEY,
  clearReferenceMapStorage,
  loadReferenceMapFromStorage,
  processRow,
  saveReferenceMapToStorage,
  type ProcessedRow,
  type ReferenceMap,
} from '../../utils/articleSplitter'
import { exportResults, readMainList, readReferenceFile, type RawArticleRow } from '../../utils/excelIO'

interface RefSlotState {
  map: ReferenceMap | null
  fileName: string
  count: number
}

const EMPTY_REF: RefSlotState = { map: null, fileName: '', count: 0 }

function ReferenceSlot({
  title,
  hint,
  state,
  onUpload,
  onClear,
}: {
  title: string
  hint: string
  state: RefSlotState
  onUpload: (file: File) => void
  onClear: () => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)

  return (
    <div className="card p-4 flex-1 min-w-[260px]">
      <div className="flex items-center gap-2 mb-1">
        <Database size={16} className="text-primary-700" />
        <p className="font-semibold text-gray-900 text-sm">{title}</p>
      </div>
      <p className="text-xs text-gray-400 mb-3">{hint}</p>

      {state.map ? (
        <div className="flex items-center justify-between gap-2 bg-accent-50 border border-accent-200 rounded-lg px-3 py-2">
          <div className="flex items-center gap-2 min-w-0">
            <CheckCircle2 size={16} className="text-accent-500 shrink-0" />
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-800 truncate">{state.fileName}</p>
              <p className="text-xs text-gray-500">{state.count.toLocaleString('de-DE')} Artikel geladen</p>
            </div>
          </div>
          <button onClick={onClear} className="p-1 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 shrink-0">
            <X size={14} />
          </button>
        </div>
      ) : (
        <button
          onClick={() => inputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 rounded-lg py-3 text-sm text-gray-500 hover:border-primary-300 hover:text-primary-700 hover:bg-primary-50 transition-colors"
        >
          <Upload size={15} />
          Datei auswählen
        </button>
      )}
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onUpload(file)
          e.target.value = ''
        }}
      />
    </div>
  )
}

function CharCount({ value }: { value: string }) {
  const over = value.length > MAX_FIELD_LENGTH
  return (
    <span className={clsx('text-[10px] tabular-nums', over ? 'text-red-500 font-semibold' : 'text-gray-300')}>
      {value.length}/{MAX_FIELD_LENGTH}
    </span>
  )
}

export function AdminArticleSplitterPage() {
  const [ref1, setRef1] = useState<RefSlotState>(EMPTY_REF)
  const [ref2, setRef2] = useState<RefSlotState>(EMPTY_REF)
  const [mainRows, setMainRows] = useState<RawArticleRow[]>([])
  const [mainFileName, setMainFileName] = useState('')
  const [results, setResults] = useState<ProcessedRow[]>([])
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const mainInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const r1 = loadReferenceMapFromStorage(REF1_STORAGE_KEY)
    if (r1) setRef1({ map: r1.map, fileName: r1.meta.fileName, count: r1.meta.count })
    const r2 = loadReferenceMapFromStorage(REF2_STORAGE_KEY)
    if (r2) setRef2({ map: r2.map, fileName: r2.meta.fileName, count: r2.meta.count })
  }, [])

  async function handleRefUpload(slot: 1 | 2, file: File) {
    setError('')
    try {
      const map = await readReferenceFile(file)
      const state: RefSlotState = { map, fileName: file.name, count: map.size }
      const storageKey = slot === 1 ? REF1_STORAGE_KEY : REF2_STORAGE_KEY
      if (slot === 1) setRef1(state)
      else setRef2(state)
      saveReferenceMapToStorage(storageKey, map, { fileName: file.name, count: map.size })
    } catch (e) {
      setError(`Referenzdatei konnte nicht gelesen werden: ${(e as Error).message}`)
    }
  }

  function handleRefClear(slot: 1 | 2) {
    const storageKey = slot === 1 ? REF1_STORAGE_KEY : REF2_STORAGE_KEY
    clearReferenceMapStorage(storageKey)
    if (slot === 1) setRef1(EMPTY_REF)
    else setRef2(EMPTY_REF)
  }

  async function handleMainUpload(file: File) {
    setError('')
    setResults([])
    try {
      const rows = await readMainList(file)
      if (rows.length === 0) {
        setError('In der Datei wurden keine Artikelzeilen erkannt. Spalte A = Artikelnummer, Spalte B = Beschreibung.')
        return
      }
      setMainRows(rows)
      setMainFileName(file.name)
    } catch (e) {
      setError(`Datei konnte nicht gelesen werden: ${(e as Error).message}`)
    }
  }

  function runProcessing() {
    setProcessing(true)
    setTimeout(() => {
      const processed = mainRows.map((r) =>
        processRow(r.artikelnummer, r.beschreibung, ref1.map ?? undefined, ref2.map ?? undefined)
      )
      setResults(processed)
      setProcessing(false)
    }, 30)
  }

  function updateCell(index: number, field: 'bezeichnung1' | 'bezeichnung2' | 'bezeichnung3', value: string) {
    setResults((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)))
  }

  function handleExport() {
    const base = mainFileName.replace(/\.(xlsx|xls)$/i, '') || 'artikelliste'
    exportResults(results, `${base}-aufgeteilt.xlsx`)
  }

  const stats = {
    total: results.length,
    referenz: results.filter((r) => r.quelle !== 'automatisch').length,
    automatisch: results.filter((r) => r.quelle === 'automatisch').length,
    warnungen: results.filter((r) => r.einheitUnklar || r.gekuerzt || r.verlust).length,
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Artikel-Aufteilung</h1>
        <p className="text-gray-500 mt-1">
          Lange Artikelbeschreibungen automatisch in Bezeichnung 1/2/3 aufteilen (max. {MAX_FIELD_LENGTH} Zeichen je Feld).
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-6 text-sm">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {/* Referenzdatenbanken */}
      <div className="mb-6">
        <p className="text-sm font-semibold text-gray-700 mb-2">1. Referenz-Datenbanken (optional, einmalig)</p>
        <p className="text-xs text-gray-400 mb-3">
          Spalten: A = Artikelnummer, B = Bezeichnung lang, C/D/E = Bezeichnung 1/2/3. Bereits bekannte
          Artikelnummern werden 1:1 aus der Referenz übernommen statt automatisch erkannt. Bleibt im Browser
          gespeichert, muss also nicht bei jedem Lauf neu hochgeladen werden.
        </p>
        <div className="flex flex-wrap gap-4">
          <ReferenceSlot
            title="Artikel_Datenbank.xlsx"
            hint="Erste Referenzquelle (wird zuerst geprüft)"
            state={ref1}
            onUpload={(f) => handleRefUpload(1, f)}
            onClear={() => handleRefClear(1)}
          />
          <ReferenceSlot
            title="Artikel_OrKanCloud_Datenbank.xlsx"
            hint="Zweite Referenzquelle (Fallback)"
            state={ref2}
            onUpload={(f) => handleRefUpload(2, f)}
            onClear={() => handleRefClear(2)}
          />
        </div>
      </div>

      {/* Hauptliste */}
      <div className="card p-5 mb-6">
        <p className="text-sm font-semibold text-gray-700 mb-2">2. Neue Artikelliste hochladen</p>
        <p className="text-xs text-gray-400 mb-4">Spalte A = Artikelnummer, Spalte B = lange Artikelbeschreibung.</p>
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="outline" leftIcon={<Upload size={16} />} onClick={() => mainInputRef.current?.click()}>
            Excel-Datei wählen
          </Button>
          <input
            ref={mainInputRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleMainUpload(file)
              e.target.value = ''
            }}
          />
          {mainFileName && (
            <span className="text-sm text-gray-600 flex items-center gap-1.5">
              <FileSpreadsheet size={15} className="text-primary-700" />
              {mainFileName} · {mainRows.length.toLocaleString('de-DE')} Zeilen
            </span>
          )}
          {mainRows.length > 0 && (
            <Button variant="primary" leftIcon={<Sparkles size={16} />} loading={processing} onClick={runProcessing}>
              Verarbeiten
            </Button>
          )}
        </div>
      </div>

      {/* Ergebnis */}
      {processing && (
        <div className="flex items-center justify-center gap-2 text-gray-500 py-12">
          <Loader2 size={18} className="animate-spin" /> Verarbeite Artikel…
        </div>
      )}

      {!processing && results.length === 0 && mainRows.length === 0 && (
        <EmptyState
          icon={<FileSpreadsheet size={40} />}
          title="Noch keine Artikelliste hochgeladen"
          description="Lade oben eine Excel-Datei mit Artikelnummer (Spalte A) und Beschreibung (Spalte B) hoch."
        />
      )}

      {!processing && results.length > 0 && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div className="flex flex-wrap gap-4 text-sm">
              <span className="text-gray-600">
                <strong className="text-gray-900">{stats.total}</strong> Artikel
              </span>
              <span className="text-accent-600">
                <strong>{stats.referenz}</strong> aus Referenz übernommen
              </span>
              <span className="text-primary-700">
                <strong>{stats.automatisch}</strong> automatisch erkannt
              </span>
              {stats.warnungen > 0 && (
                <span className="text-amber-600 flex items-center gap-1">
                  <AlertTriangle size={14} />
                  <strong>{stats.warnungen}</strong> zur Prüfung markiert
                </span>
              )}
            </div>
            <Button variant="primary" leftIcon={<Download size={16} />} onClick={handleExport}>
              Als Excel exportieren
            </Button>
          </div>

          <div className="card overflow-x-auto">
            <div className="max-h-[65vh] overflow-y-auto">
              <table className="w-full text-sm border-collapse">
                <thead className="sticky top-0 bg-gray-50 z-10">
                  <tr className="text-left text-xs text-gray-500 uppercase tracking-wide">
                    <th className="px-3 py-2.5 font-medium">Artikelnr.</th>
                    <th className="px-3 py-2.5 font-medium min-w-[220px]">Bezeichnung lang</th>
                    <th className="px-3 py-2.5 font-medium min-w-[150px]">Bezeichnung 1</th>
                    <th className="px-3 py-2.5 font-medium min-w-[150px]">Bezeichnung 2</th>
                    <th className="px-3 py-2.5 font-medium min-w-[150px]">Bezeichnung 3</th>
                    <th className="px-3 py-2.5 font-medium">Quelle</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {results.map((row, i) => {
                    const hasWarning = row.einheitUnklar || row.gekuerzt || row.verlust
                    return (
                      <tr key={`${row.artikelnummer}-${i}`} className={clsx(hasWarning && 'bg-amber-50/50')}>
                        <td className="px-3 py-1.5 font-mono text-xs text-gray-600 whitespace-nowrap">
                          {row.artikelnummer}
                        </td>
                        <td className="px-3 py-1.5 text-gray-700 align-top">{row.beschreibungLang}</td>
                        {(['bezeichnung1', 'bezeichnung2', 'bezeichnung3'] as const).map((field) => (
                          <td key={field} className="px-3 py-1.5 align-top">
                            <input
                              value={row[field]}
                              onChange={(e) => updateCell(i, field, e.target.value)}
                              className={clsx(
                                'w-full rounded border px-2 py-1 text-sm bg-white',
                                row[field].length > MAX_FIELD_LENGTH
                                  ? 'border-red-300 focus:ring-red-400'
                                  : 'border-gray-200 focus:ring-primary-400',
                                'focus:outline-none focus:ring-2'
                              )}
                            />
                            <CharCount value={row[field]} />
                          </td>
                        ))}
                        <td className="px-3 py-1.5 align-top">
                          {row.quelle === 'referenz1' && (
                            <span className="badge bg-accent-100 text-accent-700">Referenz 1</span>
                          )}
                          {row.quelle === 'referenz2' && (
                            <span className="badge bg-primary-100 text-primary-700">Referenz 2</span>
                          )}
                          {row.quelle === 'automatisch' && (
                            <span className="badge bg-gray-100 text-gray-600">Automatisch</span>
                          )}
                          {hasWarning && (
                            <span
                              className="badge bg-amber-100 text-amber-700 ml-1"
                              title={
                                [
                                  row.einheitUnklar && 'Einheit im Original unklar/fehlt – bitte prüfen',
                                  row.gekuerzt && 'Feld wurde gekürzt/abgekürzt',
                                  row.verlust && 'Text passte nicht vollständig in 3x25 Zeichen',
                                ]
                                  .filter(Boolean)
                                  .join(' · ')
                              }
                            >
                              <AlertTriangle size={11} /> Prüfen
                            </span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
