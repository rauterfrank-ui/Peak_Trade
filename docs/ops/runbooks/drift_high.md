# Runbook: DRIFT_HIGH

**Alert Code:** `DRIFT_HIGH`  
**Priority:** P2 (Warning)  
**Description:** High drift detected (below critical threshold).

---

## ⚠️ Actions (Within 4 Hours)

### 1. Review Drift Report
```bash
ls -t reports/drift/*.md | head -1 | xargs cat
```

### 2. Monitor for Increase
Check if drift is increasing or stable.

### 3. Investigate Common Causes
- Slippage differences
- Fee calculation differences
- Timing offsets

---

## 📋 Escalation

Escalate to P1 if drift continues to increase.

---

**Last Updated:** 2025-01-01
