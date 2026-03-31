# Peak_Trade – Learning & Promotion Loop v1

**Dokument-Stand:** Konzept + Referenz für Operator-Flows; **Repo-Stand** siehe unten.

**Implementierungsstand (Repo, kurz):**

| Teil | Status |
|------|--------|
| **Promotion / Live-Overrides / Governance** (System 2) | Überwiegend umgesetzt — siehe Skripte unter `scripts/` und Tests/Doku zu Overrides. |
| **Learning Snippets → Overrides** | `scripts&#47;run_learning_apply_cycle.py` liest `reports&#47;learning_snippets&#47;` (`*.json` / `*.jsonl`) und schreibt `config&#47;auto&#47;learning.override.toml`. |
| **`src&#47;meta&#47;learning_loop&#47;`** | `models.py` (`ConfigPatch`, `PatchStatus`), **`emitter.py`** (`emit_learning_snippet`), **`bridge.py`** (`normalize_patches`). |
| **Bridge vs. Emitter** | **Bridge:** rein funktional **Domäne → Patch-Liste** (`normalize_patches`, kein I/O). **Emitter:** **Dateischreiben** JSON/JSONL unter `reports&#47;learning_snippets&#47;`. Spätere domänenspezifische Producer bauen auf der Bridge auf. |

*(Ältere Formulierungen „vollständig implementiert“ bezogen sich auf ein Zielbild; die Tabelle oben ist die maßgebliche Abgrenzung **vorhanden vs. geplant**.)*

---

## 1. Architektur in einem Satz

> Daten aus Backtests / Automation → Learning Loop (System 1) → ConfigPatches → Promotion Loop (System 2) → `config&#47;live_overrides&#47;auto.toml` → Live-/Shadow-/Paper-Config.

---

## 2. System 1 – Learning Loop (Peak_Trade intern)

Die **Bridge** (`normalize_patches` in `bridge.py`) überführt Rohdaten (z. B. generisches Mapping mit `patches` oder einzelnem `target`) **nur im Speicher** in eine kanonische **Liste von Patch-Dicts** — dieselbe Struktur, die `scripts&#47;run_learning_apply_cycle.py` aus Snippet-Dateien erwartet. Der **Emitter** (`emit_learning_snippet`) ist getrennt davon zuständig: **deterministisches Schreiben** dieser Inhalte nach `reports&#47;learning_snippets&#47;` (JSON oder JSONL). Weder Bridge noch Emitter schreiben TOML; das übernimmt ausschließlich das Apply-Skript.

### Quelle

* **TestHealthAutomation**
* **Trigger-Training-Drills**
* **InfoStream / Macro-Events**
* **Sonstige Tools**, die `LearningSignal` + `recommended_changes` erzeugen

### Pfad

1. **Domain-Code erzeugt Signale / Patch-Daten** (Zielbild: `LearningSignal` + `recommended_changes`; v1-API: **`normalize_patches`** für generische Mappings):

   * **Vorhanden:** `src&#47;meta&#47;learning_loop&#47;bridge.py` — `normalize_patches` (Domäne/Rohdaten → Liste von Patch-Dicts, ohne I/O)
   * Beispiele (Konzept):
     * `build_test_health_leverage_signal`
     * `build_trigger_timing_signal`
     * `build_macro_weighting_signal`

2. **Speicherung als JSON/JSONL unter `reports&#47;learning_snippets&#47;`:**

   * **Vorhanden:** `src&#47;meta&#47;learning_loop&#47;emitter.py` — `emit_learning_snippet(...)` (atomar, deterministisch; optional `json` oder `jsonl`, kompatibel mit `scripts&#47;run_learning_apply_cycle.py`)
   * Alternativ weiterhin manuell oder über andere Skripte dieselbe Verzeichnis-Konvention

3. **Learning Loop laufen lassen:**

   ```bash
   # Dry-Run (ohne Anwendung)
   python3 scripts/run_learning_apply_cycle.py --dry-run

   # Tatsächliche Anwendung
   python3 scripts/run_learning_apply_cycle.py
   ```

