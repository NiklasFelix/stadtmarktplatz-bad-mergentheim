# OrKan Cloud – Prototypen (Bachelorarbeit Niklas Pietsch)

Zwei eigenständige HTML-Prototypen für den Pilotversuch (Kapitel 4.1.3 und 4.2.3).

## Prototyp 1: Interaktive Lernplattform (Anwendungsfall 1)
**Datei:** `onboarding-lernplattform.html`

Digitales Onboarding für neue OrKan Cloud-Kunden. Ersetzt die bisher manuellen 3-stündigen Schulungen.

**Funktionen:**
- 5 interaktive Lernmodule mit Lernpfad-Navigation
- Fortschrittsanzeige (Modul-basiert, freigeschaltet nach Abschluss)
- Video-Platzhalter (Synthesia / Loom KI-Videos in Produktion)
- Wissenschecks (Quiz) am Ende jedes Moduls
- Lernstatistik & digitales Onboarding-Zertifikat
- Zeitmessung für den Pilotversuch nutzbar

**Gemessene Inhalte:**
- Modul 1: Grundlagen OrKan Cloud (~12 Min.)
- Modul 2: Artikel & Lagerplätze (~15 Min.)
- Modul 3: Kanban-Prozess (~10 Min.)
- Modul 4: Schnittstellen & Import (~18 Min.)
- Modul 5: Jahres- & Listungsgespräch (~8 Min.)

---

## Prototyp 2: KI-Support-Chatbot (Anwendungsfall 2)
**Datei:** `orkan-support-chatbot.html`

Automatisierte Beantwortung wiederkehrender Supportfragen zur OrKan Cloud.

**Funktionen:**
- Chat-Interface mit natürlichsprachiger Eingabe
- Wissensdatenbank mit 14 Themenblöcken (häufigste Supportfragen)
- Keyword-basierte Antwortlogik (simuliert LLM-Verhalten für den Pilot)
- Schnellfragen-Buttons für häufige Themen
- Automatische Eskalation bei unbekannten Fragen
- Nutzerfeedback pro Antwort (👍/👎)
- Pilot-Statistik: beantwortete Fragen, Eskalationsrate, positive Bewertungen

**Abgedeckte Themen:**
CSV-Import, ERP-Schnittstellen/API, Mindestmenge, Bestellvorschläge, Lieferanten,
Benutzerrollen, Berichte/KPIs, QR-Scan, Wareneingang, Passwort/Login

---

## Nutzung

Beide Dateien sind **selbstständige HTML-Dateien** ohne externe Abhängigkeiten.
Einfach im Browser öffnen:

```
prototypes/onboarding-lernplattform.html
prototypes/orkan-support-chatbot.html
```

Kein Build-Prozess, kein Server erforderlich.

---

## Evaluierungshinweise (Pilotversuch)

Für den Pilotversuch (Kap. 4.1.3 / 4.2.3) empfiehlt sich:

**Lernplattform:**
- Zeit von Beginn bis Abschluss messen
- Quiz-Ergebnisse (Richtig/Falsch-Quote) protokollieren
- Nutzerfeedback nach Abschluss via separatem Fragebogen erheben

**Chatbot:**
- Eskalationsrate beobachten (Ziel: < 20 %)
- Antwortqualität durch interne Experten bewerten
- Vergleich: manuelle Supportzeit vorher vs. Chatbot-Bearbeitungszeit
