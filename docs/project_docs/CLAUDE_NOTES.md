# CLAUDE_NOTES – AI Sessions Log (Peak_Trade)

**Zweck:**
Zentrale Sammelstelle für alle wichtigen AI-Interaktionen (Claude, ChatGPT, Gemini, etc.),
die direkt das Peak_Trade-Projekt betreffen.

---

## 1. Meta

- **Projekt:** Peak_Trade
- **Start der Aufzeichnung:** 2025-12-02
- **Letztes Update:** 2025-12-02
- **Primäre Tools:** Claude, ChatGPT, ggf. Gemini, Cursor, VS Code Copilot

---

## 2. Konventionen

- **Eine Session = ein Unterabschnitt** mit Datum und kurzem Titel.
- **Wichtige Ergebnisse** → kurz unter „Key Outcomes" in Bulletpoints.
- **Konkrete Entscheidungen** → unter „Decisions" festhalten.
- **Offene Punkte** → unter „TODO / Open Questions" sammeln.
- **Follow-up-Tickets** → optional mit Verweis auf Issues/Tasks (z.B. GitHub, Linear, Jira).

---

## 3. Aktuelle Sessions

> Hier kommen alle neuen KI-Sessions rein.
> Ältere Notizen kannst du im Abschnitt „Archivierte Sessions" sammeln oder hier nachtragen.

### 3.1. 2025-12-02 – Projekt-Refactor & Ordnerstruktur

**Tool:** Claude / ChatGPT
**Kontext:** Aufräumen des Peak_Trade-Projektordners, Einführung von `archive/`, `docs/project_docs/`, etc.

**Key Outcomes:**

- Neue Zielstruktur für `Peak_Trade/` definiert (inkl. `archive/`, `docs/…`, `scripts/`).
- Skript `scripts/reorganize_peak_trade.py` eingeführt:
  - verschiebt/benennt Dateien idempotent um,
  - unterstützt `--dry-run`.
- Klare Checkliste nach Reorganisation (archive/, config/config.toml, docs-Struktur, CHANGELOG, RISK_MANAGEMENT etc.).

**Decisions:**

- Dokumentation wird in `docs/project_docs/` zentralisiert.
- Alte Stände (z.B. `PeakTradeRepo/`, `full_files_stand_02.12.2025`) wandern nach `archive/`.
- `CHANGELOG.md` wird als zentrale Quelle für Änderungen genutzt.

**TODO / Open Questions:**

- [ ] Inhalte aus `archive/full_files_stand_02.12.2025` in `CHANGELOG.md` übernehmen.
- [ ] Prüfen, ob weitere alte Dokus ins Archiv verschoben werden sollen.

---

### 3.2. 2025-12-02 – Dokumentations-Konsolidierung (CHANGELOG, RISK_MANAGEMENT)

**Tool:** Claude
**Kontext:** Erstellung und Strukturierung von zentralen Dokumentationsdateien nach der Reorganisation.

**Key Outcomes:**

- `CHANGELOG.md` erstellt mit Phase 2 Changes (Risk & Data Layer Extensions)
- `RISK_MANAGEMENT.md` als umfassendes Risk-Management-Dokument angelegt:
  - Grundprinzipien, Zentrale Kennzahlen & Limits
  - Position Sizing (Fixed Fractional + Kelly Criterion)
  - Portfolio-Level Safeguards
  - Drei Risk-Profile (Conservative/Moderate/Aggressive)
  - Best Practices, FAQ, Roadmap

**Decisions:**

- CHANGELOG.md folgt chronologischem Format mit Phase-Kennzeichnung
- RISK_MANAGEMENT.md als zentrale Risk-Doku (ergänzt RISK_LIMITS_UPDATE.md)
- Alle Risk-Parameter werden in `config/config.toml` unter `[risk]` konfiguriert

**TODO / Open Questions:**

- [ ] Phase 1 Inhalte aus `archive/full_files_stand_02.12.2025` in CHANGELOG.md eintragen
- [ ] Risk-Profile in separaten Config-Dateien anlegen (z.B. `config/risk_conservative.toml`)

**Links / Referenzen:**

- `docs/project_docs/CHANGELOG.md`
- `docs/project_docs/RISK_MANAGEMENT.md`
- `docs/project_docs/RISK_LIMITS_UPDATE.md`
- `config/config.toml`

---

### 3.3. YYYY-MM-DD – [Kurzer Titel der Session]

**Tool:** [Claude / ChatGPT / Gemini / …]
**Kontext:** Kurzbeschreibung, worum es in der Session ging.

**Key Outcomes:**

- Bulletpoint 1
- Bulletpoint 2
- Bulletpoint 3

**Decisions:**

- Entscheidung 1
- Entscheidung 2

**TODO / Open Questions:**

- [ ] Offener Punkt 1
- [ ] Offener Punkt 2

**Links / Referenzen:**

- `docs/project_docs/RISK_MANAGEMENT.md`
- `scripts/demo_risk_limits.py`
- Git-Issue: `PT-123` (falls vorhanden)

---

## 4. Archivierte Sessions (Historie)

> Hier kannst du ältere oder weniger relevante KI-Sessions ablegen, damit Abschnitt 3 schlank bleibt.

### 4.1. Vor 2025-12-02 – Frühe Projektphase

**Kurzbeschreibung:**

- Erste Diskussionen zur Projektidee „Peak_Trade".
- Erste Skizzen zur Backtest-Engine und Daten-Anbindung.
- Grobe Brainstorming-Sessions zu Risk-Modellen (vor der jetzigen Struktur).

**Relevante Punkte (nur das Wichtigste):**

- [ ] Prüfen, ob noch alte, relevante Ideen in frühere Chats ausgelagert sind.
- [ ] Falls ja: komprimiert hier eintragen.

---

## 5. Best Practices für KI-Sessions

- **Vor der Session:**
  - Kurz notieren, was du vom Tool willst (Ziel + Kontext).
- **Während der Session:**
  - Wichtige Entscheidungen sofort unter „Decisions" notieren.
- **Nach der Session:**
  - Relevante Ergebnisse in „echte" Doku übernehmen:
    - Architektur → `IMPLEMENTATION_SUMMARY.md`
    - Risiko-Themen → `RISK_MANAGEMENT.md` / `RISK_LIMITS_UPDATE.md`
    - Änderungen → `CHANGELOG.md`

---

## 6. Geplante Verbesserungen

- [ ] Tagging von Sessions nach Thema (z.B. `#risk`, `#data`, `#infra`).
- [ ] Link-Liste zu besonders wichtigen Chats (z.B. Permalinks aus Claude/ChatGPT).
- [ ] Kurze „Hall of Fame"-Liste mit besonders guten Prompts/Antworten.

---

## 7. Session-Template (zum Kopieren)

```md
### X.X. YYYY-MM-DD – [Titel]

**Tool:** [Claude / ChatGPT / ...]
**Kontext:** [Kurzbeschreibung]

**Key Outcomes:**
- [Ergebnis 1]
- [Ergebnis 2]

**Decisions:**
- [Entscheidung 1]
- [Entscheidung 2]

**TODO / Open Questions:**
- [ ] [Offener Punkt 1]
- [ ] [Offener Punkt 2]

**Links / Referenzen:**
- `[Dateipfad oder URL]`
```
