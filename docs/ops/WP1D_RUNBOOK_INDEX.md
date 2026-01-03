# WP1D - Runbook Index

Operator runbooks for Phase 1 Shadow Trading alerts.

---

## 📋 Runbook Index

### P1 Alerts (Critical - Immediate Action Required)

| Alert Code | Runbook | Description |
|------------|---------|-------------|
| `DRIFT_CRITICAL` | [drift_critical.md](runbooks/drift_critical.md) | Critical drift between shadow and backtest |
| `DATA_FEED_DOWN` | [data_feed_down.md](runbooks/data_feed_down.md) | Data feed connection lost |
| `RISK_LIMIT_BREACH` | [risk_limit_breach.md](runbooks/risk_limit_breach.md) | Risk limit breached |

### P2 Alerts (Warning - Action Required Within Hours)

| Alert Code | Runbook | Description |
|------------|---------|-------------|
| `DRIFT_HIGH` | [drift_high.md](runbooks/drift_high.md) | High drift detected |
| `EXECUTION_ERROR` | [execution_error.md](runbooks/execution_error.md) | Execution engine error |

### P3 Alerts (Info - Monitor)

| Alert Code | Runbook | Description |
|------------|---------|-------------|
| `GENERAL` | [general.md](runbooks/general.md) | General alert (no specific runbook) |

---

## 🚀 Quick Actions

### Check System Status
```bash
# View status snapshot
cat reports/ops/wp1d_status_snapshot.json

# Check recent alerts
grep -r "CRITICAL" logs/
```

### Check Drift Reports
```bash
# Latest drift report
ls -t reports/drift/*.md | head -1 | xargs cat
```

### Check Session Registry
```bash
# List active sessions
python -c "from src.live.ops import SessionRegistry; r = SessionRegistry(); print(r.get_summary())"
```

---

## 📖 Additional Resources

- [Phase 1 Roadmap](../execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md)
- [WP1C Drift Detection](drift_detection.md)
- [WP1B Paper Execution](paper_execution.md)

---

**Last Updated:** 2025-01-01  
**Phase:** Shadow Trading (Phase 1)