4. **Output:**

   * `ConfigPatch`-Objekte intern
   * TOML-Overrides unter:
     * `config&#47;auto&#47;*.override.toml`

### Scope

* ✅ Nur Offline / Backtest / Drills
* ❌ Kein Live-Trading, keine Orders
* ✅ Automatische Optimierung basierend auf Evidenz

---

## 3. System 2 – Promotion Loop (Governance & Live-Auto-Apply)

### Input

* `ConfigPatch`-Instanzen aus dem Learning Loop
* via `_load_patches_for_promotion()`

### Schritte

#### 3.1 Patches → PromotionCandidates

```python
build_promotion_candidates_from_patches(...)
```

* **Tagging** basierend auf Target:
  * `leverage` - Hebel-Parameter
  * `risk` - Risiko-Parameter
  * `macro` - Makro-Regime-Parameter
  * `trigger` - Trigger-Timing-Parameter

* **eligible_for_live:**
  * Default: `False`
  * Muss per Policy/Operator explizit gesetzt werden

#### 3.2 Governance-Filter

```python
filter_candidates_for_live(...)
```

**Policies:**

* `eligible_for_live` muss `True` sein
* **Hard-Limits:**
  * Leverage-Hardlimit: 3.0 (nicht überschreitbar)
  * Weitere Sanity-Checks

**Decision-Status:**

* `PENDING` - Noch nicht bewertet
* `REJECTED_BY_POLICY` - Von Policy abgelehnt
* `REJECTED_BY_SANITY_CHECK` - Sanity-Check fehlgeschlagen
* `ACCEPTED_FOR_PROPOSAL` - Für Promotion akzeptiert

#### 3.3 Proposals bauen

```python
build_promotion_proposals(...)
```

**Output:** `PromotionProposal`-Objekt(e)

* `proposal_id` - Eindeutige ID mit Timestamp
* `title` - Proposal-Titel
* `description` - Beschreibung
* `decisions[]` - Liste aller PromotionDecisions
* `meta` - Metadaten

#### 3.4 Materialisierung

```text
reports&#47;live_promotion&#47;<proposal_id>&#47;
├── proposal_meta.json          # Metadaten
├── config_patches.json         # Alle Patches mit Decisions
└── OPERATOR_CHECKLIST.md       # Operator-Review-Checkliste
```

**Checkliste enthält:**

* Zusammenfassung der Änderungen
* Sicherheits-Checks
* Go/No-Go Entscheidungshilfe
* Detaillierte Patch-Informationen

#### 3.5 Optional: Auto-Apply in Live-Overrides

```python
apply_proposals_to_live_overrides(...)
```

**Schreibt nach:**

```toml
# config/live_overrides/auto.toml
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
"macro.regime_weight" = 0.35
```

### Modi (AutoApplyPolicy.mode)

#### `"disabled"` - Killswitch

* ❌ Keine Auto-Apply
* ❌ Keine Proposals
* Verwendung: Notfall-Deaktivierung

#### `"manual_only"` - Nur Proposals

* ✅ Generiert Proposals
* ❌ Kein Live-Override-Schreiben
* Verwendung: Manuelle Review vor jeder Änderung

#### `"bounded_auto"` - Konservativer Autopilot (⭐ Empfohlen)

* ✅ Proposals **+** Auto-Apply
* ✅ Innerhalb definierter Bounds
* **Bounds:**
  * `leverage_bounds`: 1.0–2.0 (max_step: 0.25)
  * `trigger_delay_bounds`: 3.0–15.0 (max_step: 2.0)
  * `macro_weight_bounds`: 0.0–0.8 (max_step: 0.1)

**Verwendung:** Production mit ausreichender Evidenz

### Script

```bash
# Nur Proposals (sichere Default-Variante)
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only

# Konservativer Autopilot (empfohlen, wenn ausreichend Evidenz vorhanden)
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto

# Killswitch (Notfall)
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode disabled
```

---

## 4. Config-Layer – Live-Overrides anwenden

### Datei

```toml
# config/live_overrides/auto.toml
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
"macro.regime_weight" = 0.35
```

### Integration

