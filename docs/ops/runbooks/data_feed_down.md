# Runbook: DATA_FEED_DOWN

**Alert Code:** `DATA_FEED_DOWN`  
**Priority:** P1 (Critical)  
**Description:** Data feed connection lost.

---

## 🚨 Immediate Actions

### 1. Check Connection Status
```bash
# Check recent reconnects
grep "reconnect" logs/datafeed.log | tail -20
```

### 2. Verify Network
```bash
# Test connectivity
ping api.exchange.com
```

### 3. Monitor Auto-Reconnect
The system will automatically attempt to reconnect.  
Monitor reconnection attempts in logs.

---

## 📋 If Reconnect Fails

1. Check API credentials
2. Verify API status (exchange status page)
3. Restart data feed service

---

**Last Updated:** 2025-01-01
