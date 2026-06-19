// Regelbasierte Aufteilung langer Artikelbeschreibungen in
// Bezeichnung 1 (Artikelname) / 2 (Abmessung) / 3 (Material/Zusatz),
// inkl. Abgleich gegen hochgeladene Referenz-Artikeldatenbanken.

export const MAX_FIELD_LENGTH = 25

export interface ReferenceEntry {
  artikelnummer: string
  bezeichnung1: string
  bezeichnung2: string
  bezeichnung3: string
}

export type ReferenceMap = Map<string, ReferenceEntry>

export type MatchSource = 'referenz1' | 'referenz2' | 'automatisch'

export interface ProcessedRow {
  artikelnummer: string
  beschreibungLang: string
  bezeichnung1: string
  bezeichnung2: string
  bezeichnung3: string
  quelle: MatchSource
  /** Maßangabe ohne erkennbare Einheit im Originaltext (z. B. "13×100" ohne "mm") */
  einheitUnklar: boolean
  /** Ein Feld wurde abgekürzt, um auf 25 Zeichen zu passen */
  gekuerzt: boolean
  /** Inhalt aus Spalte B konnte trotz Abkürzung nicht verlustfrei in 3x25 Zeichen untergebracht werden */
  verlust: boolean
}

export function normalizeArticleNumber(value: string): string {
  return String(value ?? '').trim().toUpperCase()
}

// Bekannte Einheiten/Maß-Präfixe, die einen Maßangaben-Block einleiten oder fortsetzen können
const UNIT_WORDS = [
  'mm', 'cm', 'dm', 'm', 'km', 'ml', 'cl', 'l', 'kg', 'g', 'mg', 't',
  'v', 'w', 'a', 'hz', 'kw', 'bar', 'pn', 'dn', 'nw', 'sw', 'ig', 'ag', 'zoll',
]

function stripPunct(token: string): string {
  return token.replace(/[.,;:]+$/g, '')
}

function isUnitWordToken(token: string): boolean {
  return UNIT_WORDS.includes(stripPunct(token).toLowerCase())
}

