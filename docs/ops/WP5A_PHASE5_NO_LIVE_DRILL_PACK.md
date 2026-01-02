# WP5A — Phase 5 NO-LIVE Drill Pack (Manual-Only)

---

## 🚨 NO-LIVE BANNER 🚨

**THIS IS A DRILL-ONLY PROCEDURE**

- **NO LIVE TRADING PERMITTED**
- **NO REAL FUNDS / EXCHANGE CONNECTIVITY**
- **NO AUTOMATIC ENABLEMENT OF LIVE ENVIRONMENTS**
- This drill pack is for **governance validation**, **operator training**, and **readiness assessment** only
- All steps must be executed in **SHADOW**, **PAPER**, or **DRILL_ONLY** mode
- Any Go/No-Go decision applies **ONLY to drill completion** — NOT to live trading authorization

---

## Purpose & Scope

### Purpose
WP5A Phase 5 provides a **manual, operator-driven drill pack** to validate:
- End-to-end operational readiness for autonomous trading systems
- Governance controls and audit trails
- Operator competency in executing critical procedures
- Evidence collection and documentation practices

### Scope
- **In Scope:** Paper/Shadow/Drill environments; manual procedures; documentation templates
- **Out of Scope:** Live trading enablement; real exchange connectivity; automated live deployment; funding instructions; API key configuration for live accounts

### Definitions
| Term | Definition |
|------|------------|
| **LIVE** | Real trading with actual funds on production exchanges (PROHIBITED in this drill) |
| **PAPER** | Simulated trading with fake fills (broker/exchange paper trading mode) |
| **SHADOW** | Real market data + internal simulation (no orders leave the system) |
| **DRILL_ONLY** | Operator training mode with synthetic scenarios |
| **GO** (in this context) | Drill completed successfully; readiness validated for NO-LIVE operations |
| **NO-GO** | Drill failed; gaps identified; remediation required before retry |

---

## Hard Prohibitions (MUST NOT)

**The following are strictly PROHIBITED under this drill pack:**

1. **Exchange Live API Keys:** Do not configure, store, or reference live API credentials
2. **Real Funding:** Do not transfer actual funds to any account or wallet
3. **Live Order Routing:** Do not enable real order submission to production exchanges
4. **Automatic Live Enablement:** Do not create scripts/configs that auto-enable live trading
5. **Production Infrastructure Changes:** Do not modify live system configs without separate approval (outside WP5A)
6. **Unsupervised Execution:** All drill steps require human operator validation

**Violation of these prohibitions invalidates the drill and triggers governance review.**

---

## Preconditions Checklist (Entry Criteria)

Before executing this drill, verify ALL conditions are met:

- [ ] **Operator trained** on Peak_Trade system architecture (docs/ops/)
- [ ] **Environment confirmed:** SHADOW, PAPER, or DRILL_ONLY (verify via config)
- [ ] **No live keys present:** Audit config files and environment variables
- [ ] **Repo clean:** Git status shows expected branch (docs/wp5a-no-live-drill-pack or similar)
- [ ] **Dependencies installed:** Python venv active, requirements.txt satisfied
- [ ] **Logs directory writeable:** Ensure audit trail can be captured
- [ ] **Templates available:** docs/ops/templates/phase5_no_live/ accessible
- [ ] **Governance approval:** WP5A drill authorized by project lead (document in Evidence Pack)
- [ ] **Rollback plan ready:** Know how to stop processes and revert changes

**If ANY checklist item fails → STOP. Resolve before proceeding.**

---

## Roles & Responsibilities

| Role | Responsibilities |
|------|------------------|
| **Drill Operator** | Executes procedures; collects evidence; maintains audit trail; enforces NO-LIVE rules |
| **Peer Reviewer** | Independent verification of drill outputs; checks for live trading risks; signs off on evidence pack |
| **Governance Approver** | Authorizes drill initiation; reviews post-run report; decides on next steps |

**Note:** Roles may be combined in small teams, but separation of duties is recommended for audit integrity.

---

## 5-Step Operator Procedure (Drill Execution)

### Step 1: Environment Setup & Verification (15 min)

**Objective:** Confirm drill-safe environment; no live trading risk.

**Actions:**
1. Activate Python environment: `source venv/bin/activate` (or equivalent)
2. Verify current branch: `git status -sb`
3. Check config environment:
   ```bash
   # Example: confirm SHADOW mode
   grep -i "environment" config/config.toml
   grep -i "live" config/config.toml
   ```
