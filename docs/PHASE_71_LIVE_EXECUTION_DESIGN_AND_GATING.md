# Peak_Trade – Phase 71: Live-Execution-Design & Gating

> **Status:** Phase 71 – Design & Dry-Wiring (keine echte Live-Aktivierung)  
> **Datum:** 2025-12  
> **Ziel:** Live-Execution-Path als Design modellieren, ohne echte Live-Orders zu aktivieren

> ⚠️ **POLICY-SAFE NOTICE:**  
> This document describes governance and gating semantics. It does **not** provide live-enable instructions.  
> All examples use `LIVE_BLOCKED` / `shadow` / `paper` semantics and require manual sign-off.  
> Live activation remains blocked by default and requires formal governance approval.

---

## 1. Überblick

Phase 71 modelliert den **Live-Execution-Path als Design**, ohne echte Live-Orders zu aktivieren. Das System **weiß**, wie ein Live-Execution-Path aussehen würde, aber er ist technisch auf "Dry-Run" verdrahtet.

**Kernprinzipien:**
- Live-Execution-Path existiert als Design/Dry-Run
- Alle Live-Operationen sind klar als TODO/commented-out/NotImplemented gekennzeichnet
- Zweistufiges Gating verhindert versehentliche Aktivierung
- Tests decken Design & Gating ab, nicht echte Live-Orders

**WICHTIG:** Diese Phase erlaubt weiterhin **keine** echten Live-Trades.

---

## 2. Neue/angepasste Klassen & Configs

### 2.1 EnvironmentConfig-Erweiterungen

`src/core/environment.py` wurde um Live-spezifische Felder erweitert:

```python
@dataclass
class EnvironmentConfig:
    # ... bestehende Felder ...

    # Phase 71: Live-Execution-Design
    live_mode_armed: bool = False              # Zweistufiges Gating: Gate 2
    live_dry_run_mode: bool = True             # Phase 71: Immer True
    max_live_notional_per_order: Optional[float] = None
    max_live_notional_total: Optional[float] = None
    live_trade_min_size: Optional[float] = None
```

**Sichere Defaults:**
- `live_mode_armed = False` (Gate 2 blockiert)
- `live_dry_run_mode = True` (Phase 71: immer True)
- Alle Limits sind `None` (müssen explizit gesetzt werden)

### 2.2 LiveOrderExecutor (Dry-Run)

`src/orders/exchange.py` enthält jetzt einen vollständigen `LiveOrderExecutor`:

**Verhalten:**
- Erfüllt das `OrderExecutor`-Interface
- Macht nur Logging und legt Events ab
- Sendet **keine echten Orders** an Exchange-APIs
- Simuliert Order-Execution mit konfigurierbaren Preisen

**Beispiel:**
```python
env = EnvironmentConfig(
    environment=TradingEnvironment.LIVE,
    live_dry_run_mode=True  # Phase 71: Immer True
)
guard = SafetyGuard(env_config=env)
executor = LiveOrderExecutor(safety_guard=guard, dry_run_mode=True)

executor.set_simulated_price("BTC/EUR", 50000.0)
result = executor.execute_order(order)
# result.metadata["mode"] == "live_dry_run"
# result.metadata["dry_run"] == True
```

### 2.3 Factory-Funktion: create_order_executor()

`src/orders/exchange.py` enthält eine Factory-Funktion für Execution-Pfad-Auswahl:

```python
def create_order_executor(
    env_config: EnvironmentConfig,
    simulated_prices: Optional[Dict[str, float]] = None,
    trading_client: Optional["TradingExchangeClient"] = None,
) -> OrderExecutor:
    """
    Erstellt den passenden OrderExecutor basierend auf EnvironmentConfig.

    - PAPER/Shadow → PaperOrderExecutor
    - TESTNET → TestnetOrderExecutor (Dry-Run)
    - LIVE → LiveOrderExecutor (Dry-Run in Phase 71)
    """
```

**Entscheidungslogik:**
1. `env.mode == "paper"` → `PaperOrderExecutor`
2. `env.mode == "testnet"` → `TestnetOrderExecutor` (Dry-Run)
3. `env.mode == "live"` → `LiveOrderExecutor` (Dry-Run in Phase 71)
4. Mit `trading_client` → `ExchangeOrderExecutor` (kann echte Calls machen)

