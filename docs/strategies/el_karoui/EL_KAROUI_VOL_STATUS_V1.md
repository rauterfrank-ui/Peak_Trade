# ✅ R&D-Strategie: El Karoui Volatility Strategy – Status v1

| Aspekt | Details |
|--------|---------|
| **Modulpfad** | `src/strategies/el_karoui/` |
| **Klassen** | `VolRegime`, `ElKarouiVolConfig`, `ElKarouiVolModel` (`vol_model.py`), `ElKarouiVolatilityStrategy` (`el_karoui_vol_model_strategy.py`) |
| **Kategorie** | `volatility` |
| **Tier** | `r_and_d` (rein Research/Backtests, keine Live-Freigabe) |
| **Registry-Key** | `el_karoui_vol_model` |

---

## Funktionale Idee

- Modelliert Volatilitäts-Regimes basierend auf stochastischen Volatilitätsmodellen (inspiriert von Nicole El Karoui)
- Regime: `LOW`, `MEDIUM`, `HIGH` (basierend auf rollendem Perzentil der realisierten Volatilität)
- Übersetzt aktives Regime in Positions-Entscheidungen via Regime→Position-Maps:
  - **Default**: LOW→long, MEDIUM→long, HIGH→flat
  - **Conservative**: nur LOW→long, sonst flat
  - **Aggressive**: alle Regimes→long (mit Vol-Scaling)
- Optional: Vol-Target-Scaling für Position-Sizing (target_vol / current_vol)

---

## Kernkomponenten

### `vol_model.py`

| Klasse/Enum | Beschreibung |
|-------------|--------------|
| `VolRegime` | Enum mit `LOW`, `MEDIUM`, `HIGH` für Vol-Regime-Klassifikation |
| `ElKarouiVolConfig` | Dataclass für Modell-Parameter (vol_window, thresholds, vol_target, regime_multipliers) |
| `ElKarouiVolModel` | Hauptmodell für Vol-Schätzung, Regime-Klassifikation und Scaling |

**Wichtige Methoden:**
- `calculate_realized_vol(returns)` → Realized Vol (EWM/rolling)
- `calculate_vol_percentile(vol_series)` → Perzentil-Position
- `regime_for_returns(returns)` → Aktuelles Vol-Regime
- `scaling_factor_for_returns(returns)` → Kombinierter Scaling-Faktor
- `get_vol_analysis(returns)` → Umfassende Analyse-Dict

### `el_karoui_vol_model_strategy.py`

| Klasse | Beschreibung |
|--------|--------------|
| `ElKarouiVolatilityStrategy` | Hauptstrategie mit Signal-Generierung basierend auf Vol-Regime |
| `ElKarouiVolModelStrategy` | Alias für Backwards Compatibility |

**Wichtige Methoden:**
- `generate_signals(data)` → Signal-Series (0/1) basierend auf Vol-Regime
- `get_vol_analysis(data)` → Detaillierte Vol-Analyse
- `get_current_regime(data)` → Aktuelles Vol-Regime
- `get_position_for_regime(regime)` → Position für gegebenes Regime
- `get_strategy_info()` → Strategy-Metadaten inkl. Tier

**Klassen-Flags:**
- `KEY = "el_karoui_vol_v1"`
- `IS_LIVE_READY = False`
- `ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]`
- `TIER = "r_and_d"`

---

## Safety / Gating

- R&D-Tier wird in `src/live/live_gates.py` explizit geprüft
- Exception: `RnDLiveTradingBlockedError`
- **Blockierte Modi**: `live`, `paper`, `testnet`, `shadow` → Exception
- **Erlaubte Modi**: `offline_backtest`, `research` → OK

**Gating-Funktionen:**
- `check_r_and_d_tier_for_mode("el_karoui_vol_model", mode)` → `True` wenn blockiert
- `assert_strategy_not_r_and_d_for_live("el_karoui_vol_model", mode)` → wirft Exception bei Blockierung
- `get_strategy_tier("el_karoui_vol_model")` → `"r_and_d"`
- `check_strategy_live_eligibility("el_karoui_vol_model")` → `LiveGateResult(is_eligible=False, ...)`

---

## Tests (90 Tests gesamt)

| Testdatei | Tests | Beschreibung |
|-----------|-------|--------------|
| `tests/strategies/el_karoui/test_vol_model.py` | 40 | VolRegime-Enum, ElKarouiVolConfig-Validierung, Vol-Berechnung, Perzentil-Ranking, Regime-Klassifikation, Scaling-Faktoren, Convenience-Funktionen |
| `tests/strategies/el_karoui/test_el_karoui_volatility_strategy.py` | 50 | Instanziierung, Config-Override, R&D-Safety-Flags, Regime-Position-Mappings, Signal-Generierung, Metadaten, Helper-Methoden, Tier-Gating, Exception-Tests, Smoke-Tests |

**Abdeckung:**
- ✅ Modell-Logik (Vol-Schätzung, Perzentile, Regime-Bestimmung)
- ✅ Strategy-Signal-Generierung
- ✅ Regime→Position-Mapping (Default, Conservative, Aggressive)
- ✅ R&D-Tier-Gating (alle blockierten Modi)
- ✅ Exception-Handling (RnDLiveTradingBlockedError)
- ✅ Smoke-Tests (End-to-End Backtest-Workflow)

---

## Registrierung

| Datei | Eintrag |
|-------|---------|
| `src/strategies/__init__.py` | `"el_karoui_vol_model": "el_karoui.el_karoui_vol_model_strategy"` |
| `src/strategies/registry.py` | `_STRATEGY_REGISTRY["el_karoui_vol_model"]` mit `ElKarouiVolModelStrategy` |
| `config/strategy_tiering.toml` | `[strategy.el_karoui_vol_model]` mit `tier = "r_and_d"`, `category = "volatility"` |

**Tiering-Config (Auszug):**
```toml
[strategy.el_karoui_vol_model]
tier = "r_and_d"
label = "El Karoui Volatility Model"
category = "volatility"
risk_profile = "experimental"
owner = "research"
tags = ["volatility", "stochastic-vol", "risk-model", "options"]
recommended_config_id = "el_karoui_vol_v0_research"
allow_live = false
```

---

## Wichtige Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `vol_window` | 20 | Fenster für Volatilitätsschätzung (Tage) |
| `lookback_window` | 252 | Fenster für Perzentil-Berechnung (Tage) |
| `low_threshold` | 0.30 | Perzentil-Schwelle für LOW-Regime |
| `high_threshold` | 0.70 | Perzentil-Schwelle für HIGH-Regime |
| `vol_target` | 0.10 | Ziel-Volatilität p.a. (10%) für Scaling |
| `use_ewm` | True | Exponentiell gewichtete Vol-Schätzung |
| `use_vol_scaling` | True | Aktiviert Vol-Target-Scaling |
| `annualization_factor` | 252.0 | Faktor für Annualisierung |

**Regime-Multipliers (Default):**
- LOW: 1.0 (volles Exposure)
- MEDIUM: 0.75 (reduziert)
- HIGH: 0.50 (stark reduziert)

---

## Verwandte Dokumente

- [R&D-Playbook Armstrong & El Karoui](../../runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md)
- [Armstrong Cycle Strategy Status](../armstrong/ARMSTRONG_CYCLE_STATUS_V1.md)
