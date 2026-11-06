# Phase 83: Live-Gating & Risk Policies v1.0

## Übersicht

**Status:** ✅ Implementiert
**Phase:** 83
**Ziel:** Tiering- und Policy-basierte Live-Eligibility-Prüfung

Phase 83 etabliert ein Gate-System, das Research-Ergebnisse (Tiering, Performance-Metriken) als Voraussetzung für Shadow/Testnet/Live-Runs nutzt. Nur Strategien und Portfolios, die definierte Kriterien erfüllen, kommen in die Nähe eines Live-Runs.

---

## Motivation

**Problem:** Ohne automatische Gates könnten:
- Legacy-Strategien versehentlich live gehen
- Schlecht performende Strategien aktiviert werden
- Nicht getestete Kombinationen deployed werden

**Lösung:** Ein Live-Gate-System das:
- Tiering-Status prüft (core/aux/legacy)
- Performance-Metriken validiert (Sharpe, MaxDD)
- Portfolio-Diversifikation sicherstellt
- Klare Fehlermeldungen bei Nicht-Eligibility liefert

---

## Neue Komponenten

### 1. Modul: `src/live/live_gates.py`

#### Kern-Funktionen

| Funktion | Beschreibung |
|----------|--------------|
| `check_strategy_live_eligibility(strategy_id)` | Prüft einzelne Strategie |
| `check_portfolio_live_eligibility(portfolio_id)` | Prüft Portfolio |
| `get_eligible_strategies()` | Listet alle eligible Strategien |
| `get_eligibility_summary()` | Übersicht aller Eligibilities |
| `assert_strategy_eligible(strategy_id)` | Wirft Exception bei Nicht-Eligibility |
| `assert_portfolio_eligible(portfolio_id)` | Wirft Exception bei Nicht-Eligibility |

#### Datenmodelle

```python
@dataclass
class LiveGateResult:
    entity_id: str
    entity_type: str  # "strategy" oder "portfolio"
    is_eligible: bool
    reasons: List[str]
    details: Dict[str, Any]
    tier: Optional[str]
    allow_live_flag: Optional[bool]

@dataclass
class LivePolicies:
    min_sharpe_core: float = 1.5
    min_sharpe_aux: float = 1.0
    max_maxdd_core: float = -0.15
    max_maxdd_aux: float = -0.20
    allow_legacy: bool = False
    require_allow_live_flag: bool = False
    require_diversification: bool = True
    max_concentration: float = 0.6
```

### 2. Config: `config/live_policies.toml`

```toml
[live_policy]
# Strategy Requirements
min_sharpe_core = 1.5
min_sharpe_aux = 1.0
max_maxdd_core = -0.15
max_maxdd_aux = -0.20

# Tiering Requirements
allow_legacy = false
require_allow_live_flag = false

# Portfolio Requirements
require_diversification = true
max_concentration = 0.60
```

---

## Eligibility-Kriterien

### Strategy-Eligibility

| Kriterium | Core | Aux | Legacy |
|-----------|------|-----|--------|
| Tier OK | ✅ | ✅ | ❌ |
| Min Sharpe | 1.5 | 1.0 | - |
| Max MaxDD | -15% | -20% | - |
| allow_live Flag | Optional* | Optional* | ❌ |

*`require_allow_live_flag` ist in Phase 83 noch `false`

### Portfolio-Eligibility

| Kriterium | Beschreibung |
|-----------|--------------|
| Alle Strategien eligible | Keine Legacy/Unclassified |
| Max Konzentration | ≤60% in einer Strategie |
| Min Strategien | ≥1 |

---

## Verwendung

### Strategie-Eligibility prüfen

```python
from src.live.live_gates import check_strategy_live_eligibility

result = check_strategy_live_eligibility("rsi_reversion")
print(result)
# Live Gate Check: rsi_reversion (strategy)
# Status: ✅ ELIGIBLE
# Tier: core
# allow_live: False
```

### Portfolio-Eligibility prüfen

