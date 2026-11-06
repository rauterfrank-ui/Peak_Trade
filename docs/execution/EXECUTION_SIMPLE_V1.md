# Simplified Execution Pipeline v1 – Learning Module

> **Vereinfachte Order-Execution für Learning & Demos**

---

## Überblick

Das **Simplified Execution Pipeline** Module (`src/execution_simple/`) ist eine eigenständige, vereinfachte Execution-Implementierung für **Learning, Prototyping und Demos**.

**Wichtig:** Für **Production** nutze das vollständige Module: `src/execution/` (Phase 16A V2 - Governance-aware)

### Warum zwei Module?

- `src/execution/` – **Production**: Vollständiges System mit Governance, LiveRiskLimits, Shadow/Testnet-Integration
- `src/execution_simple/` – **Learning**: Einfaches Gate-System, klar verständlich, minimal Dependencies

**Use Cases für execution_simple:**
- ✅ Execution-Konzepte lernen
- ✅ Schnelle Prototypen
- ✅ Demos in Dokumentation
- ✅ Teaching Material

---

## Architektur

### Pipeline Flow

```text
Target Position + Current Position
         │
         ▼
┌─────────────────┐
│ Compute Delta   │  delta = target - current
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create Intent   │  OrderIntent(symbol, side, qty, price)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      GATE SYSTEM                 │
│  1. PriceSanity                 │  ← price > 0, not NaN
│  2. ResearchOnly                │  ← block research_only in LIVE
│  3. LotSize                     │  ← round to lot_size
│  4. MinNotional                 │  ← check min order size
└────────┬────────────────────────┘
         │
    Blocked? ──→ Return (blocked=True)
         │
         ▼
┌─────────────────┐
│ Create Order    │  Order(validated)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Execute         │  SimulatedBrokerAdapter
│ (if adapter)    │  → Fill (with slippage/fees)
└────────┬────────┘
         │
         ▼
   ExecutionResult
```

---

## Quick Start

### Installation

Module ist bereits im Repo:

```bash
# Keine extra installation nötig
python3 -c "from src.execution_simple import ExecutionPipeline; print('✅ Ready')"
```

### Demo ausführen

```bash
# Basic Demo (Paper Mode)
python3 scripts/run_execution_simple_dry_run.py \
  --symbol BTC-USD \
  --target 0.5 \
  --current 0.1 \
  --price 100000

# Research Code in LIVE (wird geblockt!)
python3 scripts/run_execution_simple_dry_run.py \
  --symbol BTC-USD \
  --target 0.5 \
  --current 0.0 \
  --price 100000 \
  --mode live \
  --tags research_only
```

**Output:**
```
======================================================================
🚀 SIMPLIFIED EXECUTION PIPELINE DRY-RUN
======================================================================

📊 INPUT:
  Symbol:           BTC-USD
  Mode:             paper
  Price:            $100,000.00
  Target Position:  0.500000
  Current Position: 0.100000
  Desired Delta:    0.400000

⚙️  EXECUTION:

🔒 GATE DECISIONS:
  PriceSanity          ✅ PASS     Price valid
  ResearchOnly         ✅ PASS     Mode paper allows research code
  LotSize              ✅ PASS     Rounded 0.400000 → 0.400000
  MinNotional          ✅ PASS     Notional $40000.00 >= min $10.00

✅ EXECUTION ALLOWED

📝 PLANNED ORDERS:
  Order 1:
    Side:     BUY
    Quantity: 0.400000
    Price:    $100,000.00
    Notional: $40,000.00

💰 SIMULATED FILLS:
  Fill 1:
    Quantity: 0.400000
    Price:    $100,020.00 (incl. slippage)
    Fee:      $0.0000

✅ DRY-RUN COMPLETE
```

---

## Programmatic Usage

```python
from datetime import datetime
from src.execution_simple import (
    ExecutionContext,
    ExecutionMode,
    ExecutionPipeline,
    PriceSanityGate,
    ResearchOnlyGate,
    LotSizeGate,
    MinNotionalGate,
    SimulatedBrokerAdapter,
)

# 1. Build Pipeline
gates = [
    PriceSanityGate(),
    ResearchOnlyGate(block_research_in_live=True),
    LotSizeGate(lot_size=0.0001, min_qty=0.0001),
    MinNotionalGate(min_notional=10.0),
]

adapter = SimulatedBrokerAdapter(slippage_bps=2.0, fee_bps=10.0)
pipeline = ExecutionPipeline(gates=gates, adapter=adapter)

# 2. Create Context
context = ExecutionContext(
    mode=ExecutionMode.PAPER,
    ts=datetime.now(),
    symbol="BTC-USD",
    price=100000.0,
    tags=set(),  # or {"research_only"} for R&D code
)

# 3. Execute
result = pipeline.execute(
    target_position=1.0,   # Target: 1.0 BTC
    current_position=0.0,  # Current: 0 BTC
    context=context,
)

# 4. Check Result
if result.success:
    print(f"✅ Orders: {len(result.orders)}")
    print(f"💰 Fills: {len(result.fills)}")
    print(f"📊 Total: ${result.total_notional:,.2f}")
else:
    print(f"❌ Blocked: {result.block_reason}")
```

