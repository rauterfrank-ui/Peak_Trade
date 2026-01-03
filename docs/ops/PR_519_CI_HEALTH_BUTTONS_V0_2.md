# PR 519: Ops WebUI - CI Health Run-Now Buttons (v0.2)

**Status:** ✅ Ready for Review  
**Type:** Feature Enhancement  
**Component:** Ops WebUI / CI & Governance Health Panel  
**Phase:** Ops Tooling v0.2  
**Risk:** LOW (local-only, in-memory lock, no destructive operations)

---

## Summary

Erweitert das CI Health Panel um **interaktive "Run Now" Buttons** mit fetch-basiertem Update (kein Page Reload).

**Key Features:**
- ▶️ **"Run checks now"** Button (POST /ops/ci-health/run)
- 🔄 **"Refresh status"** Button (GET /ops/ci-health/status)
- 🔁 **Auto-refresh Toggle** (15s interval)
- 🔒 **In-memory Lock** verhindert parallele Runs (HTTP 409)
- ❌ **Error Banner** für sauberes Error Handling

---

## Why / Motivation

**Problem:**
- CI Health Status erforderte Page Reload für Updates
- Keine Möglichkeit, Checks manuell zu triggern
- Kein Auto-Refresh für Live-Monitoring

**Lösung:**
- Interactive Controls mit fetch() API
- POST /run Endpoint für manuelles Triggern
- Auto-refresh für kontinuierliches Monitoring
- Lock-Mechanismus verhindert Race Conditions

---

## Changes

### 1. Backend (`src/webui/ops_ci_health_router.py`)

#### Neuer Endpoint: POST /ops/ci-health/run

```python
@router.post("/run")
async def run_ci_health_checks() -> Dict[str, Any]:
    """Trigger CI health checks with in-memory lock."""
    acquired = _CHECK_LOCK.acquire(blocking=False)
    if not acquired:
        raise HTTPException(status_code=409, detail={
            "error": "run_already_in_progress",
            "message": "Another CI health check is already running."
        })
    try:
        # Execute checks + persist snapshot
        # Log run start/end with duration
    finally:
        _CHECK_LOCK.release()
```

**Features:**
- In-memory `threading.Lock()` verhindert parallele Runs
- HTTP 409 bei Konflikt (run already in progress)
- Logging: run start/end + duration
- Snapshot-Persistenz wie GET /status
- Idempotent: safe to call multiple times

### 2. Frontend (`templates/peak_trade_dashboard/ops_ci_health.html`)

#### Control Buttons

```html
<button id="run-checks-btn" onclick="runChecks()">▶️ Run checks now</button>
<button id="refresh-btn" onclick="refreshStatus()">🔄 Refresh status</button>
<label>
  <input type="checkbox" id="auto-refresh-toggle" onchange="toggleAutoRefresh(this.checked)">
  Auto-refresh (15s)
</label>
```

#### JavaScript Functions

```javascript
async function runChecks() {
  const response = await fetch('/ops/ci-health/run', { method: 'POST' });
  const data = await response.json();
  updateUI(data);  // Update badges + checks without page reload
}

async function refreshStatus() {
  const response = await fetch('/ops/ci-health/status', { method: 'GET' });
  const data = await response.json();
  updateUI(data);
}

function toggleAutoRefresh(enabled) {
  if (enabled) {
    autoRefreshInterval = setInterval(refreshStatus, 15000);
  } else {
    clearInterval(autoRefreshInterval);
  }
}
```

**Features:**
- fetch() API (kein page reload)
- Running state (buttons disabled, "⏳ Running...")
- Error handling (red banner, page bleibt nutzbar)
- Dynamic UI updates (badges, checks, timestamps)
- XSS-safe (escapeHtml helper)

### 3. Tests (`tests/webui/test_ops_ci_health_router.py`)

**7 neue Tests:**
- `test_ci_health_run_endpoint_returns_200`: POST /run returns 200 JSON
- `test_ci_health_run_endpoint_executes_checks`: Checks werden ausgeführt
- `test_ci_health_run_parallel_returns_409`: Parallel run returns 409
- `test_ci_health_run_creates_snapshot`: Snapshot wird erstellt
- `test_ci_health_dashboard_contains_buttons`: HTML enthält Buttons
- `test_ci_health_dashboard_has_error_banner`: Error Banner vorhanden
- `test_ci_health_run_sequential_calls_work`: Sequential calls funktionieren

**Test Results:**
```bash
$ python3 -m pytest tests/webui/test_ops_ci_health_router.py -v
============================== 27 passed in 0.74s ==============================
```

---

## API Reference

### POST /ops/ci-health/run

**Trigger CI health checks manually.**

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/ops/ci-health/run \
  -H "Accept: application/json"
