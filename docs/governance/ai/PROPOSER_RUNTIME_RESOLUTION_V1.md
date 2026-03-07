# Proposer Runtime Resolution v1

## Purpose
This document records the current repo-near runtime resolution state for proposer semantics.

It does not change runtime behavior.

## Current Resolution
- proposer is less runtime-evidenced than critic
- proposer remains best interpreted as advisory-only
- exact owning module and exact data contract are still unresolved or partial
- execution authority is not evidenced
- final trade authority is not evidenced

## Current Best Truth
- proposer semantics are closest to proposal / candidate / generation language
- proposer may influence upstream advisory or pre-decision artifacts where explicitly supported
- proposer is not execution authority
- closest-to-trade execution remains deterministic gated

## Next Resolution Target
- exact owning module
- exact call timing
- exact data contract
- exact runtime trigger, only if explicitly evidenced

## Canonical Reading Order
- `docs&#47;governance&#47;ai&#47;CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md`
- `docs&#47;governance&#47;ai&#47;RUNTIME_UNKNOWN_RESOLUTION_V1.md`
- `docs&#47;governance&#47;ai&#47;CRITIC_RUNTIME_RESOLUTION_V2.md`
- `out&#47;ops&#47;proposer_runtime_resolution_v1_*`
