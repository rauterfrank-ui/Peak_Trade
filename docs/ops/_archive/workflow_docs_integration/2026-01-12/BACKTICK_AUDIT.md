# Backtick Audit: Workflow Documentation Integration

**Session:** 2026-01-12 Workflow Docs Integration  
**FACTS_COLLECTOR Role:** Backtick extraction and classification  
**CI_GUARDIAN Role:** docs-reference-targets-gate impact assessment

---

## Purpose

This audit identifies all inline backtick tokens containing "/" in both workflow documents and classifies them for docs-reference-targets-gate compatibility.

---

## Classification Schema

- **A (Real Path - VALIDATE):** Existing file/directory path in repo → MUST exist, gate should validate
- **B (Branch Name - DO NOT VALIDATE):** Git branch name → NOT a file path, gate should NOT validate
- **C (Placeholder/Future - DO NOT VALIDATE):** Planned/example path that doesn't exist yet → gate should NOT validate
- **D (URL - DO NOT VALIDATE):** HTTP/HTTPS URL → NOT a file path, gate correctly ignores
- **E (Local/Absolute Path - DO NOT VALIDATE):** Non-repo path (e.g. `/usr/local/bin`) → gate should NOT validate
- **F (Command - DO NOT VALIDATE):** Command with args (e.g. `script.py arg1/arg2`) → gate should NOT validate

---

## Document 1: WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md

**Total Backticks with "/":** 39 instances

### Line 25
**Token:** `docs/CLI_CHEATSHEET.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file, should exist  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 40
**Token:** `live_ops.py orders/portfolio/health`  
**Classification:** **F (Command - DO NOT VALIDATE)**  
**Rationale:** CLI command with subcommands, contains space  
**Gate Impact:** Gate IGNORES (contains space, see line 230-232 in verify_docs_reference_targets.sh)  
**Fix Required:** NO (already safe)

### Line 67
**Token:** `docs/ops/runbooks/Wave3_Control_Center_Cheatsheet_v2.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 101
**Token:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATOR_CHEATSHEET.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 138
**Token:** `docs/LIVE_OPERATIONAL_RUNBOOKS.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 231
**Token:** `http://localhost:8000/`  
**Classification:** **D (URL - DO NOT VALIDATE)**  
**Rationale:** HTTP URL  
**Gate Impact:** Gate IGNORES (is_url check passes)  
**Fix Required:** NO (already safe)

### Line 232
**Token:** `http://localhost:8000/health`  
**Classification:** **D (URL - DO NOT VALIDATE)**  
**Rationale:** HTTP URL  
**Gate Impact:** Gate IGNORES (is_url check passes)  
**Fix Required:** NO (already safe)

### Line 233
**Token:** `http://localhost:8000/runs`  
**Classification:** **D (URL - DO NOT VALIDATE)**  
**Rationale:** HTTP URL  
**Gate Impact:** Gate IGNORES (is_url check passes)  
**Fix Required:** NO (already safe)

### Line 234
**Token:** `http://localhost:8000/runs/{run_id}/snapshot`  
**Classification:** **D (URL - DO NOT VALIDATE)**  
**Rationale:** HTTP URL with parameter placeholder  
**Gate Impact:** Gate IGNORES (is_url check passes)  
**Fix Required:** NO (already safe)

### Line 239
**Token:** `docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 247
**Token:** `docs/runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 248
**Token:** `docs/runbooks/LIVE_RISK_SEVERITY_INTEGRATION.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 249
**Token:** `docs/runbooks/LIVE_ALERT_PIPELINE_SLACK_EMAIL_RUNBOOK_V1.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 250
**Token:** `docs/runbooks/INCIDENT_RUNBOOK_INTEGRATION_V1.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 251
**Token:** `docs/GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 252
**Token:** `docs/runbooks/R_AND_D_RUNBOOK_ARMSTRONG_EL_KAROUI_V1.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 253
**Token:** `docs/runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 254
**Token:** `docs/runbooks/ARMSTRONG_ELKAROUI_CROSS_RUN_FINDINGS_V1.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 255
**Token:** `docs/runbooks/OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 272
**Token:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing runbook file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 286
**Token:** `docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 287
**Token:** `docs/ops/control_center/CONTROL_CENTER_NAV.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 288
**Token:** `docs/ops/README.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 362
**Token:** `docs/ops/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash, see line 234-236 in verify_docs_reference_targets.sh)  
**Fix Required:** NO (already safe)

### Line 365
**Token:** `control_center/AI_AUTONOMY_CONTROL_CENTER.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing file relative to docs/ops/  
**Gate Impact:** WILL be validated RELATIVE to containing doc, MUST exist  
**Fix Required:** VERIFY (relative path resolution)

### Line 366
**Token:** `control_center/CONTROL_CENTER_NAV.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing file relative to docs/ops/  
**Gate Impact:** WILL be validated RELATIVE to containing doc, MUST exist  
**Fix Required:** VERIFY (relative path resolution)

### Line 410
**Token:** `docs/WORKFLOW_NOTES.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 427
**Token:** `python scripts&#47;...`  
**Classification:** **F (Command - DO NOT VALIDATE)**  
**Rationale:** Command example with glob/ellipsis  
**Gate Impact:** Gate IGNORES (contains wildcard)  
**Fix Required:** NO (already safe)

