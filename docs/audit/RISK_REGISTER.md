# Peak_Trade Risk Register

**Audit Baseline:** `fb829340dbb764a75c975d5bf413a4edb5e47107`  
**Last Updated:** 2025-12-30

---

## Purpose

This Risk Register documents identified risks (distinct from findings) that may impact live trading operations. Each risk includes:
- Likelihood and impact assessment
- Mitigation strategies
- Detection mechanisms
- Ownership and review dates

**Note:** This register tracks **inherent risks** in the system design and operations, not individual code/config findings (those go in `findings&#47;FND-XXXX.md`).

---

## Risk Assessment Matrix

| Likelihood / Impact | Low | Medium | High |
|---------------------|-----|--------|------|
| **High** | Medium | High | Critical |
| **Medium** | Low | Medium | High |
| **Low** | Low | Low | Medium |

---

## Active Risks

### RISK-001: Exchange Connectivity Loss

- **Category:** Operations / External Dependency
- **Description:** Loss of connectivity to exchange API during active trading session
- **Likelihood:** Medium (exchanges have uptime > 99% but outages happen)
- **Impact:** High (unable to close positions, monitor market, or respond to adverse moves)
- **Mitigation:**
  - Multiple connectivity paths (primary + fallback)
  - Pre-defined position limits to cap exposure
  - Automated circuit breaker on stale data detection
  - Manual emergency procedures documented
- **Detection:**
  - Heartbeat monitoring on WebSocket connections
  - REST API health checks every 30s
  - Alert on consecutive failed requests
- **Owner:** [TBD]
- **Status:** Active
- **Review Date:** [TBD]
- **Related Findings:** [TBD]

---

### RISK-002: Market Data Quality Degradation

- **Category:** Data Pipeline
- **Description:** Stale, incorrect, or missing market data feeds strategy with bad signals
- **Likelihood:** Medium
- **Impact:** High (bad signals → bad trades → loss)
- **Mitigation:**
  - Staleness checks on all market data before use
  - Cross-validation with multiple data sources where available
  - Anomaly detection on price moves (circuit breaker on outliers)
  - Manual_only mode as default (requires explicit human approval for live trades)
- **Detection:**
  - Timestamp validation on every tick
  - Sanity checks on price ranges
  - Monitoring dashboards with data quality metrics
- **Owner:** [TBD]
- **Status:** Active
- **Review Date:** [TBD]
- **Related Findings:** [TBD]

---

### RISK-003: Strategy Logic Bug (Undetected)

- **Category:** Strategy / Code Quality
- **Description:** Undiscovered bug in strategy logic leads to unintended trading behavior
- **Likelihood:** Medium (despite testing, edge cases may exist)
- **Impact:** High (could generate large unwanted positions)
- **Mitigation:**
  - Comprehensive backtest validation with multiple market regimes
  - Shadow mode testing with live data but no real orders
  - Bounded-auto mode with strict position limits initially
  - Continuous monitoring of strategy behavior vs. expected patterns
  - Kill switch for immediate halt
- **Detection:**
  - Anomaly detection on trade frequency, size, PnL
  - Daily reconciliation of positions vs. expected
  - Operator monitoring dashboards
- **Owner:** [TBD]
- **Status:** Active
- **Review Date:** [TBD]
- **Related Findings:** [TBD]

---

### RISK-004: Risk Limits Misconfiguration

- **Category:** Configuration / Governance
- **Description:** Risk limits set incorrectly (too loose or contradictory) allowing excessive exposure
- **Likelihood:** Low (with proper review processes)
- **Impact:** High (defeats purpose of risk management)
- **Mitigation:**
  - Config validation scripts (detect contradictions, missing required fields)
  - Mandatory peer review of all risk config changes
  - Dry-run validation before applying to live
  - Version control with audit trail
- **Detection:**
  - Config schema validation on load
  - Automated alerts on config changes
  - Regular audits of active limits vs. policy
- **Owner:** [TBD]
- **Status:** Active
- **Review Date:** [TBD]
- **Related Findings:** [TBD]

---

### RISK-005: Secrets Exposure

- **Category:** Security
- **Description:** API keys, private keys, or other secrets exposed via logs, repo, or outputs
- **Likelihood:** Low (with proper controls)
- **Impact:** Critical (unauthorized trading, theft, reputational damage)
- **Mitigation:**
  - No secrets in version control (enforced via .gitignore + pre-commit hooks)
  - Secrets loaded from environment or secure vault only
  - Logging policy: never log keys, tokens, or credentials
  - Regular secrets scanning (gitleaks, detect-secrets)
- **Detection:**
  - Automated secrets scanning in CI
  - Manual code review
  - Periodic security audits
- **Owner:** [TBD]
- **Status:** Active
- **Review Date:** [TBD]
- **Related Findings:** [TBD]

---

### RISK-006: Human Error in Operations

- **Category:** Operations / Human Factors
- **Description:** Operator makes configuration or deployment error leading to unintended behavior
- **Likelihood:** Medium (humans make mistakes)
- **Impact:** High (depends on nature of error)
- **Mitigation:**
  - Runbooks with step-by-step procedures
  - Dry-run/validation steps before live changes
  - Dual-approval for critical operations
  - Audit logging of all operator actions
  - Regular training and drills
- **Detection:**
  - Post-change validation checks
  - Anomaly detection on system behavior
  - Peer review of logs
- **Owner:** [TBD]
- **Status:** Active
- **Review Date:** [TBD]
- **Related Findings:** [TBD]

---

### RISK-007: Dependency Supply Chain Attack

- **Category:** Security / Dependencies
- **Description:** Malicious code introduced via compromised third-party package
- **Likelihood:** Low
- **Impact:** High (could exfiltrate data, manipulate trades)
- **Mitigation:**
  - Dependency pinning with lockfile (uv.lock)
  - Regular vulnerability scanning (pip-audit, safety)
  - Minimize dependencies (review necessity)
  - Vendor critical dependencies if feasible
- **Detection:**
  - Automated dependency scanning in CI
  - Behavioral monitoring for anomalies
  - Security advisories monitoring
- **Owner:** [TBD]
- **Status:** Active
- **Review Date:** [TBD]
- **Related Findings:** [TBD]

---

## Retired/Closed Risks

[To be populated when risks are mitigated or no longer applicable]

---

## Risk Review Schedule

- **Frequency:** Monthly during live operations, or after any significant incident
- **Next Review:** [TBD]
- **Owner:** [TBD]

---

## Notes

- This register is a living document and should be updated as new risks are identified
- Risks with Critical severity require immediate mitigation or explicit acceptance by senior stakeholders
- All risk acceptances must be documented with justification and compensating controls
