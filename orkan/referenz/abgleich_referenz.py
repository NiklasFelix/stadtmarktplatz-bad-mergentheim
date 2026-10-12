import pandas as pd
import numpy as np
import re

POOL = '/mnt/user-data/outputs/Datenpool_bereinigt.csv'
OUT = '/mnt/user-data/outputs/'

def _lagerort(bez, gruppe):
    txt = f"{bez} {gruppe}".lower()
    if 'press' in txt and 'kupfer' in txt: return 'Kupferpress'
    if ('löt' in txt or 'loet' in txt) and 'kupfer' in txt: return 'Kupferloet'
    if 'press' in txt and 'edelstahl' in txt: return 'Edelstahlpress'
    if 'press' in txt and 'c-stahl' in txt: return 'C-Stahl-Press'
    if 'mepla' in txt: return 'Mepla'
    if 'mapress' in txt: return 'Mapress'
    if 'gewindestange' in txt: return 'Gewindestangen'
    if pd.notna(gruppe) and str(gruppe).strip(): return str(gruppe).strip()[:24]
    return 'Allgemein'

def _tokens(s):
    return set(re.sub(r'[^a-z0-9äöüß ]',' ', str(s).lower()).split())

def minmax_von_aehnlichen(pool, bez1, gruppe):
    """MinMax-Vorschlag: Median ähnlicher Artikel (gleiche Gruppe, sonst Bezeichnungs-Ähnlichkeit)."""
    kand = pool[pool['LagerMin'].notna()]
    if pd.notna(gruppe):
        g = kand[kand['BezArtikelGruppe'].str.strip().str.lower() == str(gruppe).strip().lower()]
        if len(g) >= 3: kand = g
    tok = _tokens(bez1)
    if tok:
        sim = kand['BezArtikel1'].fillna('').map(lambda b: len(tok & _tokens(b)))
        top = kand[sim >= max(1, sim.max()-0)] if sim.max() > 0 else kand
        if len(top) >= 3: kand = top
    mn = pd.to_numeric(kand['LagerMin'], errors='coerce').median()
    mx = pd.to_numeric(kand['LagerMax'], errors='coerce').median()
    if pd.isna(mn): mn, mx = 1, 2
    return int(round(mn)), int(round(max(mx, mn+1) if pd.notna(mx) else mn*2))

