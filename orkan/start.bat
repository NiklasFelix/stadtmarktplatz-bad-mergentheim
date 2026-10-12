@echo off
setlocal
cd /d "%~dp0"
title OrKan Artikel-Matching-Tool
set PORT=8000

REM ---------------------------------------------------------------
REM  Voraussetzungen pruefen
REM ---------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   FEHLER: Die Programmumgebung .venv fehlt.
  echo.
  echo   Bitte einmalig ausfuehren:
  echo     python -m venv .venv
  echo     .venv\Scripts\pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

if not exist "daten\Datenpool_bereinigt.csv" (
  echo.
  echo   FEHLER: Der Datenpool fehlt.
  echo.
  echo   Erwartet wird:  daten\Datenpool_bereinigt.csv
  echo   Siehe dazu:     daten\LIESMICH.txt
  echo.
  pause
  exit /b 1
)

REM ---------------------------------------------------------------
REM  Laeuft schon etwas auf dem Port?
REM ---------------------------------------------------------------
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue) { exit 1 }"
if errorlevel 1 (
  echo.
  echo   HINWEIS: Port %PORT% wird bereits benutzt.
  echo   Vermutlich laeuft das Programm schon in einem anderen Fenster.
  echo.
  echo   Dann erreichen Sie es einfach unter:  http://localhost:%PORT%
  echo.
  choice /c JN /n /m "   Laufenden Dienst beenden und neu starten? [J/N] "
  if errorlevel 2 (
    echo.
    echo   Abgebrochen - das bereits laufende Programm bleibt aktiv.
    echo.
    pause
    exit /b 0
  )
  echo.
  echo   Beende den laufenden Dienst ...
  powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { $eltern = $_; Get-CimInstance Win32_Process -Filter ('ParentProcessId=' + $eltern) -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; Stop-Process -Id $eltern -Force -ErrorAction SilentlyContinue }"
  powershell -NoProfile -Command "Start-Sleep -Seconds 2"
  powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue) { exit 1 }"
  if errorlevel 1 (
    echo.
    echo   Der Port liess sich nicht freigeben. Bitte Windows neu starten
    echo   oder den blockierenden Prozess im Task-Manager beenden.
    echo.
    pause
    exit /b 1
  )
)

REM ---------------------------------------------------------------
REM  Zugangsdaten fuer den Admin-Bereich - vor dem Produktivbetrieb aendern!
REM ---------------------------------------------------------------
set ADMIN_USER=pruefer
set ADMIN_PASSWORT=bitte-aendern

REM Erlaubt die Eingabe des Bildordners in der Oberflaeche. Auf einem Server
REM mit mehreren Nutzern weglassen - dort gehoert der Pfad in BILDPOOL_PFAD.
set BILDPOOL_EINGABE=1

cls
echo.
echo  ==========================================================
echo   OrKan Artikel-Matching-Tool
echo  ==========================================================
echo.
echo   Auf diesem Rechner:   http://localhost:%PORT%
powershell -NoProfile -Command "$a = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | Sort-Object InterfaceMetric; if ($a) { $a | ForEach-Object { '   Fuer Kollegen:       http://' + $_.IPAddress + ':%PORT%' } } else { '   Fuer Kollegen:       (keine Netzwerkverbindung gefunden)' }"
echo.
echo   Neuaufnahmen pruefen: http://localhost:%PORT%/admin/neuaufnahmen
echo   Anmeldung dort:       %ADMIN_USER% / %ADMIN_PASSWORT%
echo.
echo   Bildordner:           in der Oberflaeche eingebbar
echo   Beenden mit:          Strg + C   (oder Fenster schliessen)
echo.
echo  ==========================================================
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port %PORT%

echo.
echo   Der Dienst wurde beendet.
pause
