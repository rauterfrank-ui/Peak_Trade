# Component VaR Phase 2A: Operator Report

**Status:** ✅ Implemented  
**Phase:** 2A (Reporting)  
**Related:** [COMPONENT_VAR_MVP.md](COMPONENT_VAR_MVP.md)

## Quick Start (3 Lines)

```bash
# With fixtures (testing)
./scripts/ops/ops_center.sh risk component-var --use-fixtures

# With your data
./scripts/ops/ops_center.sh risk component-var --returns data/returns.csv --weights BTC=0.6,ETH=0.3,SOL=0.1 --alpha 0.95
```

---

## What It Does

Generates comprehensive Component VaR reports in **3 formats**:
- **HTML** — Interactive report with charts and sanity checks
- **JSON** — Machine-readable data for automation
- **CSV** — Table export for spreadsheets

**Output Structure:**
```
results/risk/component_var/<run_id>/
  ├── report.html     # Main visual report
  ├── report.json     # Data export
  └── table.csv       # Asset table
```

---

## Usage

### Via Ops Center (Recommended)

```bash
# Quick test with fixtures
ops risk component-var --use-fixtures

# Custom confidence & horizon
ops risk component-var --use-fixtures --alpha 0.99 --horizon 10

# With your returns data
ops risk component-var --returns path/to/returns.csv
```

### Direct Script

```bash
# Full control
python scripts/run_component_var_report.py \
  --returns data/returns.csv \
  --weights BTC=0.6,ETH=0.25,SOL=0.15 \
  --alpha 0.95 \
  --horizon 1 \
  --lookback 252 \
  --portfolio-value 1000000 \
  --output-dir results/risk/custom
```

---

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--returns PATH` | CSV file with returns (columns=assets) | Required* |
| `--use-fixtures` | Use test fixtures instead | Required* |
| `--weights SPEC` | Weights as `SYM=W,...` (e.g., `BTC=0.6,ETH=0.4`) | Equal weights |
| `--alpha FLOAT` | Confidence level (0-1) | 0.95 |
| `--horizon INT` | Horizon in days | 1 |
| `--lookback INT` | Lookback window (days) | All data |
| `--portfolio-value FLOAT` | Portfolio value (USD) | 1,000,000 |
| `--output-dir PATH` | Output directory | Auto-generated |
| `--run-id STRING` | Run identifier | Timestamp |

\* Either `--returns` or `--use-fixtures` is required.

---

## Input Data Format

**Returns CSV:**
```csv
date,BTC,ETH,SOL
2024-01-01,0.02,0.01,0.03
2024-01-02,-0.01,0.00,0.02
2024-01-03,0.03,0.02,0.01
```

- **Index:** Date column (will be parsed as datetime)
- **Columns:** Asset symbols
- **Values:** Returns (not prices) as decimals (e.g., 0.02 = 2%)

---

## Output Formats

### 1. HTML Report (`report.html`)

Interactive report with:
- **Summary Metrics:** Total VaR, portfolio value, confidence, horizon
- **Top Contributors:** Top 5 assets by risk contribution
- **Full Table:** All assets with weights, CompVaR, contribution %, marginal VaR
- **Sanity Checks:** Automated validation (weights sum, Euler property, no NaNs)

**Open in browser:**
```bash
open results/risk/component_var/<run_id>/report.html
```

### 2. JSON Report (`report.json`)

Complete data export:
```json
{
  "run_id": "20251225_120000",
  "timestamp": "2025-12-25T12:00:00",
  "total_var": 45678.90,
  "portfolio_value": 1000000.0,
  "confidence": 0.95,
  "asset_symbols": ["BTC", "ETH", "SOL"],
  "component_var": [27407.34, 13703.67, 4567.89],
  "contribution_pct": [60.0, 30.0, 10.0],
  "sanity_checks": {
    "all_pass": true,
    ...
  }
}
```

### 3. CSV Table (`table.csv`)

Asset-level breakdown:
```csv
symbol,weight,component_var,contribution_pct,marginal_var
BTC,0.600000,27407.340000,60.000000,45678.900000
ETH,0.300000,13703.670000,30.000000,45678.900000
SOL,0.100000,4567.890000,10.000000,45678.900000
```

---

## Sanity Checks

The report automatically validates:

✅ **Weights Sum:** Should be ~1.0 (within 1%)  
✅ **No NaNs:** All values are finite numbers  
✅ **Euler Property:** Σ CompVaR = Total VaR (within 1%)  
✅ **Sufficient Assets:** At least 2 assets

**Exit Codes:**
- `0` — All checks passed
- `1` — Warnings detected (see HTML report for details)

---

## Examples

### Example 1: Quick Test

```bash
# Generate report with fixtures
ops risk component-var --use-fixtures
```

**Output:**
```
Component VaR Report Generated
================================================================================
Run ID:         20251225_120530
Output Dir:     results/risk/component_var/20251225_120530
Total VaR:      $48,456.78
Portfolio:      $1,000,000.00
Confidence:     95.0%
Horizon:        1 day(s)
Assets:         3

