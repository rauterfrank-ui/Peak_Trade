# Promotion Loop v0: Governance Layer für Live-Deployment

## Überblick

Der **Promotion Loop v0** ist die Governance-Schicht zwischen dem Learning Loop (System 1) und Live-Deployments. Er filtert, bewertet und materialisiert Config-Patches als Live-Promotion-Proposals.

## Architektur

```
Learning Loop (System 1)
    ↓ ConfigPatch[]
Promotion Loop (Governance)
    ↓ PromotionProposal[]
    ├─→ Reports (immer)
    └─→ Live Overrides (optional, bounded_auto)
```

## Komponenten

### 1. Models (`src/governance/promotion_loop/models.py`)

- **`PromotionCandidate`**: Wrapper um ConfigPatch mit Governance-Metadaten
  - `tags`: Automatische Kategorisierung (leverage, risk, macro, trigger)
  - `eligible_for_live`: Muss explizit gesetzt werden (v0: default False)
  - `notes`: Zusätzliche Notizen

- **`PromotionDecision`**: Ergebnis der Governance-Filter
  - `status`: PENDING | REJECTED_BY_POLICY | REJECTED_BY_SANITY_CHECK | ACCEPTED_FOR_PROPOSAL
  - `reasons`: Liste von Begründungen

- **`PromotionProposal`**: Gebündelte akzeptierte Kandidaten
  - `proposal_id`: Eindeutige ID mit Timestamp
  - `decisions`: Liste aller Entscheidungen
  - `output_dir`: Pfad zu materialisierten Artifacts

### 2. Policy (`src/governance/promotion_loop/policy.py`)

- **`AutoApplyBounds`**: Numerische Grenzen für Auto-Apply
  - `min_value`, `max_value`: Absolute Grenzen
  - `max_step`: Maximale Änderung pro Update

- **`AutoApplyPolicy`**: Steuerung des Auto-Apply-Verhaltens
  - **`disabled`**: Keine Proposals, kein Auto-Apply
  - **`manual_only`**: Nur Proposals, kein Auto-Apply (Standard)
  - **`bounded_auto`**: Proposals + Auto-Apply innerhalb von Bounds

### 3. Engine (`src/governance/promotion_loop/engine.py`)

**Kernfunktionen:**

1. **`build_promotion_candidates_from_patches()`**
   - Filtert Patches mit Status APPLIED_OFFLINE oder PROMOTED
   - Erstellt Tags basierend auf Target-Heuristik
   - eligible_for_live bleibt False (muss extern gesetzt werden)

2. **`filter_candidates_for_live()`**
   - Verwirft alle Kandidaten mit eligible_for_live=False
   - Sanity Checks (z.B. Leverage Hard Limit: 3.0)
   - Gibt PromotionDecision[] zurück

3. **`build_promotion_proposals()`**
   - Gruppiert akzeptierte Decisions
   - v0: Genau eine Proposal pro Durchlauf

4. **`materialize_promotion_proposals()`**
   - Schreibt Artifacts nach `reports&#47;live_promotion&#47;<proposal_id>&#47;`
   - `proposal_meta.json`: Metadaten
   - `config_patches.json`: Alle Patches mit Decisions
   - `OPERATOR_CHECKLIST.md`: Operator-Checkliste

5. **`apply_proposals_to_live_overrides()`**
   - Optional: Nur in `bounded_auto` Modus
   - Schreibt akzeptierte numerische Patches in TOML
   - Respektiert AutoApplyBounds (min/max/step)
  - Pfad: `config&#47;live_overrides&#47;auto.toml` (konfigurierbar)

## Nutzung

### Script: `scripts/run_promotion_proposal_cycle.py`

```bash
# Nur Proposals (kein Auto-Apply)
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only

# Bounded Auto-Apply (innerhalb von Bounds)
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto

# Komplett deaktiviert
python3 scripts/run_promotion_proposal_cycle.py --auto-apply-mode disabled

# Custom Pfade
python3 scripts/run_promotion_proposal_cycle.py \
  --output-dir reports/my_proposals \
  --live-overrides-path config/live/my_auto.toml \
  --auto-apply-mode bounded_auto
```

### Default Bounds (bounded_auto Modus)

