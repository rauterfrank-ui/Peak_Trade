# Peak_Trade – AI-Helper-Guide (Cursor, Claude, ChatGPT)

> **Zweck:** Einheitlicher Umgang mit AI-Tools im Peak_Trade-Projekt – weniger Chaos, mehr Qualität & Safety.
>
> **Zielgruppe:** Ich (Future-Ich), Entwickler und jeder, der mit AI-Tools an Peak_Trade arbeitet.

---

## 1. Einleitung & Purpose

Dieses Dokument beschreibt, **wie AI-Tools sinnvoll mit Peak_Trade eingesetzt werden sollen**. Es definiert Grundprinzipien, Best Practices und klare Do/Don'ts, um:

- **Konsistenz** zu wahren (einheitlicher Code-Stil, Doku-Struktur, Commit-Messages)
- **Safety-First** zu leben (keine versehentliche Live-Aktivierung, keine Secrets im Code)
- **Qualität** zu sichern (Tests respektieren, Doku mitpflegen, keine quick&dirty Hacks)
- **Effizienz** zu steigern (AI als Co-Pilot, nicht als Autopilot)

Für technische Details zu Projekt-Struktur, Modulen und Commands siehe [`CLAUDE_GUIDE.md`](CLAUDE_GUIDE.md).

---

## 2. Überblick: Welche AI-Tools spielen welche Rolle?

### Cursor + integrierte Modelle (Claude, GPT)

- **Primär für:** Coding, Refactoring, Inline-Hints, Tests schreiben
- **Stärken:** Kontextbewusst durch Projekt-Indexierung, schnelle Iteration, Code-Completion
- **Typische Aufgaben:** Funktion implementieren, Test ergänzen, Modul refactoren, Import-Fehler beheben

### ChatGPT / Claude im Browser

- **Primär für:** High-Level-Design, Phasen-Planung, Meta-Prompts, Doku-Entwürfe
- **Stärken:** Längere Konversationen, komplexe Reasoning-Aufgaben, Architektur-Diskussionen
- **Typische Aufgaben:** Roadmap-Entwurf, Phasen-Planung, Zusammenfassungen, Entscheidungs-Dokumentation

### Wofür eignet sich welches Tool?

| Aufgabe | Empfohlenes Tool |
|---------|------------------|
| Neue Funktion implementieren | Cursor (Claude/GPT) |
| Tests schreiben/erweitern | Cursor |
| Refactoring eines Moduls | Cursor |
| Debugging & Fehlersuche | Cursor |
| Phasen-/Roadmap-Planung | ChatGPT/Claude Browser |
| Doku-Entwürfe & Überarbeitungen | ChatGPT/Claude Browser oder Cursor |
| Architektur-Diskussionen | ChatGPT/Claude Browser |
| Schnelle Code-Completion | Cursor |

---

## 3. Working Agreement mit AI (Grundprinzipien)

### Safety-First

- **Kein Live-Trading aktivieren:** Niemals `mode = "live"` setzen oder Safety-Gates umgehen.
- **Keine Secrets/Keys erzeugen:** Keine API-Keys, Tokens oder Credentials im Code.
- **Gating respektieren:** `live_mode_armed`, `enable_live_trading` etc. niemals auf `true` setzen ohne explizite Freigabe.

### Tests respektieren

- **Keine Tests abschalten:** Niemals `pytest.skip()` oder `@pytest.mark.skip` hinzufügen, um Tests „passend" zu machen.
- **Keine quick&dirty Hacks:** Lieber den Fehler verstehen als ihn zu umgehen.
- **Tests mitpflegen:** Bei Code-Änderungen → Tests anpassen oder ergänzen.

### Doku-First Mindset

- **Wichtige Änderungen dokumentieren:** Code + Tests + Doku gehören zusammen.
- **Phase-Dokus aktuell halten:** Neue Features → entsprechende `PHASE_*.md` ergänzen.
- **Changelogs pflegen:** Signifikante Änderungen in Status-/Release-Docs notieren.

### Kein massives Umbauen ohne Plan

- **Architektur-Änderungen nur mit Begründung:** Keine großflächigen Refactorings ohne klares Ziel.
- **Scope einhalten:** Fokussiert auf die aktuelle Aufgabe bleiben, nicht „nebenbei" optimieren.
- **Kompatibilität wahren:** Bestehende APIs nicht ohne Absprache ändern.

### AI ist Co-Pilot, nicht Autopilot

- **Menschliche Review bleibt Pflicht:** AI-generierten Code immer prüfen.
- **Kritisches Denken:** AI-Vorschläge hinterfragen, besonders bei Sicherheits-/Risk-Themen.
- **Verantwortung liegt beim Menschen:** AI schlägt vor, Mensch entscheidet.

---

## 4. Repo-Orientierung für AI (wichtige Dateien/Ordner)

### Verzeichnis-Übersicht

