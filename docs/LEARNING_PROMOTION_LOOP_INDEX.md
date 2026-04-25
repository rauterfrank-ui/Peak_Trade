# Learning & Promotion Loop - Dokumentations-Index

**Version:** v1  
**Status:** ✅ Production-Ready  
**Datum:** 2025-12-11

## Authority and epoch note

This document is a learning/promotion-loop architecture and governance navigation surface, not a standalone promotion authority. `Production-Ready`, `Production-Readiness`, promotion, readiness, registry, or Live-session wording in this document does not, by itself, grant Master V2 approval, Doubleplay authority, PRE_LIFE completion, First-Live readiness, operator authorization, production readiness, experiment authorization, training authorization, or permission to route orders into any live capital path.

Interpret this document together with current gate/evidence/signoff artifacts, Scope / Capital Envelope boundaries, Risk / Exposure Caps, Safety / Kill-Switches, staged Execution Enablement, manual-only controls, and the explicit blacklist / P0 / P1 governance in this document. This docs-only note changes no runtime behavior, learning/promotion logic, registry behavior, experiment/training behavior, MLflow behavior, or status/history/checklist content.

---

## 🎯 Schnellstart

**Neu hier?** Starte mit:

1. **[QUICKSTART_LIVE_OVERRIDES.md](./QUICKSTART_LIVE_OVERRIDES.md)** - In 3 Schritten loslegen
2. **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Gesamtarchitektur verstehen

**Für Operator:**

1. **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** → Abschnitt 5: Operator-Flow

---

## 📚 Dokumentations-Struktur

### 🏛️ Architektur & Konzepte

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** | 🌟 **Master-Dokumentation** - Gesamtarchitektur System 1 + System 2 | Alle |
| **[PROMOTION_LOOP_V0.md](./PROMOTION_LOOP_V0.md)** | Detaillierte Promotion Loop Architektur & Design | Developer |
| **[PROMOTION_LOOP_SAFETY_FEATURES.md](./PROMOTION_LOOP_SAFETY_FEATURES.md)** | 🛡️ **P0/P1 Safety Features** - Blacklist, Bounds, Audit-Log | Developer, Operator |
| **[LIVE_OVERRIDES_CONFIG_INTEGRATION.md](./LIVE_OVERRIDES_CONFIG_INTEGRATION.md)** | Config-Integration & Technische Details | Developer |

### 🚀 Praktische Guides

| Dokument | Beschreibung | Zielgruppe |
|----------|--------------|------------|
| **[QUICKSTART_LIVE_OVERRIDES.md](./QUICKSTART_LIVE_OVERRIDES.md)** | 3-Schritte Quickstart mit Beispielen | Operator, Developer |
| **[IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md](./IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md)** | Implementation Summary & Abnahme-Checkliste | Developer, Reviewer |

---

## 🔍 Nach Thema

### Environment Setup

```bash
# Verzeichnisstruktur erstellen
mkdir -p config/live_overrides
mkdir -p reports/live_promotion
mkdir -p reports/learning_snippets
```

→ **[LIVE_OVERRIDES_CONFIG_INTEGRATION.md](./LIVE_OVERRIDES_CONFIG_INTEGRATION.md)** - Sektion "Config Structure"

### Config-Loading

```python
from src.core.peak_config import load_config_with_live_overrides
cfg = load_config_with_live_overrides()
```

→ **[QUICKSTART_LIVE_OVERRIDES.md](./QUICKSTART_LIVE_OVERRIDES.md)** - Sektion "Nutzung"

### Promotion Loop

```bash
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto
```

→ **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Sektion 3: "System 2"

### Learning Loop ✅

```bash
python3 scripts/run_learning_apply_cycle.py --dry-run
```

→ **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Sektion 2: "System 1"

### Monitoring & Debugging

```bash
# Historical: python3 scripts/demo_live_overrides.py
```

→ **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Sektion 7: "Monitoring & Observability"

---

## 🎓 Lernpfad

### 1. Grundlagen (30 Minuten)

1. Lies **[QUICKSTART_LIVE_OVERRIDES.md](./QUICKSTART_LIVE_OVERRIDES.md)**
   - Verstehe die 3 Schritte
   - Führe das Demo-Script aus

2. Lies **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Abschnitt 1-4
   - Architektur-Überblick
   - System 1 & System 2
   - Config-Integration

### 2. Vertiefung (1-2 Stunden)

1. Lies **[PROMOTION_LOOP_V0.md](./PROMOTION_LOOP_V0.md)**
   - Models & Policy
   - Engine-Funktionen
   - Auto-Apply Details

