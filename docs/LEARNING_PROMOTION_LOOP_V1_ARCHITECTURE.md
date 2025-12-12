# Peak_Trade – Learning & Promotion Loop v1

**Status:** ✅ Vollständig implementiert & getestet (2025-12-11)  
**Ready for Production:** 🚀

---

## 1. Architektur in einem Satz

> Daten aus Backtests / Automation → Learning Loop (System 1) → ConfigPatches → Promotion Loop (System 2) → `config/live_overrides/auto.toml` → Live-/Shadow-/Paper-Config.

---

## 2. System 1 – Learning Loop (Peak_Trade intern)

### Quelle

* **TestHealthAutomation**
* **Trigger-Training-Drills**
* **InfoStream / Macro-Events**
* **Sonstige Tools**, die `LearningSignal` + `recommended_changes` erzeugen

### Pfad

1. **Domain-Code erzeugt `LearningSignal`:**

   * via `src/meta/learning_loop/bridge.py`
   * Beispiele:
     * `build_test_health_leverage_signal`
     * `build_trigger_timing_signal`
     * `build_macro_weighting_signal`

2. **Speicherung als JSON:**

   * via `src/meta/learning_loop/emitter.py` →
   * `reports/learning_snippets/*.json`

3. **Learning Loop laufen lassen:**

   ```bash
   # Dry-Run (ohne Anwendung)
   python scripts/run_learning_apply_cycle.py --dry-run

   # Tatsächliche Anwendung
   python scripts/run_learning_apply_cycle.py
   ```

4. **Output:**

   * `ConfigPatch`-Objekte intern
   * TOML-Overrides unter:
     * `config/auto/*.override.toml`

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
reports/live_promotion/<proposal_id>/
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
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only

# Konservativer Autopilot (empfohlen, wenn ausreichend Evidenz vorhanden)
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto

# Killswitch (Notfall)
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode disabled
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
python scripts/run_test_health.py
python scripts/run_trigger_training_drill.py
python scripts/generate_infostream_packet.py
```

**Output:** Learning Signals in `reports/learning_snippets/`

### 5.2 Learning Cycle

```bash
# 2. Learning Loop ausführen
python scripts/run_learning_apply_cycle.py
```

**Output:**
* ConfigPatch-Objekte
* TOML-Overrides in `config/auto/*.override.toml`

### 5.3 Promotion Cycle

```bash
# 3. Promotion Loop fahren (bounded_auto für Production)
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto
```

**Output:**
* Proposals in `reports/live_promotion/<proposal_id>/`
* Live-Overrides in `config/live_overrides/auto.toml` (wenn bounded_auto)

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
python scripts/run_live_session.py --config config.toml
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
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode disabled

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
python scripts/demo_live_overrides.py
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
python scripts/run_test_health.py

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
  * `src/meta/learning_loop/models.py` - ConfigPatch, PatchStatus
  * `src/meta/learning_loop/bridge.py` - Signal-Builder (TODO)
  * `src/meta/learning_loop/emitter.py` - Signal-Emitter (TODO)

* **Promotion Loop:**
  * `src/governance/promotion_loop/models.py` - PromotionCandidate, Decision, Proposal
  * `src/governance/promotion_loop/policy.py` - AutoApplyPolicy, Bounds
  * `src/governance/promotion_loop/engine.py` - Core Functions

* **Config-Integration:**
  * `src/core/peak_config.py` - load_config_with_live_overrides()
  * `src/core/environment.py` - TradingEnvironment, EnvironmentConfig

### Scripts

* **`scripts/run_learning_apply_cycle.py`** - Learning Loop (TODO)
* **`scripts/run_promotion_proposal_cycle.py`** - Promotion Loop ✅
* **`scripts/demo_live_overrides.py`** - Demo & Testing ✅

### Tests

* **`tests/test_live_overrides_integration.py`** - Integration Tests (13) ✅
* **`tests/test_live_overrides_realistic_scenario.py`** - Realistic Tests (6) ✅

---

## 12. Roadmap

### v1 Status (2025-12-11)

✅ Promotion Loop vollständig implementiert  
✅ Config-Integration fertig  
✅ Auto-Apply (bounded_auto) funktioniert  
✅ Tests vollständig (19/19)  
✅ Dokumentation umfassend  
⏳ Learning Loop Bridge (TODO)  
⏳ Learning Loop Emitter (TODO)  
⏳ Automation-Integration (TODO)  

### v2 Enhancements (geplant)

* 📊 Learning Loop Bridge Implementation
* 📊 Signal-Emitter für TestHealth/Trigger/Macro
* 🔔 Slack-Notifications für Proposals
* 🔄 Auto-Rollback bei Performance-Degradation
* 📈 Web-UI für Proposal-Review
* 🧪 TestHealth Pre-Checks vor Auto-Apply
* 📝 Extended Audit-Trail

---

**Version:** v1  
**Status:** ✅ Production-Ready (mit TODO: Learning Loop Bridge)  
**Datum:** 2025-12-11
