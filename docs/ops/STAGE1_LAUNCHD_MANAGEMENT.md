# Stage 1 Monitoring - LaunchAgents Management

**Status:** Repo-Einstiege separat prüfbar; geladene Hostdienste brauchen einen eigenen Funktionsbeleg.

**Setup Date:** 2025-12-20  
**Platform:** macOS (launchd)

---

## 📊 Installed LaunchAgents

| Label | Schedule | Script | Status |
|-------|----------|--------|--------|
| `com.peaktrade.stage1.daily` | Daily 09:05 | `stage1_run_daily.sh` | Installationsbeispiel |
| `com.peaktrade.stage1.weekly` | Sunday 10:00 | `stage1_run_weekly.sh` | Installationsbeispiel |

---

## 🔍 Status Check

### Quick Status

```bash
# List running jobs
launchctl list | grep com.peaktrade.stage1

# PID und letzter Exit hängen vom tatsächlich geladenen Job ab.
```

### Detailed Info

```bash
# Show full job info (macOS 11+)
launchctl print gui/$(id -u)/com.peaktrade.stage1.daily
launchctl print gui/$(id -u)/com.peaktrade.stage1.weekly
```

---

## Abnahme vor Deployment

`launchctl print` zeigt den geladenen Einstieg, sein Arbeitsverzeichnis und den letzten Exit.
Vergleiche beide Einträge mit dem vorgesehenen, sauberen Deployment-Checkout und prüfe dort
`./scripts/pt runtime-check`. Ein Repo-Merge aktualisiert keine geladenen Plists.
Daily und Weekly verwenden denselben Stage1-Ausgabepfad. `REPORT_ROOT` überschreibt ihn
explizit; sonst gilt der Stage1-IO-Vertrag. Der Daily-Wrapper schreibt und validiert seinen
Snapshot auch bei Warnstatus 2. Der Weekly-Wrapper liest die Snapshots und veröffentlicht
erst nach erfolgreicher Trendberechnung einen Trendbericht. Ein nachgelagertes Monitoring
darf einen vorhandenen alten Trend nicht als neuen Laufbeleg lesen.

Für die isolierte Probe kann `STAGE1_INPUT_ROOT` am Daily-Wrapper auf einen Eingabeordner
mit kontrollierten Testereignissen zeigen. Ein Repo-Test mit diesen Eingaben belegt weder
die Hostausführung noch die Zustellung des separaten Recovery-Mail-Dienstes.

## 🎮 Management Commands

### Manual Trigger (Testing)

```bash
# Trigger daily job now
launchctl kickstart -k gui/$(id -u)/com.peaktrade.stage1.daily

# Trigger weekly job now
launchctl kickstart -k gui/$(id -u)/com.peaktrade.stage1.weekly

# Wait 5s and check logs
sleep 5
cat ~/Peak_Trade/logs/launchd/stage1_daily.out
```

### Start/Stop

```bash
MY_UID=$(id -u)

# Stop (disable)
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.daily
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.weekly

# Start (enable)
launchctl bootstrap gui/$MY_UID ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist
launchctl bootstrap gui/$MY_UID ~/Library/LaunchAgents/com.peaktrade.stage1.weekly.plist
```

### Reload (after editing plist)

```bash
MY_UID=$(id -u)

# Reload daily job
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.daily
launchctl bootstrap gui/$MY_UID ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist

# Verify
launchctl list | grep com.peaktrade.stage1.daily
```

---

## 📁 File Locations

### Plist Files (Configuration)

```
~/Library/LaunchAgents/
├── com.peaktrade.stage1.daily.plist    ← Daily job config
└── com.peaktrade.stage1.weekly.plist   ← Weekly job config
```

**Edit:**
```bash
# Edit with text editor
nano ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist

# After editing: RELOAD (see above)
```

### Scripts

```
~/Peak_Trade/scripts/obs/
├── stage1_run_daily.sh     ← Daily runner
└── stage1_run_weekly.sh    ← Weekly runner
```