2. Lies **[LIVE_OVERRIDES_CONFIG_INTEGRATION.md](./LIVE_OVERRIDES_CONFIG_INTEGRATION.md)**
   - Config-Layer Details
   - Environment-Gating
   - Troubleshooting

3. Führe Tests aus:
   ```bash
   python3 -m pytest tests/test_live_overrides*.py -v
   ```

### 3. Production-Readiness (1 Tag)

1. Lies **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Abschnitt 5-9
   - Operator-Flow
   - Sicherheits-Features
   - Best Practices

2. Lies **[IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md](./IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md)**
   - Implementation Details
   - Test-Coverage
   - Abnahme-Checkliste

3. Praktische Übungen:
   - Promotion Loop im `manual_only` Modus
   - Config-Loading testen
   - Proposal-Review durchführen

---

## 🛠️ Code-Referenzen

### Packages

```
src/
├── core/
│   ├── peak_config.py              # load_config_with_live_overrides()
│   └── environment.py              # TradingEnvironment, EnvironmentConfig
├── governance/
│   └── promotion_loop/
│       ├── models.py               # PromotionCandidate, Decision, Proposal
│       ├── policy.py               # AutoApplyPolicy, AutoApplyBounds
│       └── engine.py               # Core Functions
└── meta/
    └── learning_loop/
        └── models.py               # ConfigPatch, PatchStatus
```

### Scripts

```
scripts/
├── run_promotion_proposal_cycle.py   # Promotion Loop ✅
├── run_learning_apply_cycle.py       # Learning Loop ✅
└── demo_live_overrides.py            # Demo & Testing ✅
```

### Tests

```
tests/
├── test_live_overrides_integration.py          # 13 Tests ✅
└── test_live_overrides_realistic_scenario.py   # 6 Tests ✅
```

→ Alle Tests: `pytest tests&#47;test_live_overrides*.py -v`

---

## 📋 Checklisten

### Operator-Checkliste: Promotion Cycle durchführen

- [ ] Learning Loop gelaufen
- [ ] Promotion Loop gestartet: `run_promotion_proposal_cycle.py`
- [ ] Proposals in `reports&#47;live_promotion&#47;` geprüft
- [ ] `OPERATOR_CHECKLIST.md` durchgearbeitet
- [ ] Sicherheits-Checks bestanden
- [ ] Config-Diff geprüft (`demo_live_overrides.py`)
- [ ] Live-Session mit Monitoring gestartet
- [ ] Rollback-Plan bereit

→ **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Sektion 5

### Developer-Checkliste: Code-Integration

- [ ] `load_config_with_live_overrides()` statt `load_config()`
- [ ] Environment-Mode korrekt gesetzt
- [ ] Tests für neue Änderungen geschrieben
- [ ] Dokumentation aktualisiert
- [ ] Linter-Errors behoben
- [ ] PR-Review durchgeführt

→ **[LIVE_OVERRIDES_CONFIG_INTEGRATION.md](./LIVE_OVERRIDES_CONFIG_INTEGRATION.md)** - Sektion "Migration"

### Reviewer-Checkliste: Code-Review

- [ ] Keine Live-Trading-Code-Änderungen
- [ ] Nur Config-Merging
- [ ] Environment-Gating korrekt
- [ ] Graceful degradation implementiert
- [ ] Tests vollständig
- [ ] Dokumentation aktualisiert

→ **[IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md](./IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md)** - Sektion "Abnahme-Checkliste"

---

## 🆘 Troubleshooting

| Problem | Lösung | Dokument |
|---------|--------|----------|
| Overrides werden nicht angewendet | Environment prüfen, richtige Funktion nutzen | [QUICKSTART](./QUICKSTART_LIVE_OVERRIDES.md) |
| auto.toml Invalid | TOML-Syntax prüfen, Keys in Anführungszeichen | [QUICKSTART](./QUICKSTART_LIVE_OVERRIDES.md) |
| Promotion Loop lehnt alles ab | `eligible_for_live` prüfen | [ARCHITECTURE](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md) |
| Bounds zu eng | Policy anpassen (mit Vorsicht!) | [ARCHITECTURE](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md) |
| Tests schlagen fehl | Pytest verbose laufen lassen | [IMPLEMENTATION](./IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md) |

→ Vollständiges Troubleshooting: **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Sektion 8

---

## 📊 Status-Übersicht

### ✅ Implementiert & Getestet

| Komponente | Status | Tests | Dokumentation |
|-----------|--------|-------|---------------|
| Promotion Loop | ✅ | ✅ 19/19 | ✅ Vollständig |
| Config-Integration | ✅ | ✅ 19/19 | ✅ Vollständig |
| Auto-Apply (bounded_auto) | ✅ | ✅ 19/19 | ✅ Vollständig |
| Environment-Gating | ✅ | ✅ 19/19 | ✅ Vollständig |
| Graceful Degradation | ✅ | ✅ 19/19 | ✅ Vollständig |
| **P0 Safety Features** | ✅ | ✅ 33/33 | ✅ Vollständig |
| **P1 Governance Features** | ✅ | ✅ 33/33 | ✅ Vollständig |