| Ordner | Inhalt | Typische AI-Aufgaben |
|--------|--------|----------------------|
| `src/` | Produktionscode | Implementierung, Refactoring |
| `src/core/` | Config, Position Sizing, Risk, Experiments | Core-Logik anpassen |
| `src/data/` | Data Loading, Caching, Kraken API | Daten-Pipeline erweitern |
| `src/strategies/` | Trading-Strategien | Neue Strategie hinzufügen |
| `src/backtest/` | Backtest-Engine, Stats | Backtest-Logik anpassen |
| `src/live/` | Risk Limits, Alerts, Safety | Live-Track erweitern |
| `src/experiments/` | Research-Pipeline, Monte-Carlo, Sweeps | Experiment-Logik |
| `src/reporting/` | Reports, Plots, Visualisierungen | Report-Funktionen |
| `tests/` | Unit-/Integration-/Smoke-Tests | Tests schreiben/erweitern |
| `docs/` | Dokumentation (Phase-Dokus, Overviews, Guides) | Doku aktualisieren |
| `docs/ai/` | AI-Guides und Prompts | Meta-Doku für AI-Nutzung |
| `config/` | TOML-Configs, Sweeps, Test-Configs | Konfiguration anpassen |
| `scripts/` | CLI-Skripte (Backtests, Reports, Live-Ops) | CLI-Funktionalität |
| `reports&#47;` | Generierte Reports (Artefakte) | Nicht committen |

### Wo gehören neue Dinge hin?

- **Neue Strategie:** `src/strategies/` + Registry-Eintrag + Config + Tests + Doku
- **Neues Risk-Limit:** `src/live/risk_limits.py` + Tests + Developer-Guide
- **Neues Portfolio-Rezept:** `config/portfolio_recipes.toml` + Tests
- **Neue CLI-Funktion:** `scripts/` + Tests + CLI-Cheatsheet-Update
- **Neue Phase-Doku:** `docs&#47;PHASE_*.md`

---

## 5. Typische Use-Cases für AI in Peak_Trade

### Coding & Refactoring

```
Beispiel-Prompt:
"Implementiere eine neue Strategie 'DualMomentum' basierend auf DEV_GUIDE_ADD_STRATEGY.md.
Die Strategie soll absolute und relative Momentum-Signale kombinieren."
```

- Neue Funktionen/Klassen implementieren
- Bestehenden Code refactoren
- Performance-Optimierungen

### Tests schreiben & erweitern

```
Beispiel-Prompt:
"Schreibe parametrisierte Tests für die neue DualMomentum-Strategie.
Teste Edge-Cases: leere Daten, einzelne Bar, NaN-Werte."
```

- Neue Testdatei erstellen
- Edge-Cases ergänzen
- Parametrisierte Tests (pytest.mark.parametrize)
- Coverage-Lücken schließen

### Doku & Playbooks

```
Beispiel-Prompt:
"Aktualisiere docs/PHASE_XX_NEW_FEATURE.md mit der implementierten Funktionalität.
Füge CLI-Beispiele und Verweise auf verwandte Dokus hinzu."
```

- Phase-Dokus schreiben/updaten
- „How to read…"-Blöcke ergänzen
- Runbook-Schritte dokumentieren
- Changelogs pflegen

### Debugging & Fehlersuche

```
Beispiel-Prompt:
"Test test_backtest_portfolio.py::test_multi_strategy schlägt fehl mit ImportError.
Analysiere den Fehler und schlage eine Lösung vor."
```

- Testfehler analysieren
- Import-/Pfad-Probleme auflösen
- Stack-Traces interpretieren
- Root-Cause-Analyse

### Meta-Arbeit

```
Beispiel-Prompt:
"Erstelle einen Phasen-Plan für die Integration von Binance als zweiten Exchange.
Berücksichtige DEV_GUIDE_ADD_EXCHANGE.md und Safety-Anforderungen."
```

- Phasen-Planung
- Roadmap-Entwürfe
- Zusammenfassungen erstellen
- Entscheidungs-Historie dokumentieren

---

## 6. Do & Don'ts

### Do

- **Kleine, klar abgegrenzte Aufgaben definieren:** „Implementiere diese Funktion + Tests" statt „Mach das Modul besser"
- **Relevante Dateien benennen:** „Ändere `src/strategies/rsi.py`, schreibe Tests in `tests&#47;test_rsi.py`"
- **Kontext mitgeben:** „Nutze DEV_GUIDE_ADD_STRATEGY.md als Referenz"
- **Explizite Constraints setzen:** „Keine Breaking Changes an der API", „Tests müssen grün bleiben"
- **Nach Erklärungen fragen:** „Erkläre mir, warum du diesen Ansatz gewählt hast"
- **Iterativ arbeiten:** Kleine Schritte, Review, nächster Schritt
- **Tests zuerst prüfen lassen:** „Führe erst `python3 -m pytest tests&#47;test_X.py -v` aus, dann implementiere"

### Don't