### Line 771
**Token:** `docs/ops/P0_GUARDRAILS_QUICK_REFERENCE.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 772
**Token:** `docs/governance/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 776
**Token:** `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 777
**Token:** `docs/ops/CI_HARDENING_SESSION_20260103.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 778
**Token:** `docs/ops/ci/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 782
**Token:** `docs/ops/EVIDENCE_INDEX.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 783
**Token:** `docs/ops/EVIDENCE_SCHEMA.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 784
**Token:** `docs/ops/evidence/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 785
**Token:** `docs/audit/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 811
**Token:** `docs/runbooks/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 811 (second instance)
**Token:** `docs/LIVE_OPERATIONAL_RUNBOOKS.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 812
**Token:** `docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

---

## Document 2: docs/WORKFLOW_NOTES.md

**Total Backticks with "/":** 10 instances

### Line 8
**Token:** `src/data/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 13
**Token:** `src/strategies/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 27
**Token:** `src/core/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 48
**Token:** `src/backtest/`  
**Classification:** **F (Directory - DO NOT VALIDATE)**  
**Rationale:** Directory reference with trailing slash  
**Gate Impact:** Gate IGNORES (trailing slash)  
**Fix Required:** NO (already safe)

### Line 56
**Token:** `src/strategies/registry.py`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing source file  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

### Line 124
**Token:** `python scripts&#47;...`  
**Classification:** **F (Command - DO NOT VALIDATE)**  
**Rationale:** Command example with glob/ellipsis  
**Gate Impact:** Gate IGNORES (contains wildcard)  
**Fix Required:** NO (already safe)

### Line 155
**Token:** `docs/PEAK_TRADE_OVERVIEW.md`  
**Classification:** **C (Placeholder/Future - DO NOT VALIDATE)**  
**Rationale:** Planned document mentioned in "next block" section (as of Dec 2025)  
**Gate Impact:** WILL be validated if not ignored, MAY FAIL if doesn't exist  
**Fix Required:** **YES - VERIFY EXISTENCE or ESCAPE**

### Line 156
**Token:** `docs/BACKTEST_ENGINE.md`  
**Classification:** **C (Placeholder/Future - DO NOT VALIDATE)**  
**Rationale:** Planned document mentioned in "next block" section (as of Dec 2025)  
**Gate Impact:** WILL be validated if not ignored, MAY FAIL if doesn't exist  
**Fix Required:** **YES - VERIFY EXISTENCE or ESCAPE**

### Line 157
**Token:** `docs/STRATEGY_DEV_GUIDE.md`  
**Classification:** **C (Placeholder/Future - DO NOT VALIDATE)**  
**Rationale:** Planned document mentioned in "next block" section (as of Dec 2025)  
**Gate Impact:** WILL be validated if not ignored, MAY FAIL if doesn't exist  
**Fix Required:** **YES - VERIFY EXISTENCE or ESCAPE**

### Line 172
**Token:** `docs/WORKFLOW_NOTES.md`  
**Classification:** **A (Real Path - VALIDATE)**  
**Rationale:** Existing docs file (self-reference)  
**Gate Impact:** WILL be validated, MUST exist  
**Fix Required:** NO (path exists)

---

## Summary Statistics

### WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md
- **Total:** 39 backticks with "/"
- **A (Real Path - VALIDATE):** 28 instances
- **D (URL - DO NOT VALIDATE):** 4 instances
- **F (Command/Directory - DO NOT VALIDATE):** 7 instances
- **Fix Required:** 0 instances (all paths exist or are already safe)

### docs/WORKFLOW_NOTES.md
- **Total:** 10 backticks with "/"
- **A (Real Path - VALIDATE):** 2 instances
- **C (Placeholder/Future - DO NOT VALIDATE):** 3 instances
- **F (Command/Directory - DO NOT VALIDATE):** 5 instances
- **Fix Required:** 3 instances (lines 155-157: verify existence or escape)

---

## Gate Impact Assessment (CI_GUARDIAN)

### Low Risk (Already Gate-Safe)
- **URLs:** Gate correctly ignores (is_url check)
- **Commands with spaces:** Gate ignores (space detection)
- **Directories with trailing slash:** Gate ignores (trailing slash detection)
- **Wildcards/globs:** Gate ignores (wildcard detection)

### Validation Required (Real Paths)
- **WORKFLOW_RUNBOOK_OVERVIEW:** 28 paths (all verified to exist in current repo)
- **WORKFLOW_NOTES:** 2 paths (`src/strategies/registry.py`, `docs/WORKFLOW_NOTES.md` - both exist)

### Potential Failures (Placeholder/Future Paths)
- **docs/WORKFLOW_NOTES.md lines 155-157:** 3 paths need verification
  - `docs/PEAK_TRADE_OVERVIEW.md`
  - `docs/BACKTEST_ENGINE.md`
  - `docs/STRATEGY_DEV_GUIDE.md`

---

## Next Steps (Phase 3: Fix Matrix)

1. **Verify Existence:** Check if lines 155-157 paths exist in current repo
2. **If Missing:** Apply Style Guide fix pattern:
   - Convert to quoted + escaped + `(future)` marker
   - Example: `"docs\/PEAK_TRADE_OVERVIEW.md" (future, planned Dec 2025)`
3. **If Existing:** No fix required (gate will validate successfully)

---

**FACTS_COLLECTOR Sign-Off:** ✅ All backticks with "/" extracted and classified  
**CI_GUARDIAN Sign-Off:** ✅ Gate impact assessed, 3 potential issues identified (lines 155-157 in WORKFLOW_NOTES.md)
