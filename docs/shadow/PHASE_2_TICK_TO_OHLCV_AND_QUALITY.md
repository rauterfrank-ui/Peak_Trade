# Shadow Trading Phase 2: Tick→OHLCV + Quality Monitor

**Date:** 2025-12-27  
**Status:** ✅ Implemented  
**Owner:** Peak_Trade Ops Team

---

## 🎯 Ziel

Phase 2 baut die Data Pipeline für Shadow Trading:

1. **Tick Normalization** — Kraken WebSocket Trade Messages → standardisierte Ticks
2. **OHLCV Building** — Tick Aggregation zu Bars (1m/5m/1h)
3. **Data Quality Monitoring** — Gap Detection, Spike Alerts

**KRITISCH:** NIEMALS im Live-Mode laufen lassen. Defense in Depth via Config, Runtime und Import Guards.

---

## 🏗️ Architektur

```
Kraken WS Trade Messages
         ↓
  Tick Normalizer (parse_kraken_trade_message)
         ↓
    Tick[] (sorted by ts_ms)
         ↓
  OHLCV Builder (OHLCVBuilder)
         ↓
    Bar[] (OHLCV + VWAP)
         ↓
  Quality Monitor (DataQualityMonitor)
         ↓
    QualityEvent[] (Gaps, Spikes) → JSONL Log
```

### Module

| Modul | Zweck |
|-------|-------|
| `src/data/shadow/_guards.py` | Safety Guards (Import, Runtime, Config) |
| `src/data/shadow/models.py` | Tick, Bar Dataclasses |
| `src/data/shadow/tick_normalizer.py` | Kraken WS Parser |
| `src/data/shadow/ohlcv_builder.py` | OHLCV Aggregation |
| `src/data/shadow/quality_monitor.py` | Gap/Spike Detection |
| `src/data/shadow/jsonl_logger.py` | Rotating JSONL Logger |

---

## 🔐 Sicherheitsprinzipien (NEVER LIVE)

### Defense in Depth (3 Ebenen)

**1. Import Guard** — prüft bei Modul-Load
```python
# In src/data/shadow/__init__.py
check_import_guard()  # Blockiert wenn PEAK_TRADE_LIVE_MODE=1
```

**2. Runtime Guard** — prüft zur Laufzeit
```python
check_runtime_guard(cfg)  # Blockiert wenn live.enabled=true
```

**3. Config Guard** — prüft Pipeline-Aktivierung
```python
check_config_guard(cfg)  # Blockiert wenn shadow.pipeline.enabled != true
```

### Environment Variable

```bash
# NIEMALS setzen:
export PEAK_TRADE_LIVE_MODE=1

# Import Guard triggert sofort beim Import:
# >>> from src.data.shadow import Tick
# ShadowLiveForbidden: PEAK_TRADE_LIVE_MODE ist aktiv!
```

---

## 📝 Config Example

`config/shadow_pipeline_example.toml`:

```toml
[shadow.pipeline]
enabled = false  # SAFE DEFAULT

[shadow.quality]
enabled = true
gap_severity = "WARN"
spike_severity = "WARN"
max_abs_log_return = 0.10  # 10% threshold
volume_spike_factor = 10.0

[shadow.logging]
enabled = true
path = "reports/shadow_quality_events.jsonl"
max_bytes = 1000000
backup_count = 5

[live]
enabled = false  # KRITISCH: NIEMALS true wenn shadow.pipeline.enabled
```

---

## 🚀 Smoke Test ausführen

```bash
# Offline Smoke Test (< 1s)
python3 scripts/shadow_run_tick_to_ohlcv_smoke.py

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎭 Shadow Pipeline Smoke Test: Tick→OHLCV + Quality
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 1️⃣  Kraken Trade Messages (Beispiel)...
#    ✅ 3 Beispiel-Messages erstellt
#
# 2️⃣  Tick Normalization...
#    ✅ 4 Ticks normalisiert
#
# 3️⃣  OHLCV Building (1m)...
#    ✅ 2 Bars erstellt
#
# 4️⃣  Quality Monitoring (Gaps + Spikes)...
#    ✅ 1 Quality Events gefunden
#       - GAP: WARN @ 1735347660000
#
# ✅ Alle Smoke-Tests bestanden!
```

---

## 🧪 Tests

```bash
# Alle Shadow Pipeline Tests
pytest -q tests/data/shadow/

# Spezifische Tests
pytest tests/data/shadow/test_guards.py -v
pytest tests/data/shadow/test_tick_normalizer_kraken_trade.py -v
pytest tests/data/shadow/test_ohlcv_builder.py -v
pytest tests/data/shadow/test_quality_monitor.py -v
```

### Test-Coverage

| Komponente | Tests | Fokus |
|------------|-------|-------|
| Guards | 5+ | Import/Runtime/Config Guards triggern korrekt |
| Normalizer | 5+ | Parse Kraken Messages, Filter invalid, Sort |
| OHLCV | 5+ | Deterministisch, OHLC korrekt, VWAP, Timeframes |
| Quality | 5+ | Gap Detection, Price/Volume Spikes |

---

## 🔧 Developer Guide

### Tick Normalization

```python
from src.data.shadow.tick_normalizer import normalize_ticks_from_messages

# Kraken WS Messages
messages = [
    [channelID, [[price, volume, time, side, type, misc], ...], "trade", "XBT/EUR"],
    ...
]

# Parse + Normalize
ticks = normalize_ticks_from_messages(messages)
# → List[Tick], sorted by ts_ms, invalid filtered
```

### OHLCV Building

```python
from src.data.shadow.ohlcv_builder import OHLCVBuilder

builder = OHLCVBuilder(symbol="XBT/EUR", timeframe="1m")
builder.add_ticks(ticks)
bars = builder.finalize()  # → List[Bar], sorted by start_ts_ms
```

### Quality Monitoring

```python
from src.data.shadow.quality_monitor import DataQualityMonitor

cfg = {"shadow": {"quality": {"enabled": True, ...}}}
monitor = DataQualityMonitor(cfg)
events = monitor.check_bars(bars)
# → List[QualityEvent]: GAP, SPIKE (price/volume)
```

---

## 📊 Quality Events

### Gap Event

```json
{
  "kind": "GAP",
  "severity": "WARN",
  "ts_ms": 1735347660000,
  "symbol": "XBT/EUR",
  "timeframe": "1m",
  "details": {
    "expected_next_start_ms": 1735347720000,
    "actual_next_start_ms": 1735347780000,
    "missing_bars": 1
  }
}
```

### Spike Event (Price)

```json
{
  "kind": "SPIKE",
  "severity": "WARN",
  "ts_ms": 1735347780000,
  "symbol": "XBT/EUR",
  "timeframe": "1m",
  "details": {
    "type": "price_spike",
    "abs_log_return": 0.15,
    "threshold": 0.10,
    "prev_close": 50000.0,
    "curr_close": 58000.0
  }
}
```

---

## 🔮 Next Steps (Phase 3)

1. **Signal Processing** — Strategy Execution im Shadow-Mode
2. **Backtest Matcher** — Vergleich Shadow-Signals vs. Backtest-Signals
3. **Validation Reports** — Signal Quality Metrics

---

## 📚 Verwandte Dokumentation

- Peak_Trade Tooling & Evidence Chain Runbook: `Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md`
- Ops Operator Center: `docs/ops/OPS_OPERATOR_CENTER.md`

---

**Version:** 2.0  
**Last Updated:** 2025-12-27  
**Next Review:** After Phase 3 Implementation
