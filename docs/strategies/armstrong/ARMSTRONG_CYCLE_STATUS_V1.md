# ✅ R&D-Strategie: Armstrong Cycle Strategy – Status v1

| Aspekt | Details |
|--------|---------|
| **Modulpfad** | `src/strategies/armstrong/` |
| **Klassen** | `ArmstrongPhase`, `ArmstrongCycleConfig`, `ArmstrongCycleModel` (`cycle_model.py`), `ArmstrongCycleStrategy` (`armstrong_cycle_strategy.py`) |
| **Kategorie** | `cycles` |
| **Tier** | `r_and_d` (rein Research/Backtests, keine Live-Freigabe) |
| **Registry-Key** | `armstrong_cycle` |

---

## Funktionale Idee

- Modelliert Armstrong-Zyklen über ein konfigurierbares Cycle-Modell (8.6-Jahres-Zyklus = 3141 Tage)
- Phasen: `CRISIS`, `PRE_CRISIS`, `POST_CRISIS`, `EXPANSION`, `CONTRACTION`
- Übersetzt aktive Phase in Positions-Entscheidungen via Phase→Position-Maps:
  - **Default**: EXPANSION→long, CRISIS→flat
  - **Conservative**: nur EXPANSION→long
  - **Aggressive**: CRISIS→short

---

## Safety / Gating

- R&D-Tier wird in `src/live/live_gates.py` explizit geprüft
- Neue Exception: `RnDLiveTradingBlockedError`
- **Blockierte Modi**: `live`, `paper`, `testnet`, `shadow` → Exception
- **Erlaubte Modi**: `offline_backtest`, `research` → OK

---

## Tests (74 Tests gesamt)

- `tests/strategies/armstrong/test_cycle_model.py` – 26 Tests
- `tests/strategies/armstrong/test_armstrong_cycle_strategy.py` – 48 Tests
- Abdeckung: Cycle-Logik, Phasen-Bestimmung, Risk-Multiplikatoren, Signal-Generierung, R&D-Tier-Gating, Smoke-Tests

---

## Registrierung

- ✅ `src/strategies/registry.py` – `_STRATEGY_REGISTRY["armstrong_cycle"]`
- ✅ `src/strategies/__init__.py` – `STRATEGY_REGISTRY["armstrong_cycle"]`
- ✅ `config/strategy_tiering.toml` – `tier = "r_and_d"`, `category = "cycles"`

---

## Verwandte Dokumente

- [R&D-Playbook Armstrong & El Karoui](../../runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md)
- [Peak_Trade V1 Overview](../../PEAK_TRADE_V1_OVERVIEW_FULL.md) – Abschnitt "R&D-Strategie-Welle v1"