4. Audit for live API keys:
   ```bash
   # Should return NO results for live keys
   grep -rI "api.exchange.live" config/ || echo "OK: No live keys found"
   ```
5. Document findings in `PHASE5_NO_LIVE_EVIDENCE_INDEX.md` (see templates)

**Exit Criteria:**
- [ ] Environment = SHADOW/PAPER/DRILL_ONLY
- [ ] No live API keys detected
- [ ] Evidence logged with timestamp + operator name

---

### Step 2: Pre-Flight Systems Check (20 min)

**Objective:** Validate system health in non-live mode.

**Actions:**
1. Run health check script (if available):
   ```bash
   # Example (adjust to actual script path)
   python scripts/health_check.py --mode=shadow
   ```
2. Check telemetry pipeline:
   ```bash
   # Verify logs are being written
   ls -lht logs/ | head -5
   ```
3. Test data connectivity (paper/shadow market data):
   ```bash
   # Example data fetch test (no live trading)
   python scripts/test_data_feed.py --symbol=BTC-EUR --mode=paper
   ```
4. Capture screenshots/logs as evidence

**Exit Criteria:**
- [ ] All health checks pass (or documented exceptions)
- [ ] Telemetry pipeline active
- [ ] Market data feed operational (paper/shadow)

---

### Step 3: Strategy Dry-Run (30 min)

**Objective:** Execute trading strategy in simulation; collect performance data.

**Actions:**
1. Select test strategy (e.g., MA crossover) + symbol (e.g., BTC-EUR)
2. Prepare config (ensure `mode: shadow` or `mode: paper`):
   ```toml
   # Example snippet (NOT a complete config)
   [environment]
   mode = "shadow"  # or "paper"

   [strategy]
   name = "ma_crossover_drill"
   ```
3. Run backtest or live simulation:
   ```bash
   # Example (adjust to actual command)
   python src/core/engine.py --config=config/drill_test.toml --duration=30m
   ```
4. Monitor logs in real-time:
   ```bash
   tail -f logs/strategy_drill.log
   ```
5. Collect outputs: trades.csv, metrics.json, logs

**Exit Criteria:**
- [ ] Strategy executed without crashes
- [ ] Simulated trades recorded (no real fills)
- [ ] Performance metrics generated
- [ ] Evidence artifacts saved to `results/drill_<timestamp>/`

---

### Step 4: Evidence Pack Assembly (20 min)

**Objective:** Compile audit-ready documentation.

**Actions:**
1. Copy template: `cp docs/ops/templates/phase5_no_live/PHASE5_NO_LIVE_EVIDENCE_INDEX.md results/drill_<timestamp>/EVIDENCE_INDEX.md`
2. Fill in metadata (date, operator, repo SHA, run ID)
3. Add artifact paths:
   - Config files used
   - Log files (system, strategy, audit)
   - Trade data (simulated)
   - Metrics/plots
   - Screenshots (if any)
4. Cross-reference with `PHASE5_NO_LIVE_OPERATOR_CHECKLIST.md` (all items checked)
5. No external links; repo-relative paths only

**Exit Criteria:**
- [ ] Evidence Index complete (all sections filled)
- [ ] All artifacts referenced and accessible
- [ ] NO-LIVE mode documented in Evidence Index header

---

### Step 5: Go/No-Go Assessment (15 min)

**Objective:** Determine drill outcome; document decision.

**Actions:**
1. Copy template: `cp docs/ops/templates/phase5_no_live/PHASE5_NO_LIVE_GO_NO_GO_RECORD.md results/drill_<timestamp>/GO_NO_GO_RECORD.md`
2. Review success criteria:
   - Environment verified as NO-LIVE
   - Strategy executed without errors
   - Evidence pack complete
   - No live trading prohibitions violated
3. Record decision:
   - **GO:** Drill passed; operator competency validated; NO-LIVE readiness confirmed
   - **NO-GO:** Issues identified (list them); remediation plan required
4. Sign & date record (operator + peer reviewer if available)

**Exit Criteria:**
- [ ] Go/No-Go decision documented
- [ ] Rationale provided (especially for NO-GO)
- [ ] Next steps defined (e.g., post-run review, remediation tasks)

**REMINDER: A "GO" decision means the DRILL was successful. It does NOT authorize live trading.**

---

## Evidence Pack Structure