### ⏳ TODO

| Komponente | Status | Priorität |
|-----------|--------|-----------|
| Learning Loop Bridge | ⏳ TODO | High |
| Learning Loop Emitter | ⏳ TODO | High |
| Automation-Integration | ⏳ TODO | Medium |
| Slack-Notifications | ⏳ TODO | Low |
| Web-UI für Proposals | ⏳ TODO | Low |

→ Vollständige Roadmap: **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Sektion 12

---

## 🔄 Stabilisierungsphase – Überblick (Cycles 1–10)

**Status:**

* **Aktueller Modus:** `manual_only` ✅
* **Stabilisierungsphase:** 2 / 10 erfolgreiche Cycles
* **Nächster Meilenstein:** Cycle #5 (50 % der geplanten Stabilisierung)

---

### Learnings aus den ersten 2 Cycles

**Positive Beobachtungen**

* ✅ **Stabilität:**
  System läuft zuverlässig ohne Fehler über mehrere Durchläufe.

* ✅ **Konsistenz:**
  Bei identischen Input-Daten erzeugt das System konsistente, reproduzierbare Empfehlungen.

* ✅ **Safety / Governance:**

  * Keine unerwarteten Änderungen
  * Kein Bypass der Governance-Filter
  * Environment-Gating aktiv (keine ungewollten Live-Effekte)

* ✅ **Usability:**
  Reports sind verständlich, gut lesbar und unterstützen die manuelle Go/No-Go-Entscheidung des Operators.

---

**Verbesserungspotenzial**

* 📝 **Datenvielfalt:**
  Aktuell basieren die Vorschläge vor allem auf Demo-Patches.
  → Nächster Schritt: echte Learning-Loop-Integration und Anbindung an reale Experimente / Backtests.

* 📝 **Varianz in Szenarien:**
  Bisher sind die Tests relativ homogen.
  → Mehr unterschiedliche Test-Szenarien (verschiedene Strategien, Marktphasen, Config-Varianten) zur feineren Kalibrierung.

* 📝 **Teil-Automation (später):**
  Einige Operator-Entscheidungen könnten zukünftig regelbasiert/vorqualifiziert werden,
  z.B. Auto-Approval für sehr kleine, klar begrenzte Patches mit guter Historik.

---

### Operatives Vorgehen (kurzfristig)

**Empfehlung für die nächsten Tage:**

