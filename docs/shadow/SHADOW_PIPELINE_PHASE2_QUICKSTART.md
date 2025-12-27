# Shadow Pipeline Phase 2 — Quickstart

**5-Minute Quick Start für Shadow Tick→OHLCV→Quality**

---

## Prerequisites

- Python 3.9+ with Peak_Trade dependencies installed
- Local dev environment (shadow components are blocked in live mode)

---

## Quick Start (30 seconds)

```bash
# 1) Ensure you're in the repo root
cd /path/to/Peak_Trade

# 2) Run the smoke script
python scripts/shadow_run_tick_to_ohlcv_smoke.py

# Expected: ✅ Alle Smoke-Tests bestanden!
```

**Success Indicators:**
- Script exits with code 0
- Console shows 4 steps: Messages → Ticks → Bars → Quality
- At least 1 quality event detected (GAP or SPIKE)

---

## What Just Happened?

The smoke script demonstrated a complete pipeline:

1. **Kraken Trade Messages** — Synthetic WebSocket trade data
2. **Tick Normalization** — Parsed and sorted ticks
3. **OHLCV Building** — Aggregated into 1-minute bars
4. **Quality Monitoring** — Detected gaps/spikes

---

## Next Steps

### Explore the Code

```bash
# Core modules
ls src/data/shadow/

# Guards: _guards.py
# Models: models.py
# Processing: tick_normalizer.py, ohlcv_builder.py, quality_monitor.py
```

### Run Tests

```bash
# All shadow tests
pytest tests/data/shadow/ -v

# Specific component
pytest tests/data/shadow/test_ohlcv_builder.py -v
```

### Read the Docs

- **Full Runbook:** `docs/shadow/SHADOW_PIPELINE_PHASE2_OPERATOR_RUNBOOK.md`
- **Technical Spec:** `docs/shadow/PHASE_2_TICK_TO_OHLCV_AND_QUALITY.md`
- **Config Example:** `config/shadow_pipeline_example.toml`

---

## Safety Notes

- Shadow pipeline is **blocked when live mode is active**
- All components include defense-in-depth guards (Import, Runtime, Config)
- Config defaults to disabled (requires explicit opt-in)

---

## Quick Commands

```bash
# Via Ops Center
scripts/ops/ops_center.sh shadow smoke

# Direct
python scripts/shadow_run_tick_to_ohlcv_smoke.py

# Tests
pytest tests/data/shadow/ -q

# Check config
cat config/shadow_pipeline_example.toml
```

---

## Troubleshooting

### Script Fails Immediately

```bash
# Check Python version
python --version  # Should be 3.9+

# Check dependencies
pip list | grep pandas

# Verify you're NOT in live mode
echo $PEAK_TRADE_LIVE_MODE  # Should be empty
```

### Need Help?

- **Runbook:** `docs/shadow/SHADOW_PIPELINE_PHASE2_OPERATOR_RUNBOOK.md` (Troubleshooting section)
- **Tests:** `pytest tests/data/shadow/test_guards.py -v` (shows guard behavior)

---

**Version:** 1.0  
**Last Updated:** 2025-12-27
