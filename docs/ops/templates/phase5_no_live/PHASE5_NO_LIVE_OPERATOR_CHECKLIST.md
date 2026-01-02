# Phase 5 NO-LIVE Drill — Operator Checklist

---

## 🚨 NO-LIVE DRILL ONLY 🚨
**Check each item as you proceed. Any unchecked items = drill incomplete (NO-GO).**

---

## Metadata

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Operator** | [Your Name] |
| **Run ID** | drill_YYYYMMDD_HHMMSS |
| **Start Time** | HH:MM |
| **End Time** | HH:MM |

---

## Pre-Flight (Before Step 1)

- [ ] Preconditions checklist reviewed (see main drill pack document)
- [ ] Repo on correct branch: `git status -sb`
- [ ] Python venv activated: `which python` shows venv path
- [ ] Templates copied to working directory: `ls docs/ops/templates/phase5_no_live/`
- [ ] Governance approval documented (email, ticket, or verbal confirmation noted)

**Blocker?** If any item unchecked, STOP and resolve.

---

## Step 1: Environment Setup & Verification

- [ ] Verified current config environment (SHADOW/PAPER/DRILL_ONLY)
  - Command run: `grep -i "environment\|mode" config/config.toml`
  - Result: [paste relevant line, e.g., `mode = "shadow"`]
- [ ] Audited for live API keys (none found)
  - Command run: `grep -rI "api.exchange.live" config/`
  - Result: [e.g., "No matches" or "OK: No live keys"]
- [ ] Documented findings in EVIDENCE_INDEX.md
- [ ] Timestamp logged: [HH:MM]

**Issues?** [Note any anomalies or leave blank if clean]

---

## Step 2: Pre-Flight Systems Check

- [ ] Health check script executed successfully
  - EXAMPLE Command: Run health check script (create as needed)
  - Exit code: [0 = success]
- [ ] Telemetry pipeline verified active
  - Command: `ls -lht logs/ | head -5`
  - Recent log files present: [Y/N]
- [ ] Market data feed tested (paper/shadow)
  - EXAMPLE Command: Test data feed (create script as needed)
  - Result: [Data received / Timeout / Error]
- [ ] Screenshots/logs captured as evidence
- [ ] Timestamp logged: [HH:MM]

**Issues?** [Note any failures; if critical, consider NO-GO]

---

## Step 3: Strategy Dry-Run

- [ ] Test strategy selected: [e.g., ma_crossover_drill]
- [ ] Test symbol selected: [e.g., BTC-EUR]
- [ ] Config file prepared (mode confirmed as shadow/paper)
  - Path: `config/[filename].toml`
  - Key settings verified: [list 2-3 key params, e.g., window=50, mode=shadow]
- [ ] Strategy execution command run:
  - EXAMPLE Command: Run strategy engine with drill config (configure as needed)
  - Start time: [HH:MM]
  - End time: [HH:MM]
- [ ] Logs monitored in real-time (no crashes)
  - Command: `tail -f logs/strategy_drill.log`
  - Observed: [Normal operation / Errors noted below]
- [ ] Outputs collected:
  - [ ] `results/drill_<timestamp>/trades/simulated_trades.csv`
  - [ ] `results/drill_<timestamp>/metrics/performance_summary.json`
  - [ ] `results/drill_<timestamp>/logs/strategy_drill.log`
- [ ] Simulated trades confirmed (NO real fills)
- [ ] Timestamp logged: [HH:MM]

**Issues?** [Note any errors, timeouts, or unexpected behavior]

---

## Step 4: Evidence Pack Assembly

- [ ] EVIDENCE_INDEX.md template copied to results folder
  - Path: `results/drill_<timestamp>/EVIDENCE_INDEX.md`
- [ ] All metadata fields filled in (date, operator, SHA, run ID, etc.)
- [ ] Artifact paths documented in EVIDENCE_INDEX.md:
  - [ ] Config files
  - [ ] Log files
  - [ ] Trade data (simulated)
  - [ ] Metrics/plots
  - [ ] Screenshots (if any)
- [ ] Cross-referenced with OPERATOR_CHECKLIST.md (this file)
- [ ] NO external links used (repo-relative paths only)
- [ ] NO-LIVE attestation signed in EVIDENCE_INDEX.md
- [ ] Timestamp logged: [HH:MM]

**Issues?** [Note any missing artifacts or gaps]

---

## Step 5: Go/No-Go Assessment

- [ ] GO_NO_GO_RECORD.md template copied to results folder
  - Path: `results/drill_<timestamp>/GO_NO_GO_RECORD.md`
- [ ] All 5 success criteria evaluated (see GO_NO_GO_RECORD.md)
  - [ ] Criterion 1: Environment verified as NO-LIVE [PASS/FAIL]
  - [ ] Criterion 2: Strategy executed without critical errors [PASS/FAIL]
  - [ ] Criterion 3: Evidence pack complete [PASS/FAIL]
  - [ ] Criterion 4: No live trading prohibitions violated [PASS/FAIL]
  - [ ] Criterion 5: Operator competency demonstrated [PASS/FAIL]
- [ ] Overall decision recorded: **GO** / **NO-GO**
- [ ] Rationale documented (2-3 sentences)
- [ ] Next steps defined (archive if GO; remediation plan if NO-GO)
- [ ] Signatures obtained (operator + peer reviewer if available)
- [ ] Timestamp logged: [HH:MM]

**Issues?** [If NO-GO, list top 3 issues to remediate]

---

## Post-Drill (After Step 5)

- [ ] All checklist items above completed (or NO-GO declared)
- [ ] Evidence pack archived: `tar -czf drill_<timestamp>.tar.gz results/drill_<timestamp>/`
- [ ] POST_RUN_REVIEW.md template filled out (see separate template)
- [ ] This checklist saved to: `results/drill_<timestamp>/OPERATOR_CHECKLIST.md`
- [ ] Operator training record updated (if applicable)
- [ ] Drill results communicated to governance approver

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Drill Duration** | [X minutes] |
| **Steps Completed** | [X / 5] |
| **Critical Issues** | [X] |
| **GO / NO-GO** | [GO / NO-GO] |

---

## Operator Notes / Observations

[Freeform field for any additional notes, observations, or recommendations. Examples:
- "Step 3 took longer than expected due to slow market data feed"
- "Config audit was straightforward; no issues"
- "Recommend adding timeout config to strategy for future drills"]

---

## Approval

**Operator:**  
Name: ___________________________  
Date: ___________________________  
Signature: ___________________________

**Peer Reviewer (if applicable):**  
Name: ___________________________  
Date: ___________________________  
Findings: [No issues / See GO_NO_GO_RECORD for details]

---

**END OF OPERATOR CHECKLIST**
