# Policy Guard Pattern Template

## Goal
Prevent policy drift by enforcing:
1) **Local enforcement** (ops doctor)
2) **CI enforcement** (always-run gate)
3) **Guard-the-guardrail** (ops doctor verifies CI enforcement presence)

## Files
- Local guard script:
  - `scripts&#47;ops&#47;check_<policy>.sh`
- CI enforcement:
  - Always-run gate workflow runs the guard script (exit 1 blocks PR)
- Guard-the-guardrail script:
  - `scripts&#47;ops&#47;check_<policy>_ci_enforced.sh` verifies workflow still calls local guard

## Checklist (Copy/Paste)
### A) Local guard
- [ ] Script exists + executable
- [ ] Fast (<1s), grep/static where possible
- [ ] Exit 0 on PASS, exit 1 on FAIL, clear output

### B) ops doctor integration
- [ ] Run local guard in `ops doctor`
- [ ] Surface PASS/FAIL with clear label

### C) CI enforcement (always-run)
- [ ] Add step in always-run gate workflow
- [ ] Step runs regardless of change scope (docs-only included)
- [ ] Fails only on actual policy violation

### D) Guard-the-guardrail
- [ ] Script verifies gate workflow still calls local guard
- [ ] Integrated into `ops doctor`

### E) Documentation
- [ ] README: local + CI enforcement documented
- [ ] Merge-log created

## Example: Formatter Policy Drift Guard
- Local: `check_no_black_enforcement.sh`
- CI: `.github/workflows/lint_gate.yml` runs it
- Guard CI presence: `check_formatter_policy_ci_enforced.sh`