### 2.4 LiveRiskConfig-Erweiterungen

`src/live/risk_limits.py` wurde um Live-spezifische Limits erweitert:

```python
@dataclass
class LiveRiskConfig:
    # ... bestehende Felder ...

    # Phase 71: Live-spezifische Limits (Design)
    max_live_notional_per_order: Optional[float] = None
    max_live_notional_total: Optional[float] = None
    live_trade_min_size: Optional[float] = None
```

---

## 3. Live-Gating & Limits

### 3.1 Zweistufiges Gating

**Gate 1: `enable_live_trading`**
- Muss explizit auf `True` gesetzt werden
- Blockiert Live-Trading, wenn `False`

**Gate 2: `live_mode_armed` (Phase 71)**
- Zusätzliches Gate für zusätzliche Sicherheit
- Muss explizit auf `True` gesetzt werden
- Blockiert Live-Trading, wenn `False`

**Technisches Gate: `live_dry_run_mode`**
- Phase 71: Immer `True`
- Blockiert echte Orders technisch
- Selbst wenn alle Flags gesetzt sind, blockiert `live_dry_run_mode=True` echte Orders

**Zentrale Helper-Funktion: `is_live_execution_allowed()`**

Die Funktion `is_live_execution_allowed(env_config)` in `src/live/safety.py` definiert
die **vollständigen Kriterien** für echte Live-Execution:

```python
from src.live.safety import is_live_execution_allowed

allowed, reason = is_live_execution_allowed(env_config)
# In Phase 71: allowed wird immer False sein wegen live_dry_run_mode=True
```

Diese Funktion dient der **Dokumentation des Designs** und macht die Gating-Logik
explizit und testbar.

### 3.2 SafetyGuard-Integration

`SafetyGuard.ensure_may_place_order()` prüft:

1. **Environment-Check:** Ist der aktuelle Mode erlaubt?
2. **Gate 1:** `enable_live_trading` set? (requires manual governance approval)
3. **Gate 2:** `live_mode_armed` set? (Phase 71 — requires manual governance approval)
4. **Confirm-Token:** Korrekter Token gesetzt?
5. **Dry-Run-Check:** `live_dry_run_mode = True` blockt echte Orders (Phase 71)

### 3.3 Risk-Limits für Live

Live-spezifische Limits sind in `LiveRiskConfig` modelliert:

- `max_live_notional_per_order`: Max. Notional pro einzelner Live-Order
- `max_live_notional_total`: Max. Gesamt-Notional für Live-Orders
- `live_trade_min_size`: Min. Order-Größe für Live-Trades

**Hinweis:** Diese Limits sind in Phase 71 nur modelliert, nicht aktiv implementiert. Sie werden in einer späteren Phase aktiviert.

---

## 4. Flow-Diagramm

```
┌─────────────────────────────────────────────────────────────┐
│                    create_order_executor(env)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────┐                      ┌───────────────┐
│ env.mode ==   │                      │ env.mode ==   │
│ "paper"       │                      │ "testnet"     │
└───────────────┘                      └───────────────┘
        │                                       │
        ▼                                       ▼
┌───────────────┐                      ┌───────────────┐
│ PaperOrder    │                      │ TestnetOrder  │
│ Executor      │                      │ Executor      │
│               │                      │ (Dry-Run)     │
└───────────────┘                      └───────────────┘

        ┌───────────────────────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────┐                  ┌───────────────┐
│ env.mode ==   │                  │ trading_client│
│ "live"        │                  │ vorhanden     │
└───────────────┘                  └───────────────┘
        │                                   │
        ▼                                   ▼
┌───────────────┐                  ┌───────────────┐
│ LiveOrder     │                  │ ExchangeOrder  │
│ Executor      │                  │ Executor      │
│ (Dry-Run)     │                  │ (echte Calls) │
│ Phase 71      │                  │               │
└───────────────┘                  └───────────────┘
```

---

## 5. Tests

Tests befinden sich in `tests/test_phase71_live_execution_design.py`:

