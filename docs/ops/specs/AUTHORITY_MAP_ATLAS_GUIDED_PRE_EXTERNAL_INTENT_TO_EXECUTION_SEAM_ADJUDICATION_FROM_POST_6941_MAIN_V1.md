# Authority-Map-/Atlas-Guided PRE_EXTERNAL → intent_to_execution Seam Adjudication (post-6941 main, v1)

Normative spec for forensic decomposition of the `order_intent` → `execution_external_effect`
(`intent_to_execution`) seam after PR #6941 merge, without venue POST, permit mint, credential
load, or standing import-time lift.

## Scope

- Continue Map/Atlas-guided whole-system workflow from synthetic-treasury PRE_EXTERNAL proof.
- Runtime-probe canonical external-effect policy chain (policy → standing lift → permit mint
  admission bindings) against CURRENT decision records.
- Probe fail-closed invoke sink and envelope-bound send seam with `permit=None` (no network).
- Classify epistemic layers explicitly; stop at operational Owner boundary for actual POST.

## Non-goals

- Minting permits, loading credentials, venue POST, or flipping import-time standing constants.
- PAPER / SHADOW / TESTNET / G2 runtime.
- Registry / operator-verify infra repair.

## Terminal success

`PRE_EXTERNAL_EFFECT` runtime-proven; policy-chain admissions documented; `intent_to_execution`
classified `AUTHORITY_BLOCKED` at operational external-effect sink; earliest remaining genuine
blocker remains umbrella `EXTERNAL_EFFECT_AUTHORIZATION` (scoped Owner-GO for actual
permit-backed venue POST, not missing policy admission wiring).