```python
from src.live.live_gates import check_portfolio_live_eligibility

result = check_portfolio_live_eligibility(
    "my_portfolio",
    strategies=["rsi_reversion", "ma_crossover"],
    weights=[0.6, 0.4],
)
print(result.is_eligible)  # True
```

### Eligibility erzwingen (Exception bei Fehler)

```python
from src.live.live_gates import assert_strategy_eligible, assert_portfolio_eligible

# Wirft ValueError wenn nicht eligible
assert_strategy_eligible("rsi_reversion")
assert_portfolio_eligible("core_balanced")
```

### Eligibility-Übersicht

```python
from src.live.live_gates import get_eligibility_summary

summary = get_eligibility_summary()
print(f"Eligible: {summary['num_eligible']}")
print(f"Ineligible: {summary['num_ineligible']}")
print(f"Core eligible: {summary['by_tier']['core']['eligible']}")
```

### CLI-Integration (Beispiel)

```bash
# Vor Shadow/Testnet-Start
python3 -c "
from src.live.live_gates import assert_portfolio_eligible
assert_portfolio_eligible('core_balanced')
print('Portfolio is live-eligible')
"
```

---

## Integration mit anderen Phasen

### Phase 71-73 (Bestehendes Gating)

Phase 83 ergänzt das bestehende Gating:

```
Phase 71 Gates (Safety)          Phase 83 Gates (Eligibility)
├── enable_live_trading          ├── Tiering-Check
├── live_mode_armed              ├── Performance-Check
└── live_dry_run_mode            └── Diversifikation-Check
```

### Phase 80 (Tiered Presets)

Alle Phase-80 Presets sind automatisch live-eligible:
- `core_balanced` → ✅ Eligible
- `core_trend_meanreversion` → ✅ Eligible
- `core_plus_aux_aggro` → ✅ Eligible

### Phase 84 (Operator Dashboard)

Das Operator-Dashboard nutzt Live-Gates für:
- Eligibility-Status-Anzeige
- Warnungen bei nicht-eligible Strategien
- Pre-flight-Checks vor Runs

---

## Tests

```bash
# Alle Live-Gates Tests
python3 -m pytest tests/test_live_gates.py -v

# Nur positive Cases
python3 -m pytest tests/test_live_gates.py::TestStrategyEligibilityPositive -v

# Nur negative Cases
python3 -m pytest tests/test_live_gates.py::TestStrategyEligibilityNegative -v
```

### Testabdeckung

| Testklasse | Fokus |
|------------|-------|
| `TestLivePolicies` | Policy-Loading & Defaults |
| `TestStrategyEligibilityPositive` | Core/Aux eligible |
| `TestStrategyEligibilityNegative` | Legacy/Unknown blocked |
| `TestPortfolioEligibility` | Portfolio-Checks |
| `TestHelperFunctions` | Helper-Funktionen |
| `TestLiveGatesIntegration` | End-to-End-Workflows |

---

## Erweiterung für v1.1+

### Geplante Erweiterungen

1. **`require_allow_live_flag = true`**
   - Strategie muss explizit `allow_live=true` haben
   - Manueller Freigabe-Prozess

2. **Monte-Carlo p5 Percentile**
   - Zusätzliches Kriterium: MC p5 > 0
   - Integration mit StrategyProfile

3. **Regime-Robustheit**
   - Prüfung der Regime-Profile
   - Mindestanforderungen pro Regime

4. **Automatische Profile-Validierung**
   - Profile-Alter prüfen
   - Automatischer Re-Test bei veralteten Profilen

---

## Definition of Done

- [x] `src/live/live_gates.py` implementiert
- [x] `config/live_policies.toml` konfiguriert
- [x] Tests in `tests/test_live_gates.py` (27 Tests)
- [x] Dokumentation vorhanden
- [x] Integration mit Tiering-System

---

## Nächste Schritte

→ **Phase 84:** Operator-Dashboard nutzt Live-Gates
→ **Phase 85:** Drill-Skript nutzt Live-Gates vor Shadow-Start
