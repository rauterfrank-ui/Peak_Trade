# Ops Registry Index

## Policy Telemetry (Real) — Audit Milestone

This milestone ensures `telemetry_summary.json` is derived from **real** policy decision context (paper session `evidence_manifest.json`), not from fallback policy.

### Stable pointers

- Phase L smoke: `docs/ops/registry/LATEST_PHASE_L_SMOKE.pointer`
- Phase M smoke: `docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer`
- Global latest: `docs/ops/registry/LATEST_POLICY_TELEMETRY_REAL.pointer`

### Operator verification

Preferred operator entrypoint:

```bash
scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_POLICY_TELEMETRY_REAL.pointer --download
```

With evidence pack:

```bash
scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_POLICY_TELEMETRY_REAL.pointer --download --pack
```

### Invariants checked

- `policy.action` ∈ {ALLOW, NO_TRADE}
- `policy.reason_codes` is a list
- `AUDIT_MANIFEST_NO_DECISION_CONTEXT` not in reason_codes
- `source` == "evidence_manifest"

### Pipeline phases (L → R)

| Phase | Description |
|-------|-------------|
| L | Real policy from evidence_manifest |
| M | Regression guards (no fallback) |
| N | Stable pointers in registry |
| O | Portable pointer fields + fetch script |
| P | Verifier + README |
| Q | Operator entrypoint (`verify_from_registry.sh`) |
| R | CI operator verify smoke |
| S | **DONE** — This index |
