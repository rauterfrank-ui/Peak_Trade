# Phase 4E — Stability Monitoring Checklist (Weeks 1–3)

**Version:** 1.0.0  
**Created:** 2026-01-11  
**Baseline Run:** 20902441555  
**Owner:** Operator  

---

## Purpose

Confirm ongoing stability of Phase 4E validator-report artifacts and CI behavior on `main` after PR #656 merge and docs audit trail completion (PR #658).

## Scope

**Workflow:** `L4 Critic Replay Determinism v2` (`.github/workflows/l4_critic_replay_determinism_v2.yml`)

**Artifacts:**
- **Normalized (canonical):** `validator_report.normalized.json`, `validator_report.normalized.md`
- **Legacy (compat):** `validator_report.json`

**Guardrails:**
- No changes to trading logic or live configs
- Monitoring only (no code modifications)
- Documentation of observed behavior

---

## Known Evidence Anchors

| Evidence | Value | Date | Status |
|----------|-------|------|--------|
| **Implementation PR** | #656 | 2026-01-11 | ✅ MERGED |
| **Merge Commit** | 8574c672507d54a127451f786b2cf12edd917ba3 | 2026-01-11T21:50:35Z | ✅ |
| **Post-Merge Run (Baseline)** | 20902441555 | 2026-01-11T21:50:39Z | ✅ SUCCESS |
| **Proof Run** | 20902058406 | 2026-01-11T21:20:21Z | ✅ SUCCESS |
| **Docs Audit PR** | #658 | 2026-01-11T22:27:48Z | ✅ MERGED |
| **Schema Version** | 1.0.0 | - | ✅ Verified |
| **Baseline Hash** | 4de2937bd14a8556e7f3611d2270d31e359bc38b1e37b62c4b3ab75c7c48a59b | - | ✅ |

---

## Monitoring Cadence (Fixed Dates)

**Baseline (Day 0):** 2026-01-11

| Checkpoint | Date | Status | Notes |
|------------|------|--------|-------|
| **Day 0 (Baseline)** | 2026-01-11 | ✅ Complete | Run 20902441555, Schema 1.0.0, PASS |
| **Day 3** | 2026-01-14 | ⏳ Pending | Check CI run consistency |
| **Day 7** | 2026-01-18 | ⏳ Pending | Review weekly CI run |
| **Day 14** | 2026-01-25 | ⏳ Pending | Review 2nd weekly CI run |
| **Day 21** | 2026-02-01 | ⏳ Pending | Final stability check + closeout |

---

## Quick Commands (Operator-Safe)

### A) Check Recent Workflow Runs (Success Consistency)

```bash
# List last 10 runs with status
gh run list --workflow l4_critic_replay_determinism_v2.yml --limit 10
```

**Expected:** Recent runs on `main` should show SUCCESS (✓)

---

### B) Get Latest Successful Run ID

```bash
# Find most recent successful run
RUN_ID="$(gh api repos/rauterfrank-ui/Peak_Trade/actions/workflows/l4_critic_replay_determinism_v2.yml/runs \
  --jq '[.workflow_runs[] | select(.conclusion=="success")][0].id')"
echo "Latest successful run: $RUN_ID"
```

**Expected:** Should return a run ID (numeric)

---

### C) View Run Details

```bash
# View run metadata
gh run view "$RUN_ID" --json status,conclusion,createdAt,event,headBranch,headSha

# Human-readable summary
gh run view "$RUN_ID"
```

**Expected:**
- `status`: "completed"
- `conclusion`: "success"
- `event`: "push" (for main branch runs)
- `headBranch`: "main"

---

### D) Download Artifacts (If New Run Available)

```bash
# Download to timestamped directory
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
gh run download "$RUN_ID" -D "./artifacts_check_${TIMESTAMP}"

# Verify download
find "./artifacts_check_${TIMESTAMP}" -type f -name "validator_report*.json" -o -name "validator_report*.md"
```

**Expected Files:**
- `validator-report-normalized-${RUN_ID}&#47;validator_report.normalized.json`
- `validator-report-normalized-${RUN_ID}&#47;validator_report.normalized.md`
- `validator-report-legacy-${RUN_ID}&#47;validator_report.json`

---

### E) Verify Schema Version (Must Be 1.0.0)

```bash
# Extract schema version
SCHEMA_VERSION="$(jq -r '.schema_version // .schemaVersion // empty' \
  ./artifacts_check_*/validator-report-normalized-*/validator_report.normalized.json | head -n 1)"
echo "Schema Version: $SCHEMA_VERSION"

# Verify
if [ "$SCHEMA_VERSION" = "1.0.0" ]; then
  echo "✅ Schema version correct"
else
  echo "❌ Schema version mismatch! Expected 1.0.0, got: $SCHEMA_VERSION"
fi
```

