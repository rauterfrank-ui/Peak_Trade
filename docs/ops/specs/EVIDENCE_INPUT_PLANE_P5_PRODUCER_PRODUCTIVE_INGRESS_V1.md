---
docs_token: DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_EVIDENCE_INPUT_PLANE_P5_PRODUCER_PRODUCTIVE_INGRESS_V1
status: active
scope: P5 productive producer ingress terminating at Component A only; no B/DP bypass
workpackage: P5_MASTER_V2_DOUBLE_PLAY_PRODUCER_PRODUCTIVE_INGRESS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-11-22
---

# Master V2 / Double Play — Evidence & Input Plane P5 Producer Productive Ingress V1

Bounded **producer → adapter → Component A** termination for Market Intelligence, Learning,
Optimization, and Meta-Learning producer classes.

```text
PRODUCER_TRADING_AUTHORITY=NONE
DIRECT_PRODUCER_TO_B_BYPASS=false
DIRECT_PRODUCER_TO_DP_BYPASS=false
PRODUCTIVE_ACTIVATION_AUTHORIZED=false
L6_SEMANTIC_AUTHORITY=UNCHANGED
```

## Topology

```text
Producer artifact
  → typed P5 adapter
  → Component A (adjudicate_evidence_intake_v1)
  → canonical adjudicated evidence envelope (ADMIT only)
```

Forbidden: producer → B, producer → L6, producer → DP layers, trading semantics in adapters.

## Verification

```bash
./scripts/pt -m pytest tests/governance/test_master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.py -q
./scripts/pt -m pytest tests/learning/test_loop_a_conditioned_learning_evidence_v1.py -q
```

## Original producer-artifact admission before A — 2026-11-22

At `9adc88677a8cd8f1653dff697ecbc59b2f59a4c5`, Optimization and Meta producer
artifacts already reach Component A through their typed P5 adapters. Producer/schema
admission, instrument/epoch/freshness checks and the in-memory adjudication ledger
exist. Their native artifact validators checked only the format of content_hash
and reproducibility_digest; the declared IDs and fixed namespace/version/effect
metadata were not fully checked against the original producers.

Both existing validators now verify the full original content_hash, reconstruct
their own retained reproducibility body and reuse the original ID derivation.
Optimization binds M5 content/plane identity, binding digest/record ID and producer;
Meta binds M6 ID/reproducibility digest, binding digest and producer. The two scopes
are distinct, and neither is replaced by a whole-record reproduction digest.
Domain, producer version, source/binding schema and trading_selection_effect must
match the original producer constants. Earlier schema, kind, authority, hash-format
and producer-ID errors retain their precedence. Producers, original formulas,
artifact bytes and extra opaque annotations remain unchanged.

The two existing adapters convert their owner's typed validation error into the
existing artifact_malformed adapter error. Ingress therefore emits its original
typed REJECT with no envelope before invoking Component A or writing its ledger.
Promotion lookup and wrong-source-schema blocking remain earlier separate gates.
No new producer-to-B/L6/DP bypass or runtime authority is introduced.

Verification: `tests/governance/test_p5_producer_artifact_integrity_v1.py`.
The corrected original-owner baseline has 114 unblocked paths and eight passing
controls. Thirty-eight malformed ingress packets reached actual A adjudication;
six captured examples are ADMIT and recorded in its in-memory ledger, always with
trading_authority=NONE. That is incorrect evidence admission, not a grant of trading
or apply authority. Six complete valid source/artifact/intake/A-result/replay packets
and six synthetic source LearningState ledger files remain byte-identical. Original
Mapping, JSON and annotations survive. Replay returns the stored original result;
the existing dedup_replay flag is not redefined. The A ledger remains in memory;
these source ledger files do not prove a durable P5 writer or restart recovery.

The three P5 files are frozen SOURCE_INTERFACE entries in the policy inventory.
The existing law projection now admits only their complete exact reviewed source
bundle or the complete frozen originals. Missing/mixed/unknown bodies, forged
frozen parents, ordinary rehashed development rows and unrelated policy changes
remain rejected. Each changed source still needs its original-parent development
binding. Frozen inventories, policy objects, tags and runtime grants are preserved.
`tests/ops/test_p5_artifact_admission_development_delta_v1.py` checks both allowed
bundles and these denials through the actual policy reader. This is exact source
admission for this repair, not a general exemption or operating authorization.

Self-consistency does not authenticate original M5/M6, the original binding context
or its market source. Their complete records are not supplied to these validators.
Fields outside each retained reproduction scope remain protected by the full
transport hash, not independently reprojected from an absent source. A freshly
self-consistent replacement record is not source-certified. Numerical quality,
chronology, decision correctness, economics, trading effect downstream of A and
overall operation need their own evidence. No new measurement, training, search,
promotion or operating session is started. BTC and financial rules are unchanged.

## Original binding-context body before new P5 artifacts — 2026-11-22

At `98af19878ef259714194e0329f169dd327c273cd`, both native M5/M6 producers
already validate their source and compare its lineage schema/digest with the
supplied governed binding. The shared binding validator, however, did not
recompute binding_digest or binding_record_id from the retained original body.
Thirty-six counterexamples pass that old validator or producer. Six captured
examples produce P5 artifacts which reach actual Component A ADMIT and its
in-memory ledger, always with trading_authority=NONE.

The existing binding validator now checks the original domain, reconstructs
exactly the builder's ten retained body fields, recomputes binding_digest and
reuses its original record-ID formula. Missing reconstruction inputs and
contradictory declarations stop with the existing typed binding error before
either native producer can issue a new P5 artifact. Earlier schema, presence,
source-digest and epoch errors retain their priority. The builder, formulas,
M5/M6 joins, original time strings and distinct artifact reproduction scopes
are unchanged. Extra opaque annotations remain outside this original body.

`tests/governance/test_p5_binding_context_integrity_v1.py` covers both validator
and producer entrypoints, valid Mapping/JSON/annotation packets and the original
producer-owned lineage denials. Six complete valid source/context/binding/P5/A/
replay packets and six synthetic source LearningState ledger files remain
byte-identical. Replay retains the stored original A result. Those files are
not P5 persistence or crash-recovery evidence.

This checks the supplied body's self-consistency, not independent authenticity
of the original market context or its opaque references. Fresh self-consistent
replacement records are not source-certified; historical P5 artifacts lacking
the original binding body are not retroactively certified or rejected by this
new upstream check. The stored freshness_horizon_seconds is part of the binding
digest; actual A intake still uses its separate termination-context horizon.
No new freshness policy, exact-clock claim, numerical quality, trading rule or
operating grant is introduced. ADMIT remains evidence admission only.

The existing policy reader admits only the exact reviewed binding-validator
source with its original frozen-parent development row. Unknown/rehashed
sources, missing rows, wrong parents and unrelated policy drift remain denied;
the earlier three-file P5 bundle and frozen policy objects/tags are unchanged.
`tests/ops/test_p5_binding_context_development_delta_v1.py` tests that real reader.
BTC, Core/financial rules, real stores and runtime authority stay unchanged;
no operating, capture, training, search or research session is started.
