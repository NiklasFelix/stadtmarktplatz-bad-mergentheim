# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Beschreibung fuer die Desktop-Fassung.

Bauen mit:   .venv\Scripts\python.exe -m PyInstaller orkan.spec --noconfirm

ACHTUNG: Die erzeugte .exe enthaelt den vollstaendigen Artikel-Datenpool.
Sie darf nur an OrKan-Mitarbeiter weitergegeben werden, nicht an Kunden.
"""

daten = [
    ('daten/Datenpool_bereinigt.csv', 'daten'),
    ('referenz/Importformat_39_Spalten_Vorlage.csv', 'referenz'),
    # Ganzes Verzeichnis, damit ein hinterlegtes Logo mitgeht.
    ('app/static', 'app/static'),
]

versteckt = [
    'uvicorn.logging',
    'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.loops.asyncio',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off',
    'anyio._backends._asyncio',
    'openpyxl.cell._writer',
    'app', 'app.main', 'app.config', 'app.pool', 'app.matching',
    'app.parsing', 'app.export', 'app.queue_store', 'app.jobs',
    'app.pdf_extract', 'app.text',
]

# Nicht gebraucht - spart deutlich Platz.
raus = [
    'tkinter', 'test', 'unittest', 'pydoc', 'doctest',
    'matplotlib', 'PIL.ImageQt', 'PyQt5', 'PySide2',
    'reportlab', 'pytest', 'IPython', 'notebook',
]

a = Analysis(
    ['desktop.py'],
    pathex=[],
    binaries=[],
    datas=daten,
    hiddenimports=versteckt,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=raus,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OrKan-Artikel-Matching',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