**Expected:** `1.0.0`

---

### F) Verify Determinism Result (Must Be PASS)

```bash
# Extract result
RESULT="$(jq -r '.result' \
  ./artifacts_check_*/validator-report-normalized-*/validator_report.normalized.json | head -n 1)"
echo "Determinism Result: $RESULT"

# Verify
if [ "$RESULT" = "PASS" ]; then
  echo "✅ Determinism check passed"
else
  echo "❌ Determinism check failed! Got: $RESULT"
fi
```

**Expected:** `PASS`

---

### G) Verify Hash Match (Baseline == Candidate)

```bash
# Extract hash match status
HASH_MATCH="$(jq -r '.checks[0].metrics | "\(.baseline_hash == .candidate_hash)"' \
  ./artifacts_check_*/validator-report-normalized-*/validator_report.normalized.json | head -n 1)"
echo "Hash Match: $HASH_MATCH"

# Show hashes
jq -r '.checks[0].metrics | "Baseline:  \(.baseline_hash)\nCandidate: \(.candidate_hash)"' \
  ./artifacts_check_*/validator-report-normalized-*/validator_report.normalized.json | head -n 2

# Verify
if [ "$HASH_MATCH" = "true" ]; then
  echo "✅ Hashes match"
else
  echo "❌ Hash mismatch!"
fi
```

**Expected:** `true`

---

### H) Verify Legacy Compatibility

```bash
# Check legacy format still works
LEGACY_RESULT="$(jq -r '.result.equal // empty' \
  ./artifacts_check_*/validator-report-legacy-*/validator_report.json | head -n 1)"
echo "Legacy Result: $LEGACY_RESULT"

# Verify
if [ "$LEGACY_RESULT" = "true" ]; then
  echo "✅ Legacy format compatible"
else
  echo "⚠️  Legacy format result: $LEGACY_RESULT"
fi
```

**Expected:** `true`

---

### I) Compare Run to Baseline

```bash
# Baseline info (Day 0)
echo "=== BASELINE (Day 0) ==="
echo "Run ID: 20902441555"
echo "Date: 2026-01-11T21:50:39Z"
echo "Schema: 1.0.0"
echo "Result: PASS"
echo "Hash: 4de2937bd14a8556e7f3611d2270d31e359bc38b1e37b62c4b3ab75c7c48a59b"

echo ""
echo "=== CURRENT RUN ==="
echo "Run ID: $RUN_ID"
gh run view "$RUN_ID" --json createdAt --jq '"Date: \(.createdAt)"'
jq -r '"Schema: \(.schema_version)\nResult: \(.result)\nHash: \(.checks[0].metrics.baseline_hash)"' \
  ./artifacts_check_*/validator-report-normalized-*/validator_report.normalized.json | head -n 3
```

---

## Success Criteria (Per Checkpoint)

Each monitoring checkpoint (Day 3, 7, 14, 21) should verify:

| Criterion | Expected Value | Command Reference |
|-----------|----------------|-------------------|
| **Workflow Status** | SUCCESS (✓) | Section A |
| **Schema Version** | 1.0.0 | Section E |
| **Determinism Result** | PASS | Section F |
| **Hash Match** | true | Section G |
| **Legacy Compat** | true | Section H |
| **Artifacts Present** | 3 files | Section D |

**All criteria must be met** for checkpoint to be marked as ✅.

---

## Alert Conditions

Trigger escalation if any of the following are observed:

| Alert | Condition | Action |
|-------|-----------|--------|
| **🔴 Workflow Failure** | `conclusion != "success"` | Investigate logs immediately |
| **🔴 Schema Drift** | `schema_version != "1.0.0"` | CRITICAL - Schema regression |
| **🔴 Determinism Failure** | `result != "PASS"` | Investigate hash mismatch |
| **🟡 Hash Mismatch** | `baseline_hash != candidate_hash` | Review replay logic |
| **🟡 Legacy Break** | `legacy result != true` | Check backward compat |
| **🟡 Missing Artifacts** | < 3 files | Workflow artifact upload issue |

---

## Checkpoint Execution Guide

### Day 3 (2026-01-14)

**Goal:** Verify consistency 3 days after baseline

**Steps:**
1. Run commands A, B, C (get latest successful run)
2. Run command D (download artifacts if new run available)
3. Run commands E, F, G, H (verify all criteria)
4. Run command I (compare to baseline)
5. Document results in **Day 3 Results** section below

**Expected:** Same schema version (1.0.0), PASS result, hash match

