# Policy Critic Status

**Current Phase:** G4 - Real-world Telemetry Collection  
**Last Updated:** 2025-12-12  
**Status:** ✅ Production Ready

---

## Implementation Progress

### ✅ Completed Phases

- **G1 (Charter):** LLM Policy Critic Charter defined
- **G2 (Core Implementation):** PolicyCritic engine + rules + packs implemented
- **G3 (Validation):**
  - G3.5: 5 synthetic cycles tested
  - G3.6: UX improvements + tuning based on cycle results
- **G3.7 (CI Integration):** GitHub Actions workflow deployed

### 🔄 Current Phase: G4 - Telemetry Collection

**Goal:** Collect data from 10-20 real PRs to validate false positive rate < 10%

**Resources:**
- Workflow Guide: `docs/governance/POLICY_CRITIC_G4_TELEMETRY_WORKFLOW.md`
- Telemetry Log: `docs/governance/POLICY_CRITIC_TELEMETRY_G4.md`
- Tuning Log: `docs/governance/POLICY_PACK_TUNING_LOG.md`

**Exit Criteria:**
- [ ] 10-20 PRs logged with classifications
- [ ] False Positive Rate < 10%
- [ ] At least 1 real BLOCK scenario observed
- [ ] Change Set 2 created or "no changes needed" documented

### 📋 Future Phases

- **G5:** LLM-assisted rule suggestions (optional)
- **G6:** Auto-apply for PASS cases (optional)

---

## Current Configuration

### Active Rules (7 total)

1. **NoSecretsRule** (BLOCK) - Detects API keys, credentials
2. **NoLiveUnlockRule** (BLOCK) - Prevents live mode unlocks without approval
3. **ExecutionEndpointTouchRule** (WARN/BLOCK) - Monitors execution code changes
4. **RiskLimitRaiseRule** (WARN/BLOCK) - Requires justification for risk limit changes
5. **MissingTestPlanRule** (WARN) - Enforces test plans for critical changes
6. **StrategyTouchWithoutTestRule** (WARN) - Requires tests for strategy changes
7. **ConfigMismatchRule** (INFO) - Detects live/paper config inconsistencies

### Policy Packs

- **ci.yml** - Applied to all PRs (main gate)
- **live_adjacent.yml** - Additional rules for live-related changes
- **research.yml** - Relaxed rules for research/analysis code

### Path Exclusions

- `docs/` - Documentation files
- `tmp/` - Temporary test artifacts
- `tests/fixtures/` - Test data

---

## Key Files

```
.github/workflows/
  └── policy_critic.yml              # CI workflow

docs/governance/
  ├── POLICY_CRITIC_STATUS.md        # This file
  ├── POLICY_CRITIC_G4_TELEMETRY_WORKFLOW.md  # Operator guide
  ├── POLICY_CRITIC_TELEMETRY_G4.md  # PR telemetry log
  ├── POLICY_PACK_TUNING_LOG.md      # Rule tuning history
  ├── POLICY_CRITIC_ROADMAP.md       # Full roadmap
  └── LLM_POLICY_CRITIC_CHARTER.md   # Original charter

src/governance/policy_critic/
  ├── critic.py                      # Core engine
  ├── rules.py                       # Rule implementations
  ├── packs.py                       # Policy pack loader
  ├── models.py                      # Data models
  ├── auto_apply_gate.py             # Auto-apply logic (G6)
  └── integration.py                 # Git integration

policy_packs/
  ├── ci.yml                         # Default pack
  ├── live_adjacent.yml              # Live-focused pack
  └── research.yml                   # Research pack

scripts/
  └── run_policy_critic.py           # CLI runner

tests/governance/policy_critic/
  ├── test_critic.py                 # Core tests (64 total)
  ├── test_rules.py                  # Rule tests
  ├── test_packs.py                  # Pack tests
  └── test_auto_apply_gate.py        # Auto-apply tests
```

---

## Recent Changes

### 2025-12-12 - PR #4 Merged

**Changes:**
- Removed tmp artifacts from git tracking
- Added path exclusions to RiskLimitRaiseRule (docs/, tmp/, tests/fixtures/)
- Created G4 telemetry workflow guide
- Implemented violation deduplication
- Lowered test plan threshold for high-critical paths (50→10 lines)

**Commits:**
- `1d5a216` - Merge PR #4
- `448e125` - fix(policy-critic): exclude docs/tmp/fixtures paths
- `0e401fa` - docs(governance): log PR #4 false positive
- `c7307bc` - chore(policy-critic): remove tmp artifacts
- `92edea7` - chore(governance): G3.6 policy pack tuning

**Impact:**
- False positive from tmp artifacts resolved
- Documentation false positives resolved
- Policy Critic gate now production-ready

---

## Quick Commands

### Check PR with Policy Critic
```bash
gh pr view <PR>
gh pr checks <PR>
```

### View Policy Critic logs
```bash
gh run view <RUN_ID> --log-failed
```

### Run Policy Critic locally
```bash
python3 scripts/run_policy_critic.py \
  --diff-file pr.diff \
  --changed-files "file1.py,file2.py"
```

### View telemetry stats
```bash
# Count PRs
grep -c "^## PR #" docs/governance/POLICY_CRITIC_TELEMETRY_G4.md

# False positive rate
grep -c "FALSE_POSITIVE" docs/governance/POLICY_CRITIC_TELEMETRY_G4.md
```

---

## Support

- **Issues:** Report at project issue tracker
- **Questions:** Check `docs/governance/POLICY_CRITIC_G4_TELEMETRY_WORKFLOW.md`
- **Rule Changes:** Document in `POLICY_PACK_TUNING_LOG.md`
