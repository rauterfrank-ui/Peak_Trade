# InfoStream v0 – Intel-Pipeline für Peak_Trade

> **Version:** v0 (Text-Konvention)
> **Status:** Aktiv
> **Erstellt:** 2025-12-11

## Übersicht

Der **InfoStream** ist ein leichtgewichtiger Meta-Layer über Peak_Trade, der:

1. **Generierte Auswertungen sammelt** aus verschiedenen Quellen (TestHealth, OfflineRealtime, TriggerTraining, Makro/GeoRisk, Operator-Notes)
2. **Sie in ein einheitliches Intel-Paket umwandelt** (INFO_PACKET Format)
3. **An einen KI-Auswertungsspezialisten weitergibt** zur Analyse
4. **Verdichtete Erkenntnisse extrahiert** (EVAL_PACKAGE + LEARNING_SNIPPET)

```
┌──────────────────────────────────────────────────────────────────┐
│                        InfoStream v0                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────┐   │
│  │  Quellen    │───▶│ INFO_PACKET  │───▶│ Datenauswertungs- │   │
│  │  (Sources)  │    │  (Collector) │    │   spezialist (KI) │   │
│  └─────────────┘    └──────────────┘    └─────────┬─────────┘   │
│                                                    │              │
│                                                    ▼              │
│                                         ┌───────────────────┐    │
│                                         │ EVAL_PACKAGE +    │    │
│                                         │ LEARNING_SNIPPET  │    │
│                                         └─────────┬─────────┘    │
│                                                    │              │
│                                                    ▼              │
│                                         ┌───────────────────┐    │
│                                         │ Mindmap / Doku /  │    │
│                                         │ Operator-Training │    │
│                                         └───────────────────┘    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quellen (InfoSources)

Typische Quellen für den InfoStream:

| Quelle | Beschreibung | Typische Outputs |
|--------|--------------|------------------|
| `test_health_automation` | GitHub Actions Nightly Health-Checks | Reports, Health-Scores |
| `offline_realtime_pipeline` | OfflineRealtimeFeed-Runs | HTML-Reports, Logs |
| `offline_synth_session` | Synthetische Trading-Sessions | Session-Reports |
| `trigger_training_sessions` | Trigger-Training Drills | Training-Logs, Psychology-Heatmaps |
| `macro_georisk_specialist` | Makro-/Weltpolitik-Analysen | Markt-Einschätzungen |
| `operator_notes` | Manuelle Operator-Notizen | Incident-Notes, Learnings |

---

## Ordnerstruktur

```
Peak_Trade/
├── docs/
│   ├── infostream/
│   │   ├── README.md              # Diese Datei
│   │   ├── PROMPTS.md             # KI-Prompts für Collector & Evaluator
│   │   └── TEMPLATES.md           # Format-Templates
│   └── mindmap/
│       └── INFOSTREAM_LEARNING_LOG.md  # Gesammelte Learnings
│
├── reports/
│   └── infostream/
│       ├── events/                # Gespeicherte INFO_PACKETs
│       │   └── INF-YYYYMMDD-HHMMSS-source.txt
│       └── learning/              # Archivierte LEARNING_SNIPPETs
│           └── LEARN-YYYYMMDD-HHMMSS-topic.md
│
└── scripts/
    └── create_info_packet.py      # Hilfs-Script für Paket-Erstellung
```

---

## Workflow (v0)

### Schritt 1: Quelle erzeugt Output

```bash
# Beispiel: GitHub Action läuft durch
# Output: reports/test_health/20251211_143920_daily_quick/
```

### Schritt 2: INFO_PACKET erstellen

Manuell oder mit Hilfs-Script:

```bash
# Mit Script (empfohlen)
python scripts/create_info_packet.py \
    --source test_health_automation \
    --category test_automation \
    --severity warning \
    --summary "Health-Score 100.0/100.0, alle Checks bestanden." \
    --links "reports/test_health/20251211_143920_daily_quick/summary.md" \
    --tags "test_health,nightly,monitoring"

# Oder manuell: Template aus TEMPLATES.md kopieren und ausfüllen
```

### Schritt 3: INFO_PACKET in KI-Chat einfügen

Das generierte INFO_PACKET in einen KI-Chat kopieren, der mit dem **Datenauswertungsspezialisten-Prompt** konfiguriert ist.

Siehe: [PROMPTS.md](PROMPTS.md)

### Schritt 4: EVAL_PACKAGE + LEARNING_SNIPPET erhalten

Die KI generiert:
- **EVAL_PACKAGE**: Strukturierte Auswertung mit Empfehlungen
- **LEARNING_SNIPPET**: Kompakte Erkenntnis für langfristiges Lernen

### Schritt 5: Learnings dokumentieren

Das LEARNING_SNIPPET in die passende Stelle übernehmen:
- `docs/mindmap/INFOSTREAM_LEARNING_LOG.md` (primär)
- Relevantes Mindmap-Thema (z.B. `50_AI_WORKFLOW_IDEAS.md`)
- Operator-Runbook oder Doku (bei konkreten Prozess-Änderungen)

---

## Severity-Level

| Level | Bedeutung | Typische Reaktion |
|-------|-----------|-------------------|
| `info` | Normale Information | Zur Kenntnis nehmen |
| `warning` | Auffälligkeit, keine akute Gefahr | Beobachten, ggf. Ticket erstellen |
| `error` | Fehler im System | Zeitnah untersuchen |
| `critical` | Kritischer Fehler, Handlungsbedarf | Sofort handeln |

---

## Tags (Konvention)

Tags helfen beim Clustern und späteren Filtern:

```
# Quellen-Tags
test_health, trigger_training, offline_realtime, macro, operator