**Zentrale Config-Ladefunktion:**

```python
from src.core.peak_config import load_config_with_live_overrides

# Lädt Basis-Config + wendet auto.toml an (nur in Live-Environments)
cfg = load_config_with_live_overrides()
```

**Workflow:**

1. **Basis-Config** aus `config.toml` + internen Layers
2. **Environment-Erkennung:**
   * Live-nahe Environments: `live`, `live_dry_run`, `shadow`, `paper_live`, `testnet`
   * Paper-Environments: Keine Overrides
3. **Laden von `auto.toml`:**
   * via `_load_live_auto_overrides()`
4. **Anwenden der Dotted-Keys:**
   * via `cfg.with_overrides(overrides)`
   * Nutzt existierende `PeakConfig.with_overrides()` Methode

### Effektive Werte

```python
cfg.get("portfolio.leverage")      # -> 1.75 (statt 1.0)
cfg.get("strategy.trigger_delay")  # -> 8.0 (statt 10.0)
cfg.get("macro.regime_weight")     # -> 0.35 (statt 0.0)
```

### Environment-Gating

| Environment | Auto-Overrides angewendet? |
|------------|---------------------------|
| `paper` | ❌ Nein |
| `testnet` | ✅ Ja |
| `live` | ✅ Ja |
| `shadow` | ✅ Ja |
| `paper_live` | ✅ Ja |
| `live_dry_run` | ✅ Ja |

---

## 5. Operator-Flow in der Praxis

### 5.1 Setup Phase

```bash
# 1. Automation / Tests laufen lassen
python3 scripts/run_test_health.py
python3 scripts/run_trigger_training_drill.py
python3 scripts/generate_infostream_packet.py
```

**Output:** Learning Signals in `reports&#47;learning_snippets&#47;`

### 5.2 Learning Cycle

```bash
# 2. Learning Loop ausführen
python3 scripts/run_learning_apply_cycle.py
```

**Output:**
* ConfigPatch-Objekte
* TOML-Overrides in `config&#47;auto&#47;*.override.toml`

### 5.3 Promotion Cycle

```bash
# 3. Promotion Loop fahren (bounded_auto für Production)
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto
```

**Output:**
* Proposals in `reports&#47;live_promotion&#47;<proposal_id>&#47;`
* Live-Overrides in `config&#47;live_overrides&#47;auto.toml` (wenn bounded_auto)

### 5.4 Review Phase

```bash
# 4. Proposals checken
cat reports/live_promotion/<latest>/OPERATOR_CHECKLIST.md
```

**Checkliste prüfen:**

* [ ] Sind die Änderungen sicher für Live?
* [ ] Keine R&D-Strategien enthalten?
* [ ] Risk Limits eingehalten?
* [ ] Leverage innerhalb Bounds?
* [ ] TestHealth / Backtests durchgeführt?

### 5.5 Execution Phase

```bash
# 5. Live-/Shadow-Session starten
python3 scripts/run_live_session.py --config config/config.toml
```

**Config-Loader verwendet:**

```python
cfg = load_config_with_live_overrides()
```

**Verhalten beobachten:**

* Leverage-Anpassungen
* Trigger-Timing-Änderungen
* Regime-Gewichtungen

### 5.6 Rollback (wenn nötig)

```bash
# Option 1: Modus wechseln
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode disabled

# Option 2: auto.toml zurücksetzen
cp config/live_overrides/auto.toml.backup config/live_overrides/auto.toml

# Option 3: auto.toml leeren
echo '[auto_applied]' > config/live_overrides/auto.toml
```

---

## 6. Sicherheits-Features

### 6.1 Environment-basiertes Gating

* ✅ Overrides **nur** in Live-nahen Environments
* ✅ Paper-Backtests **vollständig isoliert**
* ✅ Explizite Environment-Detection

### 6.2 Bounded Auto-Apply

* ✅ Numerische Bounds (min/max/step)
* ✅ Nur validierte Parameter-Types
* ✅ Inkrementelle Änderungen (max_step)

### 6.3 Graceful Degradation