### Logs

```
~/Peak_Trade/logs/launchd/
├── stage1_daily.out        ← Daily stdout
├── stage1_daily.err        ← Daily stderr
├── stage1_weekly.out       ← Weekly stdout
└── stage1_weekly.err       ← Weekly stderr
```

**View logs:**
```bash
# Latest daily output
cat ~/Peak_Trade/logs/launchd/stage1_daily.out

# Live tail (for debugging)
tail -f ~/Peak_Trade/logs/launchd/stage1_daily.out

# Check for errors
cat ~/Peak_Trade/logs/launchd/stage1_daily.err
```

### Reports

```
~/Peak_Trade/reports/obs/stage1/
├── YYYY-MM-DD_snapshot.md    ← Daily snapshots
└── YYYY-MM-DD_trend.md       ← Weekly trends
```

---

## 🔧 Common Tasks

### Change Schedule

**Example: Change daily job from 09:05 to 08:00**

```bash
# 1) Edit plist
nano ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist

# Find:
#   <key>Hour</key><integer>9</integer>
#   <key>Minute</key><integer>5</integer>
#
# Change to:
#   <key>Hour</key><integer>8</integer>
#   <key>Minute</key><integer>0</integer>

# 2) Reload
MY_UID=$(id -u)
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.daily
launchctl bootstrap gui/$MY_UID ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist

# 3) Verify
launchctl print gui/$MY_UID/com.peaktrade.stage1.daily | grep "next fire"
```

### Disable Temporarily

```bash
# Stop jobs (but keep plist files)
MY_UID=$(id -u)
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.daily
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.weekly

# Re-enable later
launchctl bootstrap gui/$MY_UID ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist
launchctl bootstrap gui/$MY_UID ~/Library/LaunchAgents/com.peaktrade.stage1.weekly.plist
```

### Complete Uninstall

```bash
# 1) Stop jobs
MY_UID=$(id -u)
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.daily 2>/dev/null || true
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.weekly 2>/dev/null || true

# 2) Remove plist files
rm ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist
rm ~/Library/LaunchAgents/com.peaktrade.stage1.weekly.plist

# 3) Verify
launchctl list | grep com.peaktrade.stage1
# (should return empty)
```

---

## 🐛 Troubleshooting

### Job not running

**Check 1: Is it loaded?**
```bash
launchctl list | grep com.peaktrade.stage1
# Should show 2 lines with PID or "-"
```

**Check 2: Check logs for errors**
```bash
cat ~/Peak_Trade/logs/launchd/stage1_daily.err
# Should be empty or contain error messages
```

**Check 3: Verify plist paths**
```bash
grep "string>" ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist | head -10
# All paths should be absolute (starting with /Users/...)
```

**Check 4: Manual test**
```bash
# Run script directly
cd ~/Peak_Trade
bash scripts/obs/stage1_run_daily.sh
# Should work without errors
```

### Logs not created

**Cause:** Log directory doesn't exist

**Fix:**
```bash
mkdir -p ~/Peak_Trade/logs/launchd

# Reload job
MY_UID=$(id -u)
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.daily
launchctl bootstrap gui/$MY_UID ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist
```

### Script fails with "command not found"

**Cause:** venv not activated or python not in PATH

**Check:**
```bash
# Test script directly
cd ~/Peak_Trade
bash -lc "scripts/obs/stage1_run_daily.sh"
# Note the -lc flag (login shell)
```

**Fix:** Ensure plist uses `-lc` flag:
```xml
<array>
  <string>/bin/bash</string>
  <string>-lc</string>  <!-- ← Important! -->
  <string>/Users/frnkhrz/Peak_Trade/scripts/obs/stage1_run_daily.sh</string>
</array>
```

### Job runs but reports not updated

**Check 1: Verify script output**
```bash
cat ~/Peak_Trade/logs/launchd/stage1_daily.out
# Should show:
# ✅ Wrote: /Users/frnkhrz/Peak_Trade/reports/obs/stage1/YYYY-MM-DD_snapshot.md
```