# Themen-Tags
monitoring, automation, strategy, risk, psychology, performance

# Status-Tags
learning.*, pattern.*, candidate.*, action.*
```

Beispiele:
- `learning.test_health` → Erkenntnis über TestHealth-System
- `pattern.expected_failure` → Erkanntes Muster für erwartete Fehler
- `candidate.doc_update` → Kandidat für Doku-Aktualisierung
- `action.config_change` → Erfordert Config-Änderung

---

## Integration mit bestehenden Systemen

### TestHealth-Automation

```bash
# Nach einem Nightly-Run kann automatisch ein INFO_PACKET generiert werden
# Siehe: .github/workflows/test-health-automation.yml
```

### Trigger-Training

```bash
# Nach einer Trigger-Training-Session
python scripts/create_info_packet.py \
    --source trigger_training_sessions \
    --category operator_training \
    --severity info \
    --summary "Session abgeschlossen, 3 Trigger erkannt" \
    --links "reports/trigger_training/session_xyz.html"
```

### Makro/GeoRisk

```bash
# Nach einer Makro-Analyse
python scripts/create_info_packet.py \
    --source macro_georisk_specialist \
    --category market_analysis \
    --severity warning \
    --summary "Erhöhte Volatilität erwartet wegen Event X"
```

---

## Roadmap

### v0 (Aktuell)
- [x] Text-Konvention (INFO_PACKET, EVAL_PACKAGE, LEARNING_SNIPPET)
- [x] Prompts für InfoStream-Collector und Datenauswertungsspezialisten
- [x] Hilfs-Script für Paket-Erstellung
- [x] Learning-Log in Mindmap

### v1 (Geplant)
- [ ] Python-Modul `src/meta/infostream/`
- [ ] `IntelEvent` Dataclass
- [ ] JSON-Speicherung statt Text
- [ ] Script `scripts/register_infostream_event.py`

### v2 (Zukunft)
- [ ] HTML-Dashboard (Tailwind) in bestehender Web-UI
- [ ] Filter nach Quelle, Severity, Tag
- [ ] Integration mit Trigger-Training- und TestHealth-Reports
- [ ] Export für Operator-Trainings

---

## Makro/GeoRisk-Integration

Der InfoStream unterstützt die Erfassung von Makro-Events und geopolitischen Risiken:

### Quick-Mode für häufige Events

```bash
# FED-Entscheidung
python scripts/create_macro_event.py --quick fed_hike

# Inflationsdaten
python scripts/create_macro_event.py --quick cpi_high

# Regulierung
python scripts/create_macro_event.py --quick regulation

# Kritisches Event
python scripts/create_macro_event.py --quick black_swan
```

### Interaktiver Modus

```bash
python scripts/create_macro_event.py --interactive
```

### Verfügbare Quick-Templates

| Template | Beschreibung |
|----------|--------------|
| `fed_hike` | FED Zinserhöhung |
| `fed_cut` | FED Zinssenkung |
| `cpi_high` | Inflation über Erwartungen |
| `cpi_low` | Inflation unter Erwartungen |
| `regulation` | Neue Crypto-Regulierung |
| `exchange_issue` | Exchange-Problem |
| `geopolitics` | Geopolitische Spannungen |
| `black_swan` | Kritisches/Unerwartetes Event |

Siehe: [MACRO_GEORISK_PROMPT.md](MACRO_GEORISK_PROMPT.md) für den KI-Agenten-Prompt.

---

## Siehe auch

- [PROMPTS.md](PROMPTS.md) – KI-Prompts für Collector & Evaluator
- [MACRO_GEORISK_PROMPT.md](MACRO_GEORISK_PROMPT.md) – Makro/GeoRisk-Spezialist Prompt
- [TEMPLATES.md](TEMPLATES.md) – Format-Templates
- [INFOSTREAM_LEARNING_LOG.md](../mindmap/INFOSTREAM_LEARNING_LOG.md) – Gesammelte Learnings
- [README_MINDMAP.md](../mindmap/README_MINDMAP.md) – Mindmap-Übersicht