---

## Config (TOML)

```toml
[execution]
mode = "paper"              # backtest | paper | live
slippage_bps = 2.0          # 0.02% Slippage (nur simulated)
fee_bps = 10.0              # 0.1% Fee
min_notional = 10.0         # $10 Minimum
lot_size = 0.0001           # 0.0001 BTC Rounding
min_qty = 0.0001            # Absolute Min

[execution.gates]
block_research_in_live = true  # Safety!
```

**Config Builder:**

```python
from src.core.peak_config import load_config
from src.execution_simple import build_execution_pipeline_from_config

cfg = load_config("config/config.toml")
pipeline = build_execution_pipeline_from_config(cfg)
```

---

## Gate System

### Gate-Reihenfolge (wichtig!)

1. **PriceSanity** – Validiert Preis (> 0, not NaN)
2. **ResearchOnly** – Blockt R&D-Code in LIVE
3. **LotSize** – Rundet auf Exchange-Lot-Size
4. **MinNotional** – Prüft Mindestordergröße

**Warum diese Reihenfolge?**
- Preis muss gültig sein (alle Gates nutzen ihn)
- Research-Block ist Safety-kritisch
- Lot-Rounding BEFORE Notional-Check (gerundete Qty relevant)

### ResearchOnly Gate (Safety-Feature)

```python
# R&D-Code taggen
context = ExecutionContext(
    mode=ExecutionMode.LIVE,
    symbol="BTC-USD",
    price=100000.0,
    tags={"research_only"},  # ← Tag als Research
)

result = pipeline.execute(1.0, 0.0, context)
# ❌ Blocked: "Research code blocked in LIVE mode (safety)"
```

**Standardmäßig aktiviert!** (`block_research_in_live = true`)

### LotSize Gate (Rounding)

```python
# lot_size = 0.1, qty = 0.75
# → rounds to 0.7 (floor-based)

# lot_size = 0.1, qty = 0.05
# → rounds to 0.0 → blocked (below min_qty)
```

**Floating-Point-Fix:** Nutzt `+ 1e-9` epsilon um 0.6/0.1=5.999 → 6.0 zu vermeiden.

---

## Simulated Adapter

### Slippage-Berechnung

```python
# BUY: zahlt mehr (positive slippage)
fill_price = price * (1 + slippage_bps/10000)

# SELL: bekommt weniger (negative slippage)
fill_price = price * (1 - slippage_bps/10000)
```

**Beispiel:** `slippage_bps=10` (0.1%)
- BUY @ $100,000 → Fill @ $100,100
- SELL @ $100,000 → Fill @ $99,900

### Fee-Berechnung

```python
fee = notional * (fee_bps / 10000)
```

**Beispiel:** `fee_bps=10` (0.1%), notional=$40,000
- Fee = $40,000 * 0.001 = $40

---

## Testing

```bash
# Unit Tests
python3 -m pytest tests/execution_simple/test_execution_pipeline.py -v

# Specific Test
python3 -m pytest tests/execution_simple/test_execution_pipeline.py::test_blocks_research_only_in_live -v

# With Coverage
python3 -m pytest tests/execution_simple/ --cov=src.execution_simple --cov-report=term-missing
```

**Test Coverage:**
- ✅ All gates (PriceSanity, ResearchOnly, LotSize, MinNotional)
- ✅ Slippage calculation (BUY vs SELL)
- ✅ Pipeline orchestration
- ✅ Config builder
- ✅ E2E scenarios

---

## Unterschied zu src/execution/

| Feature | execution_simple | execution (Production) |
|---------|------------------|------------------------|
| **Zielgruppe** | Learning, Demos | Production Trading |
| **Gates** | 4 Basic Gates | Governance-integrated, SafetyGuard |
| **Broker** | Simulated only | Paper, Shadow, Testnet, (Future: Live) |
| **Dependencies** | Minimal | LiveRiskLimits, Governance, SafetyGuard |
| **Complexity** | ~500 LOC | ~1300 LOC |
| **Use Case** | Prototypes, Learning | Live Trading, Testnet |

---

## Nächste Schritte

### Für Learning:
1. Run Demo-Script (siehe Quick Start)
2. Lese Tests: `tests/execution_simple/test_execution_pipeline.py`
3. Experimentiere mit Gate-Reihenfolge
4. Füge eigene Gates hinzu

### Für Production:
1. Migiere zu `src/execution/` (vollständiges System)
2. Integriere mit LiveSessionRunner (Phase 80)
3. Nutze Governance-Integration
4. Aktiviere Real-Broker-Adapters

---

## Weiterführende Dokumentation

- [src/execution/ (Production)](../../src/execution/pipeline.py) – Vollständiges System
- [PEAK_TRADE_OVERVIEW.md](../PEAK_TRADE_OVERVIEW.md) – Gesamtarchitektur
- [BACKTEST_ENGINE.md](../BACKTEST_ENGINE.md) – Backtest-Integration

---

**Status:** ✅ Learning Module Complete  
**Production Module:** `src/execution/` (Phase 16A V2 - Governance-aware)