- **Keine vagen Aufgaben:** „Verbessere den Code" → zu unspezifisch
- **Keine Safety-Bypasses:** Niemals „Deaktiviere die Safety-Checks" oder „Setze mode=live"
- **Keine Test-Unterdrückung:** Niemals „Mach den Test grün, egal wie"
- **Keine Secrets committen:** Niemals API-Keys, Tokens, Credentials im Code
- **Keine massiven Änderungen ohne Plan:** Kein „Refactore alles auf einmal"
- **Keine ungeprüfte AI-Ausgabe committen:** Immer Review vor Commit
- **Keine Änderungen an fremden Commits:** Keine `--amend` auf Commits anderer Entwickler

---

## 7. Prompt-Templates für häufige Aufgaben

### Neue Strategie implementieren

```markdown
Implementiere eine neue Strategie '{STRATEGY_NAME}' für Peak_Trade.

Kontext:
- Nutze docs/DEV_GUIDE_ADD_STRATEGY.md als Referenz
- Erstelle src/strategies/{strategy_name}.py
- Registriere in src/strategies/registry.py
- Füge Config-Section in config/config.toml hinzu
- Schreibe Tests in tests/test_{strategy_name}.py

Anforderungen:
- {BESCHREIBUNG DER STRATEGIE}
- Erbe von BaseStrategy
- Implementiere generate_signals() und from_config()
- Mindestens 5 Tests inkl. Edge-Cases
```

### Tests erweitern

```markdown
Erweitere die Tests für {MODUL/KLASSE}.

Kontext:
- Bestehende Tests: tests/test_{module}.py
- Modul: src/{path}/{module}.py

Anforderungen:
- Füge parametrisierte Tests für {SZENARIEN} hinzu
- Teste Edge-Cases: {EDGE_CASES}
- Coverage-Ziel: {PROZENT}%
- Tests müssen mit bestehendem Fixture-Setup kompatibel sein
```

### Doku aktualisieren

```markdown
Aktualisiere die Dokumentation für Phase {XX}.

Kontext:
- Datei: docs/PHASE_{XX}_{NAME}.md
- Implementierte Features: {LISTE}

Anforderungen:
- Aktualisiere Status-Block
- Ergänze CLI-Beispiele
- Füge Verweise auf verwandte Dokus hinzu
- Schreibe in Deutsch, tech-englische Begriffe sind ok
```

### Debugging

```markdown
Analysiere folgenden Fehler in Peak_Trade:

Fehler:
{FEHLERMELDUNG / STACK-TRACE}

Kontext:
- Betroffene Datei(en): {DATEIEN}
- Aufruf: {WIE WURDE DER FEHLER REPRODUZIERT}

Anforderungen:
- Analysiere die Root-Cause
- Schlage eine Lösung vor
- Erkläre, warum die Lösung das Problem behebt
- Prüfe, ob Tests betroffen sind
```

---

## 8. Integration mit v1.0-Workflow

### Verwandte Dokumente

| Dokument | Zweck |
|----------|-------|
| [`CLAUDE_GUIDE.md`](CLAUDE_GUIDE.md) | Technische Referenz (Module, Commands, Struktur) |
| [`../PEAK_TRADE_V1_OVERVIEW_FULL.md`](../PEAK_TRADE_V1_OVERVIEW_FULL.md) | v1.0 Gesamtübersicht |
| [`../PEAK_TRADE_STATUS_OVERVIEW.md`](../PEAK_TRADE_STATUS_OVERVIEW.md) | Projekt-Status mit Prozentangaben |
| [`../PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](../PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) | Research → Live Workflow |
| [`../CLI_CHEATSHEET.md`](../CLI_CHEATSHEET.md) | CLI-Referenz |

### Wie AI-Tools in den Workflow eingebettet sind

1. **Planung:** ChatGPT/Claude Browser für Phasen-Entwürfe und Architektur-Diskussionen
2. **Implementierung:** Cursor für Code, Tests, Refactoring
3. **Review:** Menschliche Prüfung aller AI-generierten Änderungen
4. **Doku:** AI-unterstützte Aktualisierung von Phase-Dokus und Status
5. **Commit:** Mensch entscheidet, was committet wird

---

## 9. Checkliste vor dem Commit (AI-generierter Code)

- [ ] Code gelesen und verstanden?
- [ ] Tests laufen grün (`python3 -m pytest tests&#47; -v`)?
- [ ] Keine Secrets/Keys im Code?
- [ ] Keine Safety-Bypasses?
- [ ] Keine Breaking Changes ohne Absprache?
- [ ] Doku aktualisiert (falls nötig)?
- [ ] Commit-Message aussagekräftig?

---

## 10. Änderungshistorie

| Datum | Änderung |
|-------|----------|
| 2025-12-08 | Erstversion – AI-Helper-Guide |

---

**AI ist ein mächtiges Werkzeug – mit klaren Regeln wird es zum effektiven Co-Piloten.**