* ✅ Missing `auto.toml`: Config lädt normal
* ✅ Invalid TOML: Warning + Fallback
* ✅ Non-existent paths: Override ignoriert

### 6.4 Governance-Firewall

* ✅ `eligible_for_live` Default: False
* ✅ Hard Limits (Leverage: 3.0)
* ✅ Operator-Checkliste für manuelle Review

### 6.5 Audit Trail

* ✅ Alle Proposals materialisiert
* ✅ Config-History in Git
* ✅ Learning Signals gespeichert
* ✅ Promotion Decisions protokolliert

---

## 7. Monitoring & Observability

### 7.1 Learning Loop Monitoring

```bash
# Prüfe Learning Signals
ls -lh reports/learning_snippets/

# Letzte Signals anschauen
cat reports/learning_snippets/latest_*.json | jq .
```

### 7.2 Promotion Loop Monitoring

```bash
# Aktive Proposals
ls -lh reports/live_promotion/

# Letzte Proposal anschauen
cat reports/live_promotion/latest/proposal_meta.json | jq .
```

### 7.3 Live-Overrides Monitoring

```bash
# Aktuelle Overrides
cat config/live_overrides/auto.toml

# Config-Diff
python3 scripts/demo_live_overrides.py
```

### 7.4 Console Output

Beim Config-Laden mit Overrides:

```
[peak_config] Applying 3 live auto-overrides from config/live_overrides/auto.toml
[peak_config]   portfolio.leverage = 1.75
[peak_config]   strategy.trigger_delay = 8.0
[peak_config]   macro.regime_weight = 0.35
```

---

## 8. Troubleshooting

### Problem: Learning Loop findet keine Signals

**Lösung:**
```bash
# 1. Prüfe ob Learning Snippets vorhanden sind
ls reports/learning_snippets/

# 2. Prüfe ob Automation läuft
python3 scripts/run_test_health.py

# 3. Prüfe Emitter-Konfiguration
grep -r "LearningSignal" src/
```

### Problem: Promotion Loop lehnt alle Candidates ab

**Lösung:**
```bash
# eligible_for_live ist Default False
# Muss in v1 explizit per Policy gesetzt werden

# Workaround für Testing:
# In run_promotion_proposal_cycle.py temporär:
for candidate in candidates:
    candidate.eligible_for_live = True  # NUR FÜR TESTS
```

### Problem: auto.toml wird nicht angewendet

**Lösung:**
```python
# Prüfe Environment
from src.core.peak_config import load_config, _is_live_like_environment
cfg = load_config()
print(cfg.get("environment.mode"))  # Sollte "live" oder "testnet" sein
print(_is_live_like_environment(cfg))  # Sollte True sein

# Prüfe ob richtige Funktion genutzt wird
# ❌ Falsch: load_config()
# ✅ Richtig: load_config_with_live_overrides()
```

### Problem: Bounds zu eng

**Lösung:**
```python
# In run_promotion_proposal_cycle.py anpassen:
policy = AutoApplyPolicy(
    mode="bounded_auto",
    leverage_bounds=AutoApplyBounds(
        min_value=1.0,
        max_value=3.0,  # Erhöhen (aber Vorsicht!)
        max_step=0.5    # Größere Schritte
    ),
)
```

---

## 9. Best Practices

### 9.1 Development

* ✅ Starte mit `manual_only` Modus
* ✅ Teste ausgiebig in Paper-Environment
* ✅ Nutze `force_apply_overrides=True` für Tests
* ✅ Prüfe alle Proposals manuell

### 9.2 Staging

* ✅ Nutze `bounded_auto` mit engen Bounds
* ✅ Shadow-Trading für Beobachtung
* ✅ Inkrementelle Bound-Erweiterungen
* ✅ Frequent Reviews

### 9.3 Production

* ✅ `bounded_auto` mit bewährten Bounds
* ✅ Automated Monitoring
* ✅ Rollback-Plan bereit
* ✅ Operator-Checkliste immer prüfen

### 9.4 Emergency

* ✅ Killswitch: `--auto-apply-mode disabled`
* ✅ Backup von `auto.toml` vorhalten
* ✅ Git-Revert für Config-Files
* ✅ Live-Sessions können ohne Overrides starten

