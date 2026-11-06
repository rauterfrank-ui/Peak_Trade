# Runbook: DRIFT_CRITICAL

**Alert Code:** `DRIFT_CRITICAL`  
**Priority:** P1 (Critical - Immediate Action Required)  
**Description:** Critical drift detected between shadow trading and backtest expectations.

---

## 🚨 Immediate Actions

### 1. Pause Shadow Trading ⏸️
```python
# Pause shadow session
from src.live.ops import SessionRegistry
registry = SessionRegistry()
registry.update_status("current_session_id", "paused")
```

### 2. Check Drift Report 📊
```bash
# View latest drift report
ls -t reports/drift/*.md | head -1 | xargs cat
```

### 3. Investigate Root Cause 🔍

**Common Causes:**
- Data feed quality issues (missing bars, stale data)
- Timing differences (execution latency)
- Logic divergence (strategy implementation bug)

**Checks:**
```bash
# Check data quality
cat reports/data/wp1a_feed_evidence.md

# Check recent executions
tail -100 logs/execution.log
```

---

## 📋 Escalation

If drift persists after investigation:
1. Contact platform team
2. Review backtest assumptions
3. Update drift thresholds if needed

---

## 📖 Related

- [WP1C Drift Detection](../../execution/WP1C_COMPLETION_REPORT.md)
- [WP1A Live Data Feed](../../execution/WP1A_COMPLETION_REPORT.md)

---

**Last Updated:** 2025-01-01
