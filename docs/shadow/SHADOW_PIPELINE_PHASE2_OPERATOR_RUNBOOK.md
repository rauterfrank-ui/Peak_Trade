# Shadow Pipeline Phase 2 — Operator Runbook (Tick → OHLCV → Quality)

**Date:** 2025-12-27  
**Status:** Production-Ready (Shadow/Dev contexts only)  
**Owner:** Peak_Trade Ops Team

---

## Purpose

This runbook describes how to operate the Shadow Pipeline Phase 2 components that transform normalized ticks into OHLCV bars and produce data quality signals. Execution is blocked when live mode is active.

---

## Scope

**Inputs:** Normalized ticks (e.g., from the Kraken WebSocket adapter)

**Processing:**
- Tick normalization (upstream)
- OHLCV building / aggregation
- Quality monitoring (gap detection, spike alerts)

**Outputs:** OHLCV bars + quality events/flags + logs/metrics as implemented

This document focuses on how to run the provided smoke flow and how to interpret results.

---

## Preconditions

- You are in a local dev environment
- You have a Python environment with project dependencies installed
- You are on a non-live execution context (shadow components are blocked when live mode is active)

---

## Quick Operation Checklist

1. Pull latest `main`
2. Run the smoke script:
   - `python3 scripts&#47;shadow_run_tick_to_ohlcv_smoke.py`
3. Confirm:
   - Script exits with success
   - Expected OHLCV output is produced (console/log output)
   - Quality alerts behave as expected (if the script includes fixtures / synthetic anomalies)

---

## Smoke Script

### Command

```bash
python3 scripts/shadow_run_tick_to_ohlcv_smoke.py
```

### Expected Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎭 Shadow Pipeline Smoke Test: Tick→OHLCV + Quality
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Kraken Trade Messages (Beispiel)...
   ✅ 3 Beispiel-Messages erstellt

2️⃣  Tick Normalization...
   ✅ 4 Ticks normalisiert

3️⃣  OHLCV Building (1m)...
   ✅ 2 Bars erstellt

4️⃣  Quality Monitoring (Gaps + Spikes)...
   ✅ 1 Quality Events gefunden
      - GAP: WARN @ 1735347660000

5️⃣  Generating HTML Quality Report...
   ✅ Report written to: reports/shadow/quality/quality_report_20251227_153045.html

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Alle Smoke-Tests bestanden!
📊 Report: reports/shadow/quality/quality_report_20251227_153045.html
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Exit Codes

- **0** = Success (all smoke tests passed)
- **1** = Failure (one or more tests failed)

---

## Report Output

Each smoke run generates an HTML quality report.

### Location

```
reports/shadow/quality/quality_report_<timestamp>.html
```

**Example:**
```
reports/shadow/quality/quality_report_20251227_153045.html
```

### Contents

The report includes:
- Run metadata (timestamp, symbol, timeframe)
- Processing statistics (tick count, bar count)
- Quality events table with:
  - Event type (GAP, SPIKE)
  - Severity level (ERROR, WARN, INFO)
  - Timestamp
  - Details

### How to Open

**Local viewing:**
```bash
# macOS
open reports/shadow/quality/quality_report_<timestamp>.html

# Linux
xdg-open reports/shadow/quality/quality_report_<timestamp>.html

# Or use your browser directly
firefox reports/shadow/quality/quality_report_<timestamp>.html
```

The report is a standalone HTML file and requires no external dependencies or server.

### Convenience Files

In addition to the timestamped report, each successful run also updates:

**latest.html**
```
reports/shadow/quality/latest.html
```
Always points to the most recent smoke run result. Use this for quick access without needing to know the exact timestamp.

**index.html**
```
reports/shadow/quality/index.html
```
Lists the last 20 reports with links, newest first. Provides an overview of recent runs and easy navigation.

**Quick Access:**
```bash
# View latest report
open reports/shadow/quality/latest.html

# Browse all recent reports
open reports/shadow/quality/index.html
```

### Note

Report generation is skipped when the pipeline is blocked (e.g., when live mode is detected). In such cases, the script exits early and no report files are created or updated.

---

## Module Overview

| Module | Purpose |
|--------|---------|
| `src/data/shadow/_guards.py` | Safety Guards (Import, Runtime, Config) |
| `src/data/shadow/models.py` | Tick, Bar Dataclasses |
| `src/data/shadow/tick_normalizer.py` | Kraken WS Parser |
| `src/data/shadow/ohlcv_builder.py` | OHLCV Aggregation |
| `src/data/shadow/quality_monitor.py` | Gap/Spike Detection |
| `src/data/shadow/quality_report.py` | HTML Quality Report Generator |
| `src/data/shadow/jsonl_logger.py` | Rotating JSONL Logger |