---

### Day 7 (2026-01-18)

**Goal:** Review first weekly CI run

**Steps:**
1. Run commands A, B, C (get latest successful run)
2. Check if new run since Day 3 (compare run IDs)
3. If new run: execute D, E, F, G, H, I
4. If no new run: note "No new CI run since Day 3" and mark OK
5. Document results in **Day 7 Results** section below

**Expected:** Weekly run triggered, all criteria met

---

### Day 14 (2026-01-25)

**Goal:** Review 2nd weekly CI run

**Steps:**
1. Run commands A, B, C (get latest successful run)
2. Check if new run since Day 7 (compare run IDs)
3. If new run: execute D, E, F, G, H, I
4. Document results in **Day 14 Results** section below

**Expected:** 2nd weekly run triggered, all criteria met, stability confirmed

---

### Day 21 (2026-02-01)

**Goal:** Final stability check + monitoring closeout

**Steps:**
1. Run commands A, B, C (get latest successful run)
2. Check if new run since Day 14 (compare run IDs)
3. If new run: execute D, E, F, G, H, I
4. Review all checkpoint results (Day 0, 3, 7, 14, 21)
5. If all checkpoints ✅: declare Phase 4E **STABLE**
6. Document results in **Day 21 Results** section below
7. Create closeout summary document

**Expected:** 3 weeks of consistent behavior, Phase 4E declared stable

---

## Results Log

### Day 0 (Baseline) — 2026-01-11

**Status:** ✅ **COMPLETE**

| Metric | Value |
|--------|-------|
| **Run ID** | 20902441555 |
| **Date** | 2026-01-11T21:50:39Z |
| **Event** | push (main) |
| **Conclusion** | success |
| **Schema Version** | 1.0.0 ✅ |
| **Determinism Result** | PASS ✅ |
| **Hash Match** | true ✅ |
| **Legacy Compat** | true ✅ |
| **Artifacts** | 3 files ✅ |

**Notes:**
- Baseline established after PR #656 merge
- All success criteria met
- Artifacts downloaded to `artifacts_main_latest/`

---

### Day 3 — 2026-01-14

**Status:** ⏳ **PENDING**

| Metric | Value |
|--------|-------|
| **Run ID** | _TBD_ |
| **Date** | _TBD_ |
| **Event** | _TBD_ |
| **Conclusion** | _TBD_ |
| **Schema Version** | _TBD_ |
| **Determinism Result** | _TBD_ |
| **Hash Match** | _TBD_ |
| **Legacy Compat** | _TBD_ |
| **Artifacts** | _TBD_ |

**Notes:**
- _To be completed on 2026-01-14_

---

### Day 7 — 2026-01-18

**Status:** ⏳ **PENDING**

| Metric | Value |
|--------|-------|
| **Run ID** | _TBD_ |
| **Date** | _TBD_ |
| **Event** | _TBD_ |
| **Conclusion** | _TBD_ |
| **Schema Version** | _TBD_ |
| **Determinism Result** | _TBD_ |
| **Hash Match** | _TBD_ |
| **Legacy Compat** | _TBD_ |
| **Artifacts** | _TBD_ |

**Notes:**
- _To be completed on 2026-01-18_

---

### Day 14 — 2026-01-25

**Status:** ⏳ **PENDING**

| Metric | Value |
|--------|-------|
| **Run ID** | _TBD_ |
| **Date** | _TBD_ |
| **Event** | _TBD_ |
| **Conclusion** | _TBD_ |
| **Schema Version** | _TBD_ |
| **Determinism Result** | _TBD_ |
| **Hash Match** | _TBD_ |
| **Legacy Compat** | _TBD_ |
| **Artifacts** | _TBD_ |

**Notes:**
- _To be completed on 2026-01-25_

---

### Day 21 — 2026-02-01

**Status:** ⏳ **PENDING**

| Metric | Value |
|--------|-------|
| **Run ID** | _TBD_ |
| **Date** | _TBD_ |
| **Event** | _TBD_ |
| **Conclusion** | _TBD_ |
| **Schema Version** | _TBD_ |
| **Determinism Result** | _TBD_ |
| **Hash Match** | _TBD_ |
| **Legacy Compat** | _TBD_ |
| **Artifacts** | _TBD_ |

**Notes:**
- _To be completed on 2026-02-01_
- _Prepare closeout summary if all checkpoints ✅_

---

## Escalation Paths

### If Schema Version Drifts (Not 1.0.0)

**CRITICAL** — Schema regression detected

1. **Immediate:**
   - Capture run ID and artifacts
   - Review recent PRs merged to main
   - Check if `validator_report.py` or schema definitions modified

