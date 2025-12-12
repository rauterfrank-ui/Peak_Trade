# InfoStream v0 – Templates

> **Version:** v0
> **Letzte Aktualisierung:** 2025-12-11

Kopiervorlagen für alle InfoStream-Formate.

---

## 1. INFO_PACKET Template

```text
=== INFO_PACKET ===
source: [test_health_automation | offline_realtime_pipeline | offline_synth_session | trigger_training_sessions | macro_georisk_specialist | operator_notes]
event_id: INF-YYYYMMDD-HHMMSS-kurzer_name
category: [test_automation | operator_training | market_analysis | system_health | incident | performance]
severity: [info | warning | error | critical]
created_at: YYYY-MM-DDTHH:MM:SS+01:00

summary:
  [Zusammenfassung in 1-3 Sätzen. Was ist passiert? Was ist das Ergebnis?]

details:
  - [Detail 1]
  - [Detail 2]
  - [Detail 3]

links:
  - [reports/pfad/zu/report.md]
  - [reports/pfad/zu/report.html]

tags:
  - [tag1]
  - [tag2]
  - [tag3]

status: new
=== /INFO_PACKET ===
```

---

## 2. EVAL_PACKAGE Template

```text
=== EVAL_PACKAGE ===
event_id: [event_id aus INFO_PACKET]

short_eval:
  [2-3 Sätze Bewertung. Ist es gut/schlecht? Handlungsbedarf?]

key_findings:
  - [Erkenntnis 1]
  - [Erkenntnis 2]
  - [Erkenntnis 3]

recommendations:
  - [Empfehlung 1]
  - [Empfehlung 2]

risk_assessment:
  level: [low | medium | high | critical]
  notes: [Begründung]

tags_out:
  - learning.[thema]
  - pattern.[name]
  - candidate.[action]
=== /EVAL_PACKAGE ===
```

---

## 3. LEARNING_SNIPPET Template

```text
=== LEARNING_SNIPPET ===
- [Learning 1: Was haben wir gelernt?]
- [Learning 2: Was sollten wir in Zukunft anders machen?]
- [Learning 3: Was ist das Muster dahinter?]
=== /LEARNING_SNIPPET ===
```

---

## 4. CROSS_EVAL_SUMMARY Template

(Für die Analyse mehrerer INFO_PACKETs)

```text
=== CROSS_EVAL_SUMMARY ===
packets_analyzed: [Anzahl]
time_range: [YYYY-MM-DD bis YYYY-MM-DD]

overall_assessment:
  [2-3 Sätze übergreifende Bewertung]

patterns_detected:
  - [Muster 1]
  - [Muster 2]

priority_actions:
  - P1: [Wichtigste Aktion]
  - P2: [Zweitwichtigste Aktion]

combined_learnings:
  - [Übergreifendes Learning 1]
  - [Übergreifendes Learning 2]
=== /CROSS_EVAL_SUMMARY ===
```

---

## 5. Quellen-spezifische Templates

### 5.1 TestHealth-Automation

```text
=== INFO_PACKET ===
source: test_health_automation
event_id: INF-YYYYMMDD-HHMMSS-health_PROFILE
category: test_automation
severity: [info | warning | error]
created_at: YYYY-MM-DDTHH:MM:SS+01:00

summary:
  Health-Score [X]/[Y], [N] Checks bestanden, [M] fehlgeschlagen.
  [Zusatzinfo zu Exit-Code oder besonderen Vorkommnissen]

details:
  - Profile: [daily_quick | weekly_full | ...]
  - Health-Score: [X]/[Y]
  - Passed Checks: [N]
  - Failed Checks: [M]
  - Trigger Violations: [Anzahl] ([expected/unexpected])
  - Duration: [Sekunden]s

links:
  - reports/test_health/YYYYMMDD_HHMMSS_PROFILE/summary.md
  - reports/test_health/YYYYMMDD_HHMMSS_PROFILE/summary.html

tags:
  - test_health
  - nightly
  - [profile_name]
  - monitoring

status: new
=== /INFO_PACKET ===
```

### 5.2 Offline-Realtime-Pipeline

```text
=== INFO_PACKET ===
source: offline_realtime_pipeline
event_id: INF-YYYYMMDD-HHMMSS-offline_STRATEGY
category: system_health
severity: [info | warning | error]
created_at: YYYY-MM-DDTHH:MM:SS+01:00

summary:
  Offline-Realtime-Run für [STRATEGY] abgeschlossen.
  [Ergebnis-Zusammenfassung: Trades, PnL, Auffälligkeiten]

details:
  - Strategy: [Strategy-Name]
  - Symbol: [BTCUSDT | ...]
  - Timeframe: [1h | 4h | ...]
  - Duration: [X] Bars
  - Trades: [N]
  - Win-Rate: [X]%
  - PnL: [+/-X]%
  - Max Drawdown: [X]%

links:
  - reports/offline_realtime_pipeline/YYYYMMDD_strategy_report.html

tags:
  - offline_realtime
  - [strategy_name]
  - backtest
  - performance

status: new
=== /INFO_PACKET ===
```

