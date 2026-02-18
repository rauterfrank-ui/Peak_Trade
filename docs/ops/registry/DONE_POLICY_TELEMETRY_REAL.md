# DONE — Policy Telemetry (Real) Pipeline

**Status:** Complete (Phase S)

The Policy Telemetry (Real) audit pipeline is complete. All milestones L→R are implemented and verified.

## Summary

- **L:** Real policy from `evidence_manifest.json` (no fallback)
- **M:** Regression guards
- **N:** Stable pointers in registry
- **O:** Portable pointer fields + fetch script
- **P:** Verifier + README
- **Q:** Operator entrypoint (`verify_from_registry.sh`)
- **R:** CI operator verify smoke
- **S:** Canonical index ([INDEX.md](INDEX.md))

## Canonical entrypoints

- Index: [docs/ops/registry/INDEX.md](INDEX.md)
- Operator verify: `scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_POLICY_TELEMETRY_REAL.pointer --download`
