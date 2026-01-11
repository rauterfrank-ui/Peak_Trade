# Validator Report Summary

**Schema Version:** 1.0.0
**Tool:** l4_critic_determinism_contract_validator v1.0.0
**Subject:** l4_critic_determinism_contract_v1.0.0
**Result:** PASS

## Summary

- **Passed:** 1
- **Failed:** 0
- **Total:** 1

## Checks

### ✅ determinism_contract_validation

**Status:** PASS
**Message:** Reports are identical (hash match)

**Metrics:**
- `baseline_hash`: 4de2937bd14a8556e7f3611d2270d31e359bc38b1e37b62c4b3ab75c7c48a59b
- `candidate_hash`: 4de2937bd14a8556e7f3611d2270d31e359bc38b1e37b62c4b3ab75c7c48a59b
- `first_mismatch_path`: None

## Evidence

- **Baseline:** `tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/critic_report.json`
- **Candidate:** `.tmp/l4_critic_out/critic_report.json`

## Runtime Context

- **Git SHA:** `8574c672507d54a127451f786b2cf12edd917ba3`
- **Run ID:** `20902441555`
- **Workflow:** `L4 Critic Replay Determinism`
- **Job:** `l4_critic_replay_determinism`
- **Generated At (UTC):** 2026-01-11T21:50:52.571592Z