def abgleich(kundenliste, name='Kunde', pool_pfad=POOL, pool_schreiben=True):
    """kundenliste: Spalte 'Artikelnummer' noetig; optional 'Lieferant','Bezeichnung1','Bezeichnung2',
    'Bezeichnung3','Artikelgruppe','Menge' u.a. – werden fuer Neuaufnahmen genutzt."""
    pool = pd.read_csv(pool_pfad, sep=';', dtype=str, encoding='utf-8-sig')
    pool_idx = pool.set_index(pool['ArtikelNrLieferant'].str.strip().str.upper())

    k = kundenliste.copy()
    k['ANR_norm'] = k['Artikelnummer'].astype(str).str.strip().str.upper()

    treffer, fehlt = [], []
    for _, row in k.iterrows():
        anr = row['ANR_norm']
        if anr in pool_idx.index:
            p = pool_idx.loc[anr]
            if isinstance(p, pd.DataFrame): p = p.iloc[0]
            treffer.append((row, p))
        else:
            fehlt.append(row)

    # ===== NEU: Nicht gefundene Artikel in den Pool aufnehmen =====
    neue = []
    for row in fehlt:
        bez1 = row.get('Bezeichnung1', np.nan)
        gruppe = row.get('Artikelgruppe', np.nan)
        mn, mx = minmax_von_aehnlichen(pool, bez1, gruppe)
        lo = _lagerort(f"{bez1} {row.get('Bezeichnung2','')}", gruppe)
        neue.append({
            'ArtikelNrLieferant': str(row['Artikelnummer']).strip(),
            'BezArtikel1': bez1, 'BezArtikel2': row.get('Bezeichnung2', np.nan),
            'BezArtikel3': row.get('Bezeichnung3', np.nan), 'BezArtikelLang': row.get('BezeichnungLang', np.nan),
            'KurzBezeichnung': np.nan, 'BezArtikelGruppe': gruppe,
            'Lager': 'Standard Lager', 'Lagerort': lo, 'BezLagerort': gruppe if pd.notna(gruppe) else lo,
            'LagerMin': mn, 'LagerMax': mx,
            'LagerEinheit': row.get('Einheit', 'Stück'), 'VpeEinheit': np.nan, 'MengeProVPE': np.nan,
            'Werksnummer': row.get('Werksnummer', np.nan), 'HerstellerNr': row.get('Herstellernummer', np.nan),
            'EAN': row.get('EAN', np.nan), 'Bild': np.nan,
            'Lieferanten_alle': row.get('Lieferant', np.nan), 'Anz_Lieferanten': 1 if pd.notna(row.get('Lieferant', np.nan)) else 0,
            'Vorkommen': 1, 'Quellen': f'Kundenliste-{name}',
            'VermutlichTestdaten': 'Nein', 'HatKonflikt': 'Nein', 'KritischerKonflikt': 'Nein',
            'NeuAusKundenliste': 'Ja',
        })
    if neue:
        if 'NeuAusKundenliste' not in pool.columns: pool['NeuAusKundenliste'] = 'Nein'
        pool_neu = pd.concat([pool, pd.DataFrame(neue).astype(str).replace('nan', np.nan)], ignore_index=True)
        if pool_schreiben:
            pool_neu.to_csv(pool_pfad, sep=';', index=False, encoding='utf-8-sig')
        pool_idx = pool_neu.set_index(pool_neu['ArtikelNrLieferant'].str.strip().str.upper())
        for row in fehlt:
            treffer.append((row, pool_idx.loc[str(row['Artikelnummer']).strip().upper()]))

    # ===== Importdatei =====
    rows = []
    for row, p in treffer:
        rows.append({
            'Artikelnr.': np.nan, 'Bezeichnung1': p['BezArtikel1'], 'Bezeichnung2': p['BezArtikel2'],
            'Bezeichnung3': p['BezArtikel3'], 'Bezeichnung lang': p['BezArtikelLang'], 'Verwendungszweck': np.nan,
            'Artikelnummer des Lieferanten': p['ArtikelNrLieferant'],
            'Lieferant': row.get('Lieferant') if pd.notna(row.get('Lieferant', np.nan)) else str(p['Lieferanten_alle']).split(';')[0].strip() if pd.notna(p['Lieferanten_alle']) else np.nan,
            'Lager/Gebäude': 'Standard Lager', 'Lagerort': p['Lagerort'], 'Lagerortbezeichnung': p['BezLagerort'], 'Lagerplatz': np.nan,
            'Artikelgruppe': p['BezArtikelGruppe'], 'Artikeluntergruppe': np.nan,
            'Lager Min': p['LagerMin'], 'Lager Max': p['LagerMax'], 'EK-Preis': np.nan,
            'Lagereinheit': p['LagerEinheit'], 'Mengeneinheit(VPE)': p['VpeEinheit'], 'Menge(VPE)': p['MengeProVPE'],
            'Abw. Bestellmenge': np.nan, 'Abw. Bestelleinheit': np.nan, 'Abw. EK-Preis': np.nan,
            'Werksnummer': p['Werksnummer'], 'Herstellernummer': p['HerstellerNr'], 'EAN': p['EAN'],
            'Matchcode': p['KurzBezeichnung'], 'HTN-Code': np.nan, 'Gewicht (Tara) in kg': np.nan,
            'Höhe': np.nan, 'Breite': np.nan, 'Länge': np.nan, 'Wert in €': np.nan,
            'Satzart': 'ST', 'Bestellfähig': 'True', 'Bestand': '0',
            'Erstellt am': np.nan, 'Geändert am': np.nan, 'Artikelbild': p['Bild'],
        })
    imp = pd.DataFrame(rows)

    # ===== Report =====
    neu_anrs = {n['ArtikelNrLieferant'].upper() for n in neue}
    rep = []
    for row, p in treffer:
        anr = str(row['Artikelnummer']).strip().upper()
        if anr in neu_anrs:
            status = 'NEU IN POOL AUFGENOMMEN - Recherche/Pruefung noetig'
        else:
            mehrere = pd.notna(p['Anz_Lieferanten']) and float(p['Anz_Lieferanten']) > 1
            status = 'GEFUNDEN' + (' - Lieferant waehlen' if mehrere else '')
        rep.append({'Artikelnummer': row['Artikelnummer'], 'Status': status,
                    'Bezeichnung': p['BezArtikel1'], 'Lieferanten_im_Pool': p['Lieferanten_alle'],
                    'MinMax': f"{p['LagerMin']}/{p['LagerMax']}", 'Bild_vorhanden': 'Ja' if pd.notna(p['Bild']) else 'Nein'})
    report = pd.DataFrame(rep)

    imp.to_excel(OUT+f'Importdatei_{name}.xlsx', index=False)
    imp.to_csv(OUT+f'Importdatei_{name}.csv', sep=';', index=False, encoding='utf-8-sig')
    report.to_excel(OUT+f'Abgleich_Report_{name}.xlsx', index=False)
    print(f"Kundenliste: {len(k)} | direkt gefunden: {len(k)-len(neue)} | neu in Pool aufgenommen: {len(neue)}")
    return imp, report, neue

if __name__ == '__main__':
    # DEMO mit Pool-KOPIE (echter Pool bleibt unberuehrt)
    import shutil
    shutil.copy(POOL, '/home/claude/pool_test.csv')
    demo = pd.DataFrame([
        {'Artikelnummer': 'NEU-KPF-2815', 'Bezeichnung1': 'Kupfer Pressfitting Bogen 90°', 'Bezeichnung2': '28mm', 'Artikelgruppe': 'Pressfittings', 'Lieferant': 'Gerhard Sprügel GmbH'},
        {'Artikelnummer': 'NEU-GWS-M10', 'Bezeichnung1': 'Gewindestange M10', 'Bezeichnung2': '1000mm verzinkt', 'Lieferant': 'Adolf Würth'},
        {'Artikelnummer': 'CUS18H'},  # existiert im Pool
    ])
    imp, rep, neue = abgleich(demo, name='DEMO2', pool_pfad='/home/claude/pool_test.csv')
    print()
    print(rep.to_string(index=False))