---

## 10. Merk-Satz

> **System 1** optimiert dein Modell.  
> **System 2** entscheidet, was davon an den Live-Rand darf.  
> Alles andere bleibt hinter der Governance-Firewall.

---

## 11. Weiterführende Dokumentation

### Detaillierte Dokumentation

* **[PROMOTION_LOOP_V0.md](./PROMOTION_LOOP_V0.md)** - Promotion Loop Architektur
* **[LIVE_OVERRIDES_CONFIG_INTEGRATION.md](./LIVE_OVERRIDES_CONFIG_INTEGRATION.md)** - Config-Integration Details
* **[QUICKSTART_LIVE_OVERRIDES.md](./QUICKSTART_LIVE_OVERRIDES.md)** - Quickstart Guide
* **[IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md](./IMPLEMENTATION_SUMMARY_LIVE_OVERRIDES.md)** - Implementation Summary

### Code-Referenzen

* **Learning Loop:**
  * `src&#47;meta&#47;learning_loop&#47;models.py` - ConfigPatch, PatchStatus
  * `src&#47;meta&#47;learning_loop&#47;emitter.py` - emit_learning_snippet (Snippet-Dateien)
  * `src&#47;meta&#47;learning_loop&#47;bridge.py` - `normalize_patches` (Domäne → Patch-Liste)

* **Promotion Loop:**
  * `src/governance/promotion_loop/models.py` - PromotionCandidate, Decision, Proposal
  * `src/governance/promotion_loop/policy.py` - AutoApplyPolicy, Bounds
  * `src/governance/promotion_loop/engine.py` - Core Functions

* **Config-Integration:**
  * `src/core/peak_config.py` - load_config_with_live_overrides()
  * `src/core/environment.py` - TradingEnvironment, EnvironmentConfig

### Scripts

* **`scripts&#47;run_learning_apply_cycle.py`** - Learning Loop ✅
* **`scripts/run_promotion_proposal_cycle.py`** - Promotion Loop ✅
* **`scripts&#47;demo_live_overrides.py`** - Demo & Testing ✅

### Tests

* **`tests/test_live_overrides_integration.py`** - Integration Tests (13) ✅
* **`tests/test_live_overrides_realistic_scenario.py`** - Realistic Tests (6) ✅

---

## 12. Roadmap

### v1 Status (Repo-Stand, 2026-03-31)

✅ Promotion Loop vollständig implementiert  
✅ Config-Integration fertig  
✅ Auto-Apply (bounded_auto) funktioniert  
✅ Tests vollständig (19/19)  
✅ Dokumentation umfassend  
✅ **Learning Loop Emitter** vorhanden (`emit_learning_snippet` → Snippets unter `reports&#47;learning_snippets&#47;`)  
✅ **Learning Loop Bridge** vorhanden (`normalize_patches` — reine Payload-Normalisierung, kein I/O)  
⏳ **Domänen-/Automation-Anbindung** (TestHealth, Trigger, Macro, …) auf Bridge/Emitter — **optional**, kein Blocker für v1-Overrides  

### v2 Enhancements (optional / später)

Die folgenden Punkte sind **Wunschliste**, keine feste Roadmap-Phase — Umsetzung nur bei **Produkt- und Governance-Priorität** und weiterhin im **NO-LIVE**-Default, sofern nicht ausdrücklich anders freigegeben.

* 📊 Gezielte Anbindungen konkreter Quellen an `normalize_patches` / `emit_learning_snippet` (statt generischer Mappings allein)
* 🔔 Slack-Notifications für Proposals
* 🔄 Auto-Rollback bei Performance-Degradation
* 📈 Web-UI für Proposal-Review
* 🧪 TestHealth Pre-Checks vor Auto-Apply
* 📝 Extended Audit-Trail

---

**Version:** v1  
**Status:** ✅ Production-Ready (Learning Loop: Emitter + Bridge-Normalizer im Repo; siehe §2 und Code-Referenzen)  
**Datum:** 2026-03-31
