# Release v1.1 – Live-Track Web-Dashboard & Demo-Pack

**Version:** v1.1
**Datum:** 2025-12-08
**Scope:** Live-Track Web-Dashboard, Operator-Demos & Onboarding

## 1. Kurz-Übersicht

Release v1.1 erweitert den Peak_Trade Live-Track-Stack um ein vollständiges Demo- und Onboarding-Paket rund um das Web-Dashboard:

- **Live-Track Web-Dashboard v1.1** – Operator-Ansicht für Shadow-/Testnet-Sessions
- **Phase-84-Demo-Walkthrough** – End-to-End-Flow: CLI → Registry → Dashboard
- **2-Minuten-Demo-Script** – kompaktes Moderations-Script inkl. Cheat-Sheet
- **Playbook-How-To** – Abschnitt 12.5 als schnelle Demo-Anleitung für Operatoren

Zielgruppe: Operatoren, Onboarding, interne Showcases und Stakeholder-Demos.

## 2. Kern-Features

### 2.1 Live-Track Web-Dashboard v1.1

- System-Header mit **Betriebsmodus, Tiering und Live-Lock / Safety-Lock**
- Status-Kacheln für:
  - Anzahl und Verteilung von Shadow-/Testnet-Sessions
  - Letzte Runs / jüngste Aktivität
- Session-Tabelle mit:
  - Registrierten Live-/Shadow-Sessions aus der Registry
  - Kontext-Informationen für Operatoren (Mode, Tier, Zeit, Status)
- **Safety-Fokus:** Live-Mode bleibt über Safety-Gates blockiert, Demo-Flow läuft rein in Shadow-/Testnet.

Dokumentiert in:

- `docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`
  - Abschnitt **4.10 – Web-Dashboard v1.1 – Live-Track Operator View**
  - Abschnitt **4.11 – Live-Track Web-Dashboard v1.1 – Demo & Onboarding**

### 2.2 Phase 84 – Demo-Walkthrough

- Vollständige Schritt-für-Schritt-Anleitung für eine Demo-Session:
  - System-Check
  - Shadow-/Testnet-Session starten (`run_execution_session.py`)
  - Registry/Report per CLI
  - Verifikation im Web-Dashboard
- Inklusive **Storyboard** mit idealer Demo-Session und Operator-Perspektive.

Dokument:

- `docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`

### 2.3 2-Minuten-Demo-Script

- Kompaktes Script für eine **ca. 2-minütige Dashboard-Demo**
- Struktur:
  - Einstieg & Kontext
  - System-Header & Safety-Botschaft
  - Stats-Kacheln & Session-Tabelle
  - Abschluss mit Brücke CLI ↔ Dashboard
- Enthält ein kleines Cheat-Sheet für Moderator:innen.

Dokument:

- `docs/DEMO_SCRIPT_DASHBOARD_V11.md`

### 2.4 Playbook-How-To (Operator-Fokus)

- Neuer Abschnitt im Live-Playbook:

  - `docs/LIVE_DEPLOYMENT_PLAYBOOK.md`
    - **Abschnitt 12.5 – Kurz-How-To: Live-Track Dashboard Demo (ca. 2 Minuten)**

- High-Level-Ablauf:
  1. CLI → Registry zeigen
  2. Web-Dashboard öffnen
  3. System-Header & Safety hervorheben
  4. Sessions & Status-Kacheln kurz erklären
  5. Brücke CLI ↔ Dashboard

Damit haben Operatoren neben den Runbooks ein **reproduzierbares Demo-Format** für den Live-Track-Stack.

## 3. Safety & Scope

- **Keine echten Live-Orders** – Demo-Stack nutzt ausschließlich Shadow-/Testnet-Mode.
- Live-Mode bleibt durch bestehende Safety-Gates blockiert.
- Release v1.1 ändert **keine** Kern-Execution- oder Risk-Logik, sondern ergänzt:
  - UI-Ansicht
  - Demo-/Onboarding-Dokumentation
  - Operator-How-Tos

## 4. Dateien & Referenzen

- `docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`
  - 4.10 Web-Dashboard v1.1 – Live-Track Operator View
  - 4.11 Live-Track Web-Dashboard v1.1 – Demo & Onboarding
- `docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`
- `docs/DEMO_SCRIPT_DASHBOARD_V11.md`
- `docs/LIVE_DEPLOYMENT_PLAYBOOK.md`
  - 12.5 Kurz-How-To: Live-Track Dashboard Demo (ca. 2 Minuten)

## 5. Upgrade-Hinweise

- Code- und Doku-Änderungen sind rückwärtskompatibel zum bestehenden Live-/Shadow-/Testnet-Stack.
- Für eine Demo wird empfohlen:
  - Mindestens eine frische Shadow-/Testnet-Session zu starten.
  - Dashboard-URL vorab zu testen.
  - Demo-Script kurz zu lesen (2-Minuten-Variante reicht).