```
results/drill_<timestamp>/
├── EVIDENCE_INDEX.md            # Master index (template: PHASE5_NO_LIVE_EVIDENCE_INDEX.md)
├── GO_NO_GO_RECORD.md           # Decision record (template: PHASE5_NO_LIVE_GO_NO_GO_RECORD.md)
├── OPERATOR_CHECKLIST.md        # Completed checklist (template: PHASE5_NO_LIVE_OPERATOR_CHECKLIST.md)
├── config/
│   └── drill_test.toml          # Config used (confirm NO-LIVE)
├── logs/
│   ├── system.log
│   ├── strategy_drill.log
│   └── audit.log
├── trades/
│   └── simulated_trades.csv     # NO real fills
├── metrics/
│   ├── performance_summary.json
│   └── risk_report.json
└── screenshots/                 # Optional
    └── telemetry_dashboard.png
```

**Archive:** After peer review, compress and archive: `drill_<timestamp>.tar.gz`

---

## Post-Run Review Template

Use `docs/ops/templates/phase5_no_live/PHASE5_NO_LIVE_POST_RUN_REVIEW.md` to conduct debrief:

**Topics to cover:**
1. What went well?
2. What issues arose? (technical, procedural, documentation gaps)
3. Were all NO-LIVE controls effective?
4. Operator confidence level (1-5 scale)
5. Recommendations for next drill or Phase 6 planning
6. Documentation updates needed

**Output:** Post-run review document added to Evidence Pack.

---

## Risks & Controls

| Risk | Impact | Control |
|------|--------|---------|
| Operator accidentally enables live trading | **CRITICAL** | Hard prohibitions enforced; config audits (Steps 1-2); peer review mandatory |
| Live API keys leaked into config | **CRITICAL** | Pre-flight grep audit (Step 1); `.gitignore` for secrets; credential scanning (if tooling available) |
| Incomplete evidence pack | Medium | Template-driven assembly (Step 4); peer review checklist |
| Strategy crash/hang | Low | Timeout configs; monitoring (Step 3); rollback plan in preconditions |
| Misinterpretation of "GO" decision | Medium | Clear definitions (Scope section); NO-LIVE banner repeated in templates |

**Residual Risk:** Despite controls, human error remains possible. Mitigation: mandatory peer review + governance sign-off before any Phase 6 live discussions.

---

## Appendix: Common Failure Modes

### Failure Mode 1: Config Still Shows `mode: live`
**Symptom:** Grep finds "live" in config files  
**Resolution:** Edit config to `mode: shadow` or `mode: paper`; re-run Step 1; document in Evidence Pack

### Failure Mode 2: Strategy Won't Start
**Symptom:** Import errors, missing dependencies, timeout  
**Resolution:** Check Python venv; verify `requirements.txt` installed; review logs; may need environment rebuild  
**Escalation:** If unresolved in 30 min, mark NO-GO and defer

### Failure Mode 3: No Trade Data Generated
**Symptom:** Empty trades.csv after Step 3  
**Resolution:** Check strategy logic (maybe no signals in test window); verify market data feed; extend duration  
**Acceptable:** If system is healthy but no signals, document as "NO SIGNALS" in Evidence Pack (not a failure)

### Failure Mode 4: Peer Reviewer Unavailable
**Symptom:** Cannot get sign-off on Evidence Pack  
**Resolution:** Self-review with extra diligence; document "self-reviewed" in GO_NO_GO_RECORD; seek asynchronous review post-drill  
**Note:** Independent review strongly preferred for audit integrity

### Failure Mode 5: Git Conflicts / Branch Issues
**Symptom:** Cannot commit evidence or templates  
**Resolution:** Stash changes; pull latest; re-apply; commit with clear message (e.g., "docs: WP5A Phase 5 NO-LIVE drill pack artifacts")  
**Prevention:** Run pre-flight script (as provided) before starting drill

---

## References (Internal Only)

- **Governance Policy:** EXAMPLE: AI autonomy decision framework (governance policies)
- **Ops Runbooks:** `docs/ops/README.md` (navigation hub)
- **Config Examples:** `config/shadow_config.toml`, `config/shadow_pipeline_example.toml`
- **Testing Guide:** `tests/README.md` (not drill-specific, but useful for troubleshooting)
- **Timeout Triage:** `docs/ops/CURSOR_TIMEOUT_TRIAGE.md` (if system hangs during drill)

**External References:** None required for NO-LIVE drill. Any live trading documentation is out of scope.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | AI Assistant | Initial NO-LIVE drill pack creation for WP5A |

---

**END OF WP5A PHASE 5 NO-LIVE DRILL PACK**

**REMINDER: This drill does NOT authorize live trading. All operations must remain in SHADOW/PAPER/DRILL_ONLY mode.**