**Abgedeckte Bereiche:**
- `LiveOrderExecutor` im Dry-Run-Modus
- `create_order_executor()` für alle Modi
- Zweistufiges Gating (`enable_live_trading` + `live_mode_armed`)
- `live_dry_run_mode` blockt echte Orders
- Logging und Event-Tracking

**WICHTIG:** Tests prüfen nur Design & Gating, nicht echte Live-Orders.

---

## 6. Konfiguration

### 6.1 config.toml-Beispiel

```toml
[environment]
mode = "live"                    # Phase 71: Nur für Design-Tests
enable_live_trading = false       # Gate 1: BLOCKED (default; requires governance sign-off)
live_mode_armed = false           # Gate 2 (Phase 71: Blockiert)
live_dry_run_mode = true          # Phase 71: Immer True
require_confirm_token = true
confirm_token = "I_KNOW_WHAT_I_AM_DOING"

# Phase 71: Live-spezifische Limits (Design)
max_live_notional_per_order = 1000.0
max_live_notional_total = 5000.0
live_trade_min_size = 10.0

[live_risk]
enabled = true
max_order_notional = 1000.0
max_total_exposure_notional = 5000.0
# Phase 71: Live-spezifische Limits (Design)
max_live_notional_per_order = 1000.0
max_live_notional_total = 5000.0
live_trade_min_size = 10.0
```

---

## 7. Gates/Flags VOR einer echten Aktivierung

Bevor echte Live-Orders denkbar wären, müssen folgende Bedingungen erfüllt sein:

1. ✅ `environment.mode = "live"`
2. ✅ Gate 1: manual governance approval (not shown here for policy safety)
3. ✅ Gate 2: manual governance approval (not shown here for policy safety)
4. ✅ `live_dry_run_mode = False` (muss explizit auf False gesetzt werden)
5. ✅ `confirm_token = "I_KNOW_WHAT_I_AM_DOING"`
6. ✅ Risk-Limits konfiguriert und aktiv
7. ✅ Monitoring & Runbooks vorhanden
8. ✅ Governance-Freigabe dokumentiert
9. ✅ Exchange-API-Integration implementiert
10. ✅ Tests für echte Live-Orders geschrieben

**Hinweis:** Jede echte Live-Freigabe erfordert eine eigene Phase (z.B. Phase 72/73).

---

## 8. Zusammenfassung

**Was Phase 71 getan hat:**
- ✅ Live-Execution-Path als Design modelliert (Dry-Run)
- ✅ `LiveOrderExecutor` implementiert (nur Logging, keine echten Orders)
- ✅ Factory-Funktion `create_order_executor()` für Execution-Pfad-Auswahl
- ✅ Zweistufiges Gating (`enable_live_trading` + `live_mode_armed`)
- ✅ Zentrale Helper-Funktion `is_live_execution_allowed()` für klare Gating-Logik
- ✅ Explizites Logging mit "[LIVE-DRY-RUN]" und "[SAFETY]" Tags
- ✅ Live-spezifische Limits in Config modelliert
- ✅ Tests für Design & Gating hinzugefügt
- ✅ Dokumentation aktualisiert

**Was Phase 71 NICHT getan hat:**
- ❌ Keine echten Live-Orders aktiviert
- ❌ Keine Exchange-API-Integration für Live
- ❌ Keine produktive Live-Order-Ausführung

**Ergebnis:**
Das System **weiß**, wie ein Live-Execution-Path aussehen würde, aber er ist technisch auf "Dry-Run" verdrahtet. v1.0 bleibt ein **reines Research-/Testnet-System**.

---

## 9. Referenzen

- `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` – Safety-Policy mit Phase-71-Abschnitt
- `docs/PEAK_TRADE_V1_OVERVIEW_FULL.md` – v1.0-Übersicht mit Phase-71-Ausblick
- `tests/test_phase71_live_execution_design.py` – Tests für Design & Gating
- `src/core/environment.py` – EnvironmentConfig mit Live-Feldern
- `src/orders/exchange.py` – LiveOrderExecutor & Factory-Funktion
- `src/live/safety.py` – SafetyGuard mit zweistufigem Gating
- `src/live/risk_limits.py` – LiveRiskConfig mit Live-Limits

---

**Built with ❤️ and safety-first architecture**