### 5.3 Trigger-Training-Session

```text
=== INFO_PACKET ===
source: trigger_training_sessions
event_id: INF-YYYYMMDD-HHMMSS-trigger_SESSION
category: operator_training
severity: [info | warning]
created_at: YYYY-MM-DDTHH:MM:SS+01:00

summary:
  Trigger-Training-Session abgeschlossen.
  [N] Trigger erkannt, [M] Entscheidungen getroffen.

details:
  - Session-ID: [UUID]
  - Duration: [X] Minuten
  - Triggers Detected: [N]
  - Decisions Made: [M]
  - Correct Decisions: [K]
  - Psychology Score: [X]/[Y]
  - Dominant Bias: [Bias-Name oder "none"]

links:
  - reports/trigger_training/session_UUID.html
  - reports/trigger_training/meta/psychology_heatmap.html

tags:
  - trigger_training
  - psychology
  - operator_training
  - [bias_name]

status: new
=== /INFO_PACKET ===
```

### 5.4 Makro/GeoRisk-Analyse

```text
=== INFO_PACKET ===
source: macro_georisk_specialist
event_id: INF-YYYYMMDD-HHMMSS-macro_TOPIC
category: market_analysis
severity: [info | warning | error | critical]
created_at: YYYY-MM-DDTHH:MM:SS+01:00

summary:
  [Makro-Event oder GeoRisk-Situation beschreiben]
  [Erwartete Auswirkungen auf Crypto-Märkte]

details:
  - Event: [Beschreibung des Events]
  - Region: [US | EU | Asia | Global]
  - Asset-Impact: [BTC | ETH | Altcoins | All]
  - Time-Horizon: [immediate | short-term | medium-term]
  - Confidence: [low | medium | high]
  - Key Indicators: [Indicator 1], [Indicator 2]

links:
  - [Optional: Externe Quellen oder interne Analysen]

tags:
  - macro
  - georisk
  - [region]
  - [asset_class]
  - market_analysis

status: new
=== /INFO_PACKET ===
```

### 5.5 Operator-Notes

```text
=== INFO_PACKET ===
source: operator_notes
event_id: INF-YYYYMMDD-HHMMSS-note_TOPIC
category: [incident | system_health | performance | operator_training]
severity: [info | warning | error]
created_at: YYYY-MM-DDTHH:MM:SS+01:00

summary:
  [Kurze Beschreibung der Beobachtung oder des Incidents]

details:
  - Context: [Wann/Wo wurde das beobachtet?]
  - Observation: [Was wurde beobachtet?]
  - Impact: [Welche Auswirkung hatte/hat es?]
  - Action Taken: [Was wurde bereits unternommen?]

links:
  - [Optional: Relevante Logs, Reports, Screenshots]

tags:
  - operator_notes
  - [thema]
  - [system_component]

status: new
=== /INFO_PACKET ===
```

---

## 6. Event-ID Konvention

Format: `INF-YYYYMMDD-HHMMSS-kurzer_name`

Beispiele:
- `INF-20251211-143920-daily_quick`
- `INF-20251211-160000-macro_fed_rates`
- `INF-20251211-090000-trigger_morning_session`
- `INF-20251211-120000-note_api_latency`

Regeln:
- Timestamp in lokaler Timezone
- `kurzer_name` max. 30 Zeichen
- Keine Leerzeichen, nur Unterstriche
- Kleinbuchstaben bevorzugt

---

## 7. Tag-Referenz

### Quellen-Tags
| Tag | Bedeutung |
|-----|-----------|
| `test_health` | TestHealth-Automation |
| `trigger_training` | Trigger-Training-System |
| `offline_realtime` | Offline-Realtime-Pipeline |
| `offline_synth` | Offline-Synth-Sessions |
| `macro` | Makro-Analysen |
| `georisk` | Geopolitische Risiken |
| `operator_notes` | Manuelle Operator-Notizen |

### Themen-Tags
| Tag | Bedeutung |
|-----|-----------|
| `monitoring` | Monitoring & Observability |
| `automation` | CI/CD & Automation |
| `strategy` | Strategie-bezogen |
| `risk` | Risk-Management |
| `psychology` | Operator-Psychologie |
| `performance` | System- oder Trading-Performance |
| `incident` | Incident/Problem |

### Output-Tags (für EVAL_PACKAGE)
| Präfix | Bedeutung | Beispiel |
|--------|-----------|----------|
| `learning.*` | Erkenntnis | `learning.test_health` |
| `pattern.*` | Erkanntes Muster | `pattern.expected_failure` |
| `candidate.*` | Verbesserungskandidat | `candidate.doc_update` |
| `action.*` | Erforderliche Aktion | `action.config_change` |

---

## Siehe auch

- [README.md](README.md) – InfoStream-Übersicht
- [PROMPTS.md](PROMPTS.md) – KI-Prompts