```

**Response (200 OK):**
```json
{
  "overall_status": "OK",
  "summary": { "total": 2, "ok": 2, "warn": 0, "fail": 0, "skip": 0 },
  "checks": [ ... ],
  "generated_at": "2025-01-03T15:30:00.123",
  "server_timestamp_utc": "2025-01-03T14:30:00.123Z",
  "git_head_sha": "abc1234",
  "app_version": "0.2.0",
  "run_triggered": true
}
```

**Response (409 Conflict):**
```json
{
  "detail": {
    "error": "run_already_in_progress",
    "message": "Another CI health check is already running. Please wait.",
    "last_run": "2025-01-03T14:29:55.123Z"
  }
}
```

---

## Operator Usage

### Manual Check Execution

1. **Open Dashboard:**
   ```bash
   open http://127.0.0.1:8000/ops/ci-health
   ```

2. **Click "Run checks now":**
   - Button wird disabled
   - Text ändert sich zu "⏳ Running..."
   - Nach Completion: UI wird aktualisiert

3. **Click "Refresh status":**
   - Fetches latest snapshot
   - Updates UI ohne Page Reload

### Auto-Refresh

1. **Enable Auto-Refresh:**
   - Toggle Checkbox "Auto-refresh (15s)"
   - Status wird alle 15 Sekunden aktualisiert

2. **Disable Auto-Refresh:**
   - Untoggle Checkbox
   - Interval wird gestoppt

### Error Handling

**Scenario: Parallel Run Attempt**
- User 1 clicks "Run checks now"
- User 2 clicks "Run checks now" (während Run läuft)
- User 2 sieht Error Banner: "Another CI health check is already running"
- Page bleibt nutzbar, kein Crash

---

## Verification

### Automated Tests

```bash
$ python3 -m pytest tests/webui/test_ops_ci_health_router.py -v
# ✅ 27 passed (7 new v0.2 tests)
```

### Manual Verification

```bash
# 1. Start WebUI
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# 2. Open Dashboard
open http://127.0.0.1:8000/ops/ci-health

# 3. Test "Run checks now"
# - Click button
# - Observe "⏳ Running..." state
# - Observe UI update after completion

# 4. Test "Refresh status"
# - Click button
# - Observe UI update

# 5. Test Auto-refresh
# - Enable toggle
# - Wait 15 seconds
# - Observe automatic update

# 6. Test Parallel Run (409)
# - Open two browser tabs
# - Click "Run checks now" in both tabs simultaneously
# - Observe error banner in second tab
```

---

## Risk Assessment

**Risk Level:** 🟢 LOW

### Safety Guarantees

✅ **Local-only:** Keine externen API Calls  
✅ **In-memory Lock:** Verhindert parallele Runs  
✅ **Read-only Checks:** Keine destructive operations  
✅ **Error Isolation:** Errors failen Page nicht  
✅ **XSS-safe:** HTML escaping in JavaScript

### Security Considerations

**CSRF:**
- Same-origin only (fetch ohne credentials)
- Accept JSON only
- Keine sensiblen Aktionen (nur lokale Checks)

**Rate Limiting:**
- In-memory lock (max 1 concurrent run)
- Optional: cooldown 5s (nicht implementiert, aber einfach erweiterbar)

**DoS:**
- Lock verhindert Resource Exhaustion
- Checks haben Timeout (30s default)

---

## Future Enhancements (Out of Scope)

**v0.3 Kandidaten:**
- WebSocket für Real-Time Updates
- Progress Bar während Check Execution
- Check History (letzte 10 Runs)
- Configurable Auto-Refresh Interval
- Keyboard Shortcuts (Ctrl+R für Refresh)

---

## Commit Message

```
ops(webui): add run-now buttons for CI health (v0.2)

Erweitert CI Health Panel um interaktive Controls:

Features:
- POST /ops/ci-health/run endpoint (trigger checks)
- "Run checks now" button (fetch-based, no page reload)
- "Refresh status" button (fetch latest snapshot)
- Auto-refresh toggle (15s interval)
- In-memory lock prevents parallel runs (HTTP 409)
- Error banner for user-friendly error handling
- Running state (buttons disabled, visual feedback)

Frontend:
- fetch() API for async updates
- Dynamic UI updates (badges, checks, timestamps)
- XSS-safe HTML escaping
- Auto-refresh with cleanup on page unload

Tests:
- 7 neue Tests für Run-Now Funktionalität
- Coverage: parallel runs, error handling, UI elements
- 27/27 tests passed

Risk: LOW (local-only, in-memory lock, no destructive ops)

Refs: PR #519, Ops Tooling v0.2
```

---

## PR Description (GitHub)

```markdown
## Summary

Erweitert das CI Health Panel um **interaktive "Run Now" Buttons** mit fetch-basiertem Update (kein Page Reload).

**Key Features:**
- ▶️ "Run checks now" (POST /run mit Lock)
- 🔄 "Refresh status" (GET /status)
- 🔁 Auto-refresh Toggle (15s)
- ❌ Error Banner (user-friendly)

## Why

- **Problem:** Page Reload für Updates, keine manuelle Trigger-Möglichkeit
- **Lösung:** Interactive Controls mit fetch() API + Auto-refresh

## Changes

### Backend
- POST /ops/ci-health/run endpoint
- In-memory `threading.Lock()` verhindert parallele Runs
- HTTP 409 bei Konflikt

### Frontend
- 3 Buttons (Run, Refresh, Auto-refresh)
- fetch() API (kein page reload)
- Dynamic UI updates (badges, checks, timestamps)
- Error banner (red, dismissable)

### Tests
- 7 neue Tests
- 27/27 passed ✅

## Verification

```bash
# Automated
python3 -m pytest tests/webui/test_ops_ci_health_router.py -v
# ✅ 27 passed

# Manual
open http://127.0.0.1:8000/ops/ci-health
# Click buttons, observe updates
```

## Risk

🟢 **LOW**
- Local-only, in-memory lock, read-only checks
- XSS-safe, error isolation

## Refs

- Phase: Ops Tooling v0.2
- Related: PR #518 (CI Health Snapshots)
```

---

**End of PR Documentation**