2. **Investigation:**
   ```bash
   # Check recent commits affecting validator report
   git log --oneline --since="2026-01-11" -- src/ai_orchestration/validators/

   # Review schema definition
   grep -r "schema_version" src/ai_orchestration/
   ```

3. **Mitigation:**
   - If accidental regression: revert offending commit
   - If intentional: update docs and monitoring baseline

---

### If Determinism Check Fails (Result != PASS)

**HIGH** — Determinism contract violated

1. **Immediate:**
   - Capture run ID, artifacts, and logs
   - Check if baseline hash or candidate hash is empty/malformed
   - Review replay logic for changes

2. **Investigation:**
   ```bash
   # Check recent changes to replay logic
   git log --oneline --since="2026-01-11" -- src/ai_orchestration/critics/l4_critic_replay.py

   # Download and compare failed run artifacts
   gh run download "$RUN_ID" -D "./artifacts_failed_${RUN_ID}"
   jq '.' ./artifacts_failed_*/validator-report-normalized-*/validator_report.normalized.json
   ```

3. **Mitigation:**
   - Investigate root cause (code change, data drift, environment)
   - If bug: create issue and PR to fix
   - If expected behavior change: update determinism contract

---

### If Workflow Fails (conclusion != success)

**HIGH** — CI stability issue

1. **Immediate:**
   - View failed run logs
   ```bash
   gh run view "$RUN_ID" --log-failed
   ```

2. **Investigation:**
   - Check for infrastructure issues (GitHub Actions status)
   - Review error messages in logs
   - Compare to last successful run

3. **Mitigation:**
   - If transient: re-run workflow
   - If persistent: investigate root cause and create fix PR

---

### If Legacy Compatibility Breaks

**MEDIUM** — Backward compatibility issue

1. **Immediate:**
   - Capture legacy artifact
   - Check if `validator_report.json` is malformed or empty

2. **Investigation:**
   ```bash
   # Check recent changes to legacy writer
   git log --oneline --since="2026-01-11" -- src/ai_orchestration/validators/*legacy*

   # Inspect legacy artifact
   jq '.' ./artifacts_check_*/validator-report-legacy-*/validator_report.json
   ```

3. **Mitigation:**
   - If legacy writer broken: fix and issue PR
   - If intentional deprecation: update docs and notify consumers

---

## Closeout Criteria (Day 21)

Phase 4E monitoring is considered **COMPLETE** if:

- [x] **Day 0 (Baseline):** ✅ Complete (2026-01-11)
- [ ] **Day 3:** ✅ All success criteria met
- [ ] **Day 7:** ✅ All success criteria met
- [ ] **Day 14:** ✅ All success criteria met
- [ ] **Day 21:** ✅ All success criteria met
- [ ] **No Critical Alerts:** Zero schema drifts, determinism failures, or workflow failures
- [ ] **Consistency:** Schema version 1.0.0 maintained across all checkpoints
- [ ] **Legacy Compat:** Backward compatibility maintained
- [ ] **Closeout Summary:** Final report documenting 3-week stability

**If all criteria met:**
- Declare Phase 4E **STABLE** ✅
- Archive monitoring artifacts
- Update Phase 4E documentation with "Stability Confirmed" status
- Close monitoring checklist

**If criteria NOT met:**
- Extend monitoring by 1 week
- Address root causes
- Re-assess stability

---

## References

### GitHub

- **PR #656 (Implementation):** https://github.com/rauterfrank-ui/Peak_Trade/pull/656
- **PR #658 (Audit Docs):** https://github.com/rauterfrank-ui/Peak_Trade/pull/658
- **Baseline CI Run:** https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20902441555
- **Proof CI Run:** https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20902058406
- **Workflow File:** `.github/workflows/l4_critic_replay_determinism_v2.yml`

### Local Documentation

- **Merge Log:** `docs/ops/PR_656_MERGE_LOG.md`
- **Audit Report:** `docs/ops/reports/2026-01-11_PHASE4E_POST_MERGE_AUDIT.md`
- **Phase 4E Spec:** `docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md`
- **Quickstart:** `docs/governance/ai_autonomy/PHASE4E_QUICKSTART.md`

### Baseline Artifacts

- **Local Path:** `./artifacts_main_latest/`
- **Normalized:** `validator-report-normalized-20902441555&#47;`
- **Legacy:** `validator-report-legacy-20902441555&#47;`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-11 | Initial checklist created with Day 0 baseline |

---

**Operator:** _Your Name_  
**Last Updated:** 2026-01-11  
**Status:** Active Monitoring (Weeks 1-3)