```python
leverage_bounds = AutoApplyBounds(
    min_value=1.0,
    max_value=2.0,
    max_step=0.25
)

trigger_delay_bounds = AutoApplyBounds(
    min_value=3.0,
    max_value=15.0,
    max_step=2.0
)

macro_weight_bounds = AutoApplyBounds(
    min_value=0.0,
    max_value=0.8,
    max_step=0.1
)
```

## Workflow

1. **Learning Loop** generiert ConfigPatch-Objekte
2. **Promotion Loop** lädt Patches (`_load_patches_for_promotion()`)
3. **Build Candidates**: Filtert nach Status, erstellt Tags
4. **Apply Filters**: Governance-Checks, Sanity-Limits
5. **Generate Proposals**: Bündelt akzeptierte Decisions
6. **Materialize**: Schreibt Reports
7. **Auto-Apply** (optional): Schreibt Live-Overrides in bounded_auto

## Integration (TODO für v1)

Die Funktion `_load_patches_for_promotion()` muss implementiert werden:

```python
def _load_patches_for_promotion() -> List[ConfigPatch]:
    """
    Implementierung für Peak_Trade:
    - Lade ConfigPatch-Objekte aus Learning Loop Store
    - z.B. JSON-Export lesen
    - Oder direkter Zugriff auf Learning Loop Session Store
    """
    # TODO: Anbindung an Peak_Trade Learning Loop
    raise NotImplementedError("...")
```

## Sicherheits-Features

### v0 Konservativer Ansatz

1. **Default eligible_for_live=False**
   - Alle Kandidaten müssen explizit freigegeben werden

2. **Hard Limits**
   - Leverage: Maximaler Wert 3.0

3. **Bounded Auto-Apply**
   - Nur numerische Werte
   - Nur innerhalb definierter Bounds
   - Nur bei passenden Tags (leverage/trigger/macro)

4. **Operator Checkliste**
   - Jede Proposal enthält eine Checkliste
   - Manuelle Review-Pflicht

5. **Keine R&D-Strategien**
   - Filter muss in v1 implementiert werden

## Outputs

### Reports (immer erstellt)

```
reports/live_promotion/<proposal_id>/
├── proposal_meta.json        # Metadaten
├── config_patches.json        # Alle Patches mit Decisions
└── OPERATOR_CHECKLIST.md      # Operator-Review-Checkliste
```

### Live Overrides (nur bounded_auto)

```toml
# config/live_overrides/auto.toml
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
"macro.regime_weight" = 0.35
```

## Nächste Schritte (v1)

1. **Learning Loop Anbindung**
   - `_load_patches_for_promotion()` implementieren
   - Session Store Integration

2. **Erweiterte Filters**
   - R&D-Strategy-Detection
   - Multi-Dimensional Risk Scoring
   - Historical Performance Check

3. **Notification Integration**
   - Slack-Alerts für neue Proposals
   - Operator-Approval-Workflow

4. **Audit Trail**
   - Vollständige History aller Decisions
   - Git-Integration für Live-Overrides

5. **TestHealth Integration**
   - Automatische Pre-Promotion-Tests
   - Go/No-Go basierend auf TestHealth

## Config-Integration

Die automatisch generierten `auto.toml` Overrides werden nahtlos in die Laufzeit-Config integriert:

```python
from src.core.peak_config import load_config_with_live_overrides

# Lädt config.toml + wendet auto.toml an (nur in Live-Environments)
cfg = load_config_with_live_overrides()
```

**Details:** Siehe [LIVE_OVERRIDES_CONFIG_INTEGRATION.md](./LIVE_OVERRIDES_CONFIG_INTEGRATION.md)

**Wichtig:**
- Overrides werden **nur** in Live-nahen Environments angewendet (live/testnet)
- Paper-Backtests bleiben unverändert
- Graceful Degradation: Missing/invalid auto.toml führt nicht zu Fehlern

## Status: v0 (2025-12-11)

✅ Grundarchitektur implementiert
✅ Models und Policy definiert
✅ Engine-Funktionen vollständig
✅ Script mit CLI fertig
✅ Bounded Auto-Apply implementiert
✅ Config-Integration vollständig (live_overrides/auto.toml)
✅ Tests vollständig (13/13 grün)
⏳ Learning Loop Integration (TODO)
⏳ TestHealth Pre-Checks (TODO)
⏳ Notification Integration (TODO)