---

## Safety & Guardrails

### Defense in Depth (3 Layers)

**1. Import Guard** — checks at module load time
```python
# In src/data/shadow/__init__.py
check_import_guard()  # Blocks if live mode env var is active
```

**2. Runtime Guard** — checks at runtime
```python
check_runtime_guard(cfg)  # Blocks if live mode config flag is active
```

**3. Config Guard** — checks pipeline activation
```python
check_config_guard(cfg)  # Blocks if shadow pipeline is not explicitly opted-in
```

### Environment

The shadow pipeline is blocked when the live mode environment variable is present. The import guard triggers immediately on import:

```python
>>> from src.data.shadow import Tick
# ShadowLiveForbidden: Live mode environment variable is active!
```

---

## Configuration

### Example Config

`config/shadow_pipeline_example.toml`:

```toml
[shadow.pipeline]
enabled = false  # SAFE DEFAULT (requires governance approval for activation)

[shadow.quality]
enabled = false  # Example; requires governance approval for activation
gap_severity = "WARN"
spike_severity = "WARN"
max_abs_log_return = 0.10  # 10% threshold
volume_spike_factor = 10.0

[shadow.logging]
enabled = false  # Example; requires governance approval for activation
path = "reports/shadow_quality_events.jsonl"
max_bytes = 1000000
backup_count = 5

[live]
enabled = false  # CRITICAL: Runtime guard enforced
```

---

## Running Tests

```bash
# All Shadow Pipeline Tests
python3 -m pytest tests/data/shadow/ -q

# Specific Tests
python3 -m pytest tests/data/shadow/test_guards.py -v
python3 -m pytest tests/data/shadow/test_tick_normalizer_kraken_trade.py -v
python3 -m pytest tests/data/shadow/test_ohlcv_builder.py -v
python3 -m pytest tests/data/shadow/test_quality_monitor.py -v
```

### Test Coverage

| Komponente | Tests | Fokus |
|------------|-------|-------|
| Guards | 5+ | Import/Runtime/Config Guards trigger correctly |
| Normalizer | 5+ | Parse Kraken Messages, Filter invalid, Sort |
| OHLCV | 5+ | Deterministic, OHLC correct, VWAP, Timeframes |
| Quality | 5+ | Gap Detection, Price/Volume Spikes |

---

## Troubleshooting

### Script Fails Immediately

**Symptom:** Smoke script exits with error before producing output

**Check:**
1. Are you in the correct Python environment?
   ```bash
   python3 --version  # Should be 3.9+
   which python3
   ```

2. Are dependencies installed?
   ```bash
   pip list | grep -E "(pandas|numpy)"
   ```

3. Is the live mode environment variable set?
   ```bash
   # This should be empty in dev contexts:
   echo $PEAK_TRADE_LIVE_MODE
   ```

### Guards Trigger Unexpectedly

**Symptom:** `ShadowLiveForbidden` exception

**Resolution:**
- The guards are working as designed
- Shadow components are not permitted when live mode is active
- Check environment and config settings
- Ensure you are in a dev/shadow context

### Quality Monitor Shows No Events

**Symptom:** Smoke test shows `0 Quality Events gefunden`

**Explanation:**
- This is expected if the synthetic data has no gaps or spikes
- Quality monitor is working correctly
- Real data pipelines may show more events

### OHLCV Output Unexpected

**Symptom:** Bar counts or values differ from expected

**Check:**
1. Tick normalization (Step 2):
   - Are all ticks valid?
   - Are they sorted by timestamp?

2. Timeframe alignment:
   - Bars are aligned to the start of each period
   - Partial bars at the end may be incomplete

---

## Developer Notes

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

cfg = {"shadow": {"quality": {"gap_severity": "WARN", ...}}}
monitor = DataQualityMonitor(cfg)
events = monitor.check_bars(bars)
# → List[QualityEvent]: GAP, SPIKE (price/volume)
```

---

## Quality Events

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

## Related Documentation

- **Technical Spec:** `docs/shadow/PHASE_2_TICK_TO_OHLCV_AND_QUALITY.md`
- **Quickstart:** `docs/shadow/SHADOW_PIPELINE_PHASE2_QUICKSTART.md`
- **Config Example:** `config/shadow_pipeline_example.toml`
- **Merge Log:** `docs/ops/merge_logs/2025-12-27_pr-394_shadow-phase2-tick-ohlcv-quality.md`

---

**Version:** 1.0  
**Last Updated:** 2025-12-27  
**Next Review:** After Phase 3 Implementation