function isDimensionToken(token: string): boolean {
  const t = token.trim()
  if (!/\d/.test(t)) return false
  if (/^[\d.,]+$/.test(t)) return true // reine Zahl: "13", "100", "0,5"
  if (/^(dn|pn|nw|sw|g|m|r)\d/i.test(t)) return true // DN15, M8, G1/2, R1/2
  if (/[×x*]/i.test(t) && /\d/.test(t)) return true // 13×100, M8x40
  if (/^\d+[.,]?\d*\/\d+/.test(t)) return true // 1/2, 3/4
  if (/\d+["']$/.test(t)) return true // 1/2", 15'
  if (/^[øØ]\d/.test(t)) return true // Ø20
  if (/\d(mm|cm|dm|km|ml|cl|kg|mg|hz|kw|bar|v|w|a)\b/i.test(t)) return true // 15mm, 230v
  if (/°/.test(t)) return true
  if (/%/.test(t)) return true
  return false
}

function isDimensionRelated(tokens: string[], i: number): boolean {
  const tok = tokens[i]
  if (isDimensionToken(tok)) return true
  // alleinstehendes Multiplikationszeichen zwischen zwei Maßangaben: "50mm x 32mm"
  if (/^[x×*]$/i.test(tok)) {
    const prev = tokens[i - 1]
    const next = tokens[i + 1]
    if ((prev && isDimensionToken(prev)) || (next && isDimensionToken(next))) return true
  }
  if (isUnitWordToken(tok)) {
    const prev = tokens[i - 1]
    const next = tokens[i + 1]
    if (prev && isDimensionToken(prev)) return true
    if (next && isDimensionToken(next)) return true
  }
  return false
}

function findDimensionRun(tokens: string[]): { start: number; end: number } | null {
  let bestStart = -1
  let bestLen = 0
  let i = 0
  while (i < tokens.length) {
    if (isDimensionRelated(tokens, i)) {
      let j = i
      while (j < tokens.length && isDimensionRelated(tokens, j)) j++
      if (j - i > bestLen) {
        bestLen = j - i
        bestStart = i
      }
      i = j
    } else {
      i++
    }
  }
  if (bestStart === -1) return null
  return { start: bestStart, end: bestStart + bestLen }
}

// Bekannte Material-/Oberflächen-Begriffe, die typischerweise am Ende stehen.
// Wird nur als Fallback genutzt, wenn keine Maßangabe gefunden wurde.
const MATERIAL_WORDS = [
  'verzinkt', 'edelstahl', 'messing', 'kunststoff', 'pvc', 'stahl', 'alu', 'aluminium',
  'inox', 'v2a', 'v4a', 'gelb', 'blau', 'rot', 'schwarz', 'weiss', 'weiß', 'transparent',
  'guss', 'bronze', 'kupfer', 'gummi', 'silikon', 'chrom', 'verchromt', 'lackiert',
  'c-stahl', 'cstahl', 'feuerverzinkt', 'rostfrei', 'beschichtet',
]

function findTrailingMaterialStart(tokens: string[]): number {
  let i = tokens.length
  while (i > 0) {
    const t = stripPunct(tokens[i - 1]).toLowerCase()
    if (MATERIAL_WORDS.includes(t)) {
      i--
    } else {
      break
    }
  }
  return i === tokens.length ? tokens.length : i
}

// Häufige Abkürzungen, um Felder auf 25 Zeichen zu bringen, ohne Wortteile zu verlieren.
const ABBREVIATIONS: [RegExp, string][] = [
  [/Edelstahl/gi, 'Edelst.'],
  [/Aluminium/gi, 'Alu'],
  [/verzinkt/gi, 'verz.'],
  [/Kunststoff/gi, 'Kunstst.'],
  [/Schrauben/gi, 'Schr.'],
  [/Schraube/gi, 'Schr.'],
  [/Dichtung/gi, 'Dicht.'],
  [/Verschraubung/gi, 'Verschr.'],
  [/Übergang/gi, 'Überg.'],
  [/feuerverzinkt/gi, 'fverz.'],
  [/rostfrei/gi, 'rostfr.'],
  [/beschichtet/gi, 'besch.'],
  [/lackiert/gi, 'lack.'],
]

interface FitResult {
  value: string
  overflow: string
  abbreviated: boolean
}

function fitField(text: string, maxLen = MAX_FIELD_LENGTH): FitResult {
  if (text.length <= maxLen) return { value: text, overflow: '', abbreviated: false }
  let abbreviated = text
  for (const [pattern, replacement] of ABBREVIATIONS) {
    abbreviated = abbreviated.replace(pattern, replacement)
  }
  if (abbreviated.length <= maxLen) return { value: abbreviated, overflow: '', abbreviated: true }
  const cut = abbreviated.slice(0, maxLen)
  const lastSpace = cut.lastIndexOf(' ')
  const splitAt = lastSpace > maxLen * 0.5 ? lastSpace : maxLen
  return {
    value: abbreviated.slice(0, splitAt).trim(),
    overflow: abbreviated.slice(splitAt).trim(),
    abbreviated: true,
  }
}

export interface SplitResult {
  bezeichnung1: string
  bezeichnung2: string
  bezeichnung3: string
  einheitUnklar: boolean
  gekuerzt: boolean
  verlust: boolean
}

export function splitDescription(description: string): SplitResult {
  const raw = (description ?? '').trim()
  const tokens = raw.split(/\s+/).filter(Boolean)

  let nameTokens: string[]
  let dimTokens: string[]
  let restTokens: string[]

  const run = findDimensionRun(tokens)
  if (run) {
    nameTokens = tokens.slice(0, run.start)
    dimTokens = tokens.slice(run.start, run.end)
    restTokens = tokens.slice(run.end)
  } else {
    const materialStart = findTrailingMaterialStart(tokens)
    nameTokens = tokens.slice(0, materialStart)
    dimTokens = []
    restTokens = tokens.slice(materialStart)
  }

  // Maßangabe darf nicht das allererste Token "schlucken" und den Namen leeren
  if (nameTokens.length === 0 && dimTokens.length > 1) {
    nameTokens = [dimTokens[0]]
    dimTokens = dimTokens.slice(1)
  }

  const einheitUnklar =
    dimTokens.length > 0 && dimTokens.every((t) => /^[\d.,×x*/"'\-]+$/i.test(t))

  const f1 = fitField(nameTokens.join(' '))
  const f2 = fitField([f1.overflow, dimTokens.join(' ')].filter(Boolean).join(' '))
  const f3 = fitField([f2.overflow, restTokens.join(' ')].filter(Boolean).join(' '))

  return {
    bezeichnung1: f1.value,
    bezeichnung2: f2.value,
    bezeichnung3: f3.value,
    einheitUnklar,
    gekuerzt: f1.abbreviated || f2.abbreviated || f3.abbreviated,
    verlust: f3.overflow.length > 0,
  }
}

export function processRow(
  artikelnummer: string,
  beschreibung: string,
  ref1?: ReferenceMap,
  ref2?: ReferenceMap
): ProcessedRow {
  const key = normalizeArticleNumber(artikelnummer)
  const hit1 = ref1?.get(key)
  const hit2 = !hit1 ? ref2?.get(key) : undefined
  const hit = hit1 ?? hit2

  if (hit) {
    return {
      artikelnummer,
      beschreibungLang: beschreibung,
      bezeichnung1: hit.bezeichnung1,
      bezeichnung2: hit.bezeichnung2,
      bezeichnung3: hit.bezeichnung3,
      quelle: hit1 ? 'referenz1' : 'referenz2',
      einheitUnklar: false,
      gekuerzt: false,
      verlust: false,
    }
  }

  const split = splitDescription(beschreibung)
  return {
    artikelnummer,
    beschreibungLang: beschreibung,
    bezeichnung1: split.bezeichnung1,
    bezeichnung2: split.bezeichnung2,
    bezeichnung3: split.bezeichnung3,
    quelle: 'automatisch',
    einheitUnklar: split.einheitUnklar,
    gekuerzt: split.gekuerzt,
    verlust: split.verlust,
  }
}

// --- Persistenz der Referenzdatenbanken (localStorage), damit sie nicht bei jedem Lauf neu hochgeladen werden müssen ---

export const REF1_STORAGE_KEY = 'artikel-splitter:referenz-1'
export const REF2_STORAGE_KEY = 'artikel-splitter:referenz-2'

export interface ReferenceMeta {
  fileName: string
  count: number
}

export function saveReferenceMapToStorage(storageKey: string, map: ReferenceMap, meta: ReferenceMeta) {
  localStorage.setItem(storageKey, JSON.stringify({ meta, entries: Array.from(map.entries()) }))
}

export function loadReferenceMapFromStorage(
  storageKey: string
): { map: ReferenceMap; meta: ReferenceMeta } | null {
  const raw = localStorage.getItem(storageKey)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as { meta: ReferenceMeta; entries: [string, ReferenceEntry][] }
    return { map: new Map(parsed.entries), meta: parsed.meta }
  } catch {
    return null
  }
}

export function clearReferenceMapStorage(storageKey: string) {
  localStorage.removeItem(storageKey)
}