**Check 2: Check report directory**
```bash
ls -lth ~/Peak_Trade/reports/obs/stage1/
# Should show recent files
```

**Check 3: Run manually**
```bash
cd ~/Peak_Trade
python3 scripts/obs/stage1_daily_snapshot.py
# Should create new snapshot
```

---

## 📊 Expected Behavior (Healthy)

### Daily Job Output

```
=== Stage1 DAILY 2025-12-20T09:05:00+01:00 ===
✅ Wrote: /Users/frnkhrz/Peak_Trade/reports/obs/stage1/2025-12-20_snapshot.md
   New-alerts heuristic (24h): 0
=== done ===
```

**Exit Code:** 0 (OK), 2 (new alerts detected)

### Weekly Job Output

```
=== wrote: reports/obs/stage1/2025-12-20_trend.md ===
```

### Typical Logs (first week)

```bash
$ cat ~/Peak_Trade/logs/launchd/stage1_daily.out
=== Stage1 DAILY 2025-12-20T09:05:00+01:00 ===
✅ Wrote: /Users/frnkhrz/Peak_Trade/reports/obs/stage1/2025-12-20_snapshot.md
   New-alerts heuristic (24h): 0
=== done ===
=== Stage1 DAILY 2025-12-21T09:05:00+01:00 ===
✅ Wrote: /Users/frnkhrz/Peak_Trade/reports/obs/stage1/2025-12-21_snapshot.md
   New-alerts heuristic (24h): 0
=== done ===
```

**Metrics (Healthy Stage 1):**
- New alerts: 0-5 per day
- Legacy hits: 100-600 per day (ignore)
- Operator actions: 0
- Exit code: 0 (no new alerts)

---

## 🎯 Monitoring Workflow

### Daily Routine (5 Min)

```bash
# 1) Check if job ran today
ls -lh ~/Peak_Trade/reports/obs/stage1/$(date +%F)_snapshot.md

# 2) Review snapshot (optional)
cat ~/Peak_Trade/reports/obs/stage1/$(date +%F)_snapshot.md | grep "New-alerts"

# 3) Check for errors
cat ~/Peak_Trade/logs/launchd/stage1_daily.err
```

### Weekly Review (10 Min)

```bash
# 1) Check trend report
cat ~/Peak_Trade/reports/obs/stage1/$(date +%F)_trend.md

# 2) Look for Quick Signal
# ✅ = Green light (ready for Stage 2)
# ⚠️ = Yellow (investigate)

# 3) Manual trend analysis (optional)
python3 scripts/obs/stage1_trend_report.py --days 14
```

---

## 📖 Related Documentation

- **Main README:** `scripts/obs/README.md`
- **Runbooks:**
  - `docs/ops/TELEMETRY_ALERTING_RUNBOOK.md`
  - `docs/ops/TELEMETRY_ALERTING_LIFECYCLE_RUNBOOK.md`
  - `docs/ops/TELEMETRY_HEALTH_TRENDS_RUNBOOK.md`

---

## ✅ Quick Reference Card

```bash
# STATUS
launchctl list | grep com.peaktrade.stage1

# LOGS (tail live)
tail -f ~/Peak_Trade/logs/launchd/stage1_daily.out

# LATEST REPORT
cat ~/Peak_Trade/reports/obs/stage1/$(date +%F)_snapshot.md

# MANUAL TRIGGER
launchctl kickstart -k gui/$(id -u)/com.peaktrade.stage1.daily

# RELOAD (after editing plist)
MY_UID=$(id -u)
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.daily
launchctl bootstrap gui/$MY_UID ~/Library/LaunchAgents/com.peaktrade.stage1.daily.plist

# STOP ALL
MY_UID=$(id -u)
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.daily
launchctl bootout gui/$MY_UID/com.peaktrade.stage1.weekly
```

---

**Last Updated:** 2025-12-20  
**Version:** 1.0
