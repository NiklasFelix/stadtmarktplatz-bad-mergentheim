import * as XLSX from 'xlsx'
import { normalizeArticleNumber, type ProcessedRow, type ReferenceMap } from './articleSplitter'

export interface RawArticleRow {
  artikelnummer: string
  beschreibung: string
}

function cell(row: unknown[], index: number): string {
  const value = row[index]
  return value == null ? '' : String(value).trim()
}

function looksLikeHeaderRow(a: string, b: string): boolean {
  const al = a.toLowerCase()
  const bl = b.toLowerCase()
  return (
    al.includes('artikelnummer') ||
    al.includes('artikel-nr') ||
    al === 'nr' ||
    bl.includes('bezeichnung') ||
    bl.includes('beschreibung')
  )
}

async function readSheetRows(file: File): Promise<unknown[][]> {
  const buffer = await file.arrayBuffer()
  const workbook = XLSX.read(buffer, { type: 'array' })
  const sheet = workbook.Sheets[workbook.SheetNames[0]]
  if (!sheet) throw new Error('Die Datei enthält kein lesbares Tabellenblatt.')
  return XLSX.utils.sheet_to_json<unknown[]>(sheet, { header: 1, raw: false, defval: '' })
}

export async function readMainList(file: File): Promise<RawArticleRow[]> {
  const rows = await readSheetRows(file)
  const result: RawArticleRow[] = []
  rows.forEach((row, index) => {
    const artikelnummer = cell(row, 0)
    const beschreibung = cell(row, 1)
    if (!artikelnummer && !beschreibung) return
    if (index === 0 && looksLikeHeaderRow(artikelnummer, beschreibung)) return
    result.push({ artikelnummer, beschreibung })
  })
  return result
}

export async function readReferenceFile(file: File): Promise<ReferenceMap> {
  const rows = await readSheetRows(file)
  const map: ReferenceMap = new Map()
  rows.forEach((row, index) => {
    const artikelnummer = cell(row, 0)
    const beschreibungLang = cell(row, 1)
    if (!artikelnummer) return
    if (index === 0 && looksLikeHeaderRow(artikelnummer, beschreibungLang)) return
    map.set(normalizeArticleNumber(artikelnummer), {
      artikelnummer,
      bezeichnung1: cell(row, 2),
      bezeichnung2: cell(row, 3),
      bezeichnung3: cell(row, 4),
    })
  })
  return map
}

export function exportResults(rows: ProcessedRow[], filename: string) {
  const header = ['Artikelnummer', 'Bezeichnung lang', 'Bezeichnung 1', 'Bezeichnung 2', 'Bezeichnung 3']
  const data = rows.map((r) => [r.artikelnummer, r.beschreibungLang, r.bezeichnung1, r.bezeichnung2, r.bezeichnung3])
  const sheet = XLSX.utils.aoa_to_sheet([header, ...data])
  sheet['!cols'] = [{ wch: 14 }, { wch: 42 }, { wch: 25 }, { wch: 25 }, { wch: 25 }]
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, sheet, 'Artikel')
  XLSX.writeFile(workbook, filename)
}
