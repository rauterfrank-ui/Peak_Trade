# Critic Runtime Resolution v2

## Purpose
This document records the current repo-near runtime resolution state for critic semantics.

It does not change runtime behavior.

## Current Resolution
- critic is better evidenced as runtime-near than proposer
- critic remains aligned with supervisory, pre-execution, gate-adjacent influence
- exact owning module and exact data contract are still only partially resolved
- final trade authority is not evidenced

## Current Best Truth
- critic semantics are closest to policy / gate / readiness / routing / health surfaces
- critic may influence pre-execution posture where explicitly supported
- critic is not execution authority
- closest-to-trade execution remains deterministic gated

## Next Resolution Target
- exact owning module
- exact call timing
- exact data contract
- exact block/downgrade semantics, only if explicitly evidenced

## Canonical Reading Order
- `docs/governance/ai/CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md`
- `docs/governance/ai/RUNTIME_UNKNOWN_RESOLUTION_V1.md`
- `out/ops/critic_runtime_resolution_v2_*`
