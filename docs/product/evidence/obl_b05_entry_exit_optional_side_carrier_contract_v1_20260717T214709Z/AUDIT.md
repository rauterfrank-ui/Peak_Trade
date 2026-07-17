# AUDIT — OBL_B05 ENTRY_EXIT Optional Side-Carrier Contract v1

- slice_id: `OBL_B05_ENTRY_EXIT_OPTIONAL_SIDE_CARRIER_CONTRACT_V1`
- base_sha: `0473c8bad1b0b82840ec038fc0f84ec92a396cff`
- parent_audit: `OBL_B05_DIRECTIONAL_SIDE_CARRIER_AUTHORITY_AUDIT_V1` (TERMINAL_CONTRACT_GAP)
- authority_effect: `NONE`
- runtime_effect: `NONE`
- offline_only: `true`

## End-state flags

- CONTRACT_EXTENSION_AVAILABLE=true
- LEGACY_BEHAVIOR_UNCHANGED=true
- BOLLINGER_SIDE_ACTIVATED=false
- SEMANTIC_PRODUCER_DECISION_STILL_REQUIRED=true
- LIVE_AUTHORIZED=false
- ORDERS_ENABLED=false

## Before (BASE)

- Material had no `entry_side` field.
- `resolve_agreement_bound_directional_cycle_v1(ENTRY_EXIT)` always returned `None`.
- Bollinger ENTRY → flat `(mark, mark)` → DA first-false
  `FF_DA_FLAT_PATH_ENTRY_EXIT_NO_SIDE_CARRIER_V1` (contract-universal ×185).

## After (this slice)

- Material carries optional explicit `entry_side ∈ {LONG, SHORT, NONE}`.
- Adapter defaults all existing producers to `NONE` (Bollinger included).
- Resolve honors only explicit LONG/SHORT on ENTRY; EXIT invents nothing.
- Legacy Bollinger path remains flat / fail-closed — baseline predicate unchanged.
- Explicit LONG/SHORT (test-constructed) produce relative ±2% shared-path projection.

## Scope guard

No producer activation, no Suitability ENTRY→LONG promotion to DA authority,
no confirmation/composition/runtime/live mutation.
