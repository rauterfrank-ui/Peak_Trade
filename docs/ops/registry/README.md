# Ops Registry — Portable Verification

This directory contains stable pointers to important audit milestones.

## Verify a milestone (portable)

Prereqs:

- `gh` authenticated
- Repo checked out

Example (Phase M):

```bash
python3 scripts/ops/verify_registry_pointer_artifacts.py \
  docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer \
  --download \
  --out-base out/ops/gh_runs
```

With evidence pack output:

```bash
python3 scripts/ops/verify_registry_pointer_artifacts.py \
  docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer \
  --download \
  --out-base out/ops/gh_runs \
  --pack-out out/ops/evidence_packs/verify_phase_m
```

## Invariants checked

- `policy.action` ∈ {ALLOW, NO_TRADE}
- `policy.reason_codes` is a list
- `AUDIT_MANIFEST_NO_DECISION_CONTEXT` not in reason_codes
- `source` == "evidence_manifest"