Sanity Checks:  ✅ PASS

Generated Files:
  - JSON  : results/risk/component_var/20251225_120530/report.json
  - CSV   : results/risk/component_var/20251225_120530/table.csv
  - HTML  : results/risk/component_var/20251225_120530/report.html
================================================================================
```

### Example 2: Custom Portfolio

```bash
# 70/20/10 allocation, 99% confidence
ops risk component-var \
  --use-fixtures \
  --weights BTC=0.7,ETH=0.2,SOL=0.1 \
  --alpha 0.99 \
  --portfolio-value 5000000
```

### Example 3: Production Data

```bash
# Real returns, 10-day horizon, 1-year lookback
python scripts/run_component_var_report.py \
  --returns data/crypto_returns_2024.csv \
  --weights BTC=0.5,ETH=0.3,SOL=0.15,AVAX=0.05 \
  --alpha 0.95 \
  --horizon 10 \
  --lookback 252 \
  --portfolio-value 10000000 \
  --run-id prod_20251225
```

---

## Integration with Workflow

### 1. Automated Reporting

```bash
# Run daily Component VaR report
cron: 0 9 * * * cd /path/to/Peak_Trade && ops risk component-var --returns latest.csv
```

### 2. CI/CD Integration

```bash
# In GitHub Actions / CI pipeline
- name: Generate Component VaR Report
  run: |
    python scripts/run_component_var_report.py --use-fixtures
    # Fail if sanity checks fail
```

### 3. Monitoring & Alerting

```python
# Parse JSON output for monitoring
import json

with open("results/risk/component_var/latest/report.json") as f:
    report = json.load(f)

if report["total_var"] > threshold:
    send_alert(f"Portfolio VaR exceeded: ${report['total_var']:,.2f}")
```

---

## Troubleshooting

### Error: "Fixture file not found"

**Solution:** Run from repo root or check fixture path:
```bash
cd ~/Peak_Trade
ops risk component-var --use-fixtures
```

### Error: "insufficient data"

**Cause:** Not enough historical returns for covariance estimation.  
**Solution:** Use longer lookback or check data quality:
```bash
# Minimum recommended: 30 days
--lookback 60
```

### Warning: "Euler property violation"

**Cause:** Numerical precision issues or invalid weights.  
**Solution:** Check weights sum to 1.0:
```python
import pandas as pd
df = pd.read_csv("report.json")
assert abs(df["weights"].sum() - 1.0) < 0.01
```

---

## Architecture

```
scripts/run_component_var_report.py
  ├─> src/risk/component_var.py           (Core calculation)
  ├─> src/reporting/component_var_report.py  (Report generator)
  └─> results/risk/component_var/         (Outputs)
```

**Key Components:**
1. **Data Loading:** CSV or fixtures
2. **Calculation:** `calculate_component_var()` from MVP
3. **Validation:** Sanity checks
4. **Generation:** Multi-format reports (HTML/JSON/CSV)

---

## Next Steps

**Phase 2B:** Integration with Live Portfolio  
**Phase 3:** Risk Limits & Alerting  
**Phase 4:** Regime-Aware Component VaR

See: [../COMPONENT_VAR_ROADMAP_PATCHED.md](../COMPONENT_VAR_ROADMAP_PATCHED.md)

---

## References

- **Core Implementation:** `src/risk/component_var.py`
- **Report Generator:** `src/reporting/component_var_report.py`
- **Script:** `scripts/run_component_var_report.py`
- **Tests:** `tests/risk/test_component_var_report.py`
- **Ops Integration:** `scripts/ops/ops_center.sh` (`risk component-var`)
