# Ops Registry — Portable Verification

This directory contains stable pointers to important audit milestones.

## Verify a milestone (operator shortcut)

Preferred:

```bash
scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer --download
```

With evidence pack:

```bash
scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer --download --pack
```

## Verify a milestone (portable, direct)

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