* Führe **2–3 weitere Cycles** (Cycle #3–5) im `manual_only` Modus durch:

  * mit leicht variierenden Demo-/Test-Patches,
  * mit **explizit dokumentierten** Go/No-Go-Entscheidungen pro Cycle,
  * mit einem kurzen **wöchentlichen Mini-Review**.

**Standard-Command für den nächsten Cycle:**

```bash
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only
```

**Ziel der Stabilisierungsphase:**

* Insgesamt **10 erfolgreiche manual_only-Cycles**,
* ausreichend Datenbasis für:

  * Bewertung der Recommendation-Qualität,
  * Schärfung der Governance-Bounds,
  * spätere bounded_auto-Evaluation.

→ Detailliertes Log: **[OPERATOR_DECISION_LOG.md](./learning_promotion/OPERATOR_DECISION_LOG.md)**

---

## 🚀 bounded_auto – Readiness Check (Vorbereitung)

> Diese Checkliste ist für den Zeitpunkt gedacht, wenn die Stabilisierungsphase (≈ 10 manual_only-Cycles) abgeschlossen ist.

### 1. Stabilität & Historik

* [ ] Mindestens 10 erfolgreiche Cycles im `manual_only` Modus abgeschlossen
* [ ] Keine kritischen Fehler / Crashes während der Runs
* [ ] Reports und Logs sind vollständig und rückverfolgbar

### 2. Qualität der Empfehlungen

* [ ] Mehrere Go-Entscheidungen haben sich im Nachhinein als sinnvoll erwiesen
* [ ] No-Go-Entscheidungen waren begründet und nicht Folge von System-Fehlern
* [ ] Es existiert ein grobes „Profil": Welche Patch-Typen sind unkritisch, welche heikel?

### 3. Governance-Bounds definiert

* [ ] Maximale Anzahl automatischer Promotions pro Zeitraum definiert, z.B.:
  - `max_promotions_per_day = 1`
  - `max_promotions_per_week = 3`
* [ ] Erlaubte Targets klar spezifiziert, z.B. nur:
  - Backtest-/Experiment-Configs
  - Research-Tier-Strategien (kein direkter Live-Impact)
* [ ] Klare Blacklist vorhanden (was darf NIEMALS auto-promoted werden?)

### 4. Config & Schalter

* [ ] Config-Block für `bounded_auto` vorbereitet (aber noch nicht aktiv), z.B.:

```toml
# [promotion_loop]
# mode = "bounded_auto"              # NEIN: Erst aktivieren, wenn Checkliste erfüllt
# max_auto_applies_per_day = 1
# auto_apply_whitelist = ["portfolio.leverage", "strategy.trigger_delay"]
# auto_apply_blacklist = ["live_trading", "live.api_keys", "risk.stop_loss"]
```

* [ ] Rollback-Strategie definiert:

  * Wie wird bei Bedarf sofort zurück auf `manual_only` geschaltet?
  * Wie werden falsch promotete Patches rückgängig gemacht?

### 5. Monitoring & Alerts

* [ ] Ort der bounded_auto-Logs definiert (z.B. `logs&#47;learning_promotion&#47;bounded_auto&#47;`)
* [ ] Reports enthalten klar ersichtliche Markierung:
  „Dieses Patch wurde **automatisch** promotet (bounded_auto)"
* [ ] Optional: Notification-Channel (Slack / Mail / Dashboard-Widget) für auto-Promotions

---

**Freigabe-Kriterium:**

* bounded_auto darf erst aktiviert werden, wenn **alle oben relevanten Checkboxen** bewusst abgehakt wurden
  und der Operator die Freigabe explizit erteilt.

→ Siehe auch:
- **Config (Repo):** `config/promotion_loop_config.toml` – Sektion "UMSCHALTEN AUF bounded_auto"
- **[PROMOTION_LOOP_SAFETY_FEATURES.md](./PROMOTION_LOOP_SAFETY_FEATURES.md)** - P0/P1 Safety Details

---

## 🛡️ Sicherheits-Features (P0/P1) ⭐ **NEU**

**Status:** ✅ Implementiert (2025-12-11)

### P0: Critical Safety Features

- **Blacklist:** Verhindert Auto-Promotion kritischer Targets (live.api_keys, risk.stop_loss, etc.)
- **Bounds:** Harte Grenzen für min/max Werte und max_step
- **Guardrails:** bounded_auto-spezifische Sicherheitschecks

### P1: Governance Features

- **Audit-Logging:** Vollständige Nachverfolgbarkeit aller Entscheidungen (JSONL)
- **Global Lock:** Notfall-Killswitch für bounded_auto

→ Details: **[PROMOTION_LOOP_SAFETY_FEATURES.md](./PROMOTION_LOOP_SAFETY_FEATURES.md)**

---

## 🎯 Nächste Schritte

### Für Operator

1. **Quickstart durcharbeiten:** [QUICKSTART_LIVE_OVERRIDES.md](./QUICKSTART_LIVE_OVERRIDES.md)
2. **Demo-Script testen:** `python scripts&#47;demo_live_overrides.py` (historical)
3. **Promotion Loop ausprobieren:** `python3 scripts&#47;run_promotion_proposal_cycle.py --auto-apply-mode manual_only`

### Für Developer

1. **Architektur verstehen:** [LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)
2. **Code-Integration:** [LIVE_OVERRIDES_CONFIG_INTEGRATION.md](./LIVE_OVERRIDES_CONFIG_INTEGRATION.md)
3. **Tests erweitern:** `tests&#47;test_live_overrides*.py`

### Für Reviewer

1. **Implementation Summary:** [IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md](./IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md)
2. **Abnahme-Checkliste durchgehen**
3. **Tests reviewen:** `pytest tests&#47;test_live_overrides*.py -v`

---

## 📞 Support & Feedback

**Fragen? Probleme? Verbesserungsvorschläge?**

1. Prüfe **[Troubleshooting-Sektion](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md#8-troubleshooting)**
2. Führe **Demo-Script** aus: `python scripts&#47;demo_live_overrides.py` (historical)
3. Schaue in die **Tests** für Code-Beispiele

---

## 📝 Versions-Historie

### v1 (2025-12-11)

✅ Promotion Loop vollständig implementiert  
✅ Config-Integration fertig  
✅ Auto-Apply (bounded_auto) funktioniert  
✅ Tests vollständig (19/19 grün)  
✅ Dokumentation umfassend  

**Status:** Production-Ready 🚀

---

**Letzte Aktualisierung:** 2025-12-11  
**Version:** v1  
**Maintainer:** Peak_Trade Development Team
