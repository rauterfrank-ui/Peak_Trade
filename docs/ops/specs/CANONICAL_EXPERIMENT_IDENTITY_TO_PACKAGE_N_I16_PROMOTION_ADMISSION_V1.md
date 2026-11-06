# Canonical Experiment Identity to Package-N I16 Promotion Admission v1

Contract for Peak_Trade Identity Admission. This is not Self-Learning Phase 13.

```text
SCHEMA_VERSION=canonical_experiment_identity_to_package_n_i16_promotion_admission_v1
ADMISSION_DOMAIN=peak_trade.canonical_experiment_identity_to_package_n_i16_promotion_admission.v1
ADMISSION_PRESENT=true
ADMISSION_AUTHORITY=RESEARCH_EVIDENCE_PARENT_ONLY
PROMOTION_AUTHORITY=NONE
PROMOTION_APPLY_ALLOWED=false
BOUNDED_AUTO_ALLOWED=false
I16_ASSESSMENT_CONSUMABLE_WHEN_ADMITTED=true
PACKAGE_N_HASH_REINTERPRETATION_FORBIDDEN=true
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
SELF_LEARNING_NOT_SELF_AUTHORIZING=true
```

Owner:

- `src&#47;experiments&#47;canonical_experiment_identity_to_package_n_i16_promotion_admission_v1.py` — admit research-evidence parent only

Reuse, do not replace:

```text
Phase 1   src.experiments.canonical_experiment_identity_v1              REUSE COMPLETE identity
Package N src.experiments.experiment_identity_manifest_v1               REUSE experiment_identity_id unchanged
I16 join  src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1  REUSE Package-N SHA256 assessment surface
I82 id    src.experiments.cross_lane_identity_join_v1.is_package_n_sha256_canonical_id  REUSE
```

```text
src.governance.promotion_loop.engine.apply_proposals_to_live_overrides  NOT_APPLICABLE
src.governance.promotion_loop.engine                                     NOT_APPLICABLE as apply&#47;authority
src.meta.learning_loop.comparison_ssot_v1                                NOT_APPLICABLE
src.experiments.canonical_champion_challenger_v1                         NOT_APPLICABLE
src.live.live_gates                                                      NOT_APPLICABLE
```

This layer does not invent identity, does not recompute Package-N hashes, and does not promote. It attaches a Phase-1 COMPLETE identity as a research-evidence parent onto an existing Package-N `experiment_identity_id` so `manual_only` I16 assessment may consume that parent.

## Shape

```text
PHASE_1_COMPLETE_VALIDATION
PACKAGE_N_MANIFEST_VALIDATION
PLANE_SEPARATION
COMPARABLE_DIMENSION_CHECK
UNSUPPORTED_PROJECTION_GUARD
HASH_REINTERPRETATION_GUARD
AUTHORITY_BOUNDARY
I16_ASSESSMENT_ATTACHMENT
ADMISSION_EVIDENCE
```

```text
Canonical Phase-1 Identity COMPLETE
        ↓
explicit compatibility&#47;admission mapping
        ↓
existing Package-N experiment_identity_id remains unchanged
        ↓
manual_only I16 assessment may consume admitted research-evidence parent
```

## Fail closed

Any of the following yields a typed `REJECTED_*` result, never `ADMITTED`:

```text
missing dimension
incompatible dimension
ambiguous identity
unsupported projection
hash reinterpretation required
non-COMPLETE Phase-1 identity
invalid Package-N identity
requested apply
requested bounded_auto or any mode other than manual_only
```

Package N remains an incomplete historical projection. Completeness of Phase 1 does not make Package N complete. Claiming that Package N already encodes Phase-1 fee&#47;seed&#47;split&#47;core&#47;git dimensions is `REJECTED_UNSUPPORTED_PROJECTION`.

## Comparable dimension

The only overlapping comparable dimension in this contract is strategy identity:

```text
phase1.strategy_identity == package_n.identity_config.strategy_name
```

Mismatch is `REJECTED_INCOMPATIBLE_DIMENSION`. No silent aliasing, version stripping, or case folding.

## Authority

```text
PROMOTION_AUTHORITY=NONE
PROMOTION_APPLY_ALLOWED=false
I16_ASSESSMENT_CONSUMABLE != APPLY
I16_ASSESSMENT_CONSUMABLE != bounded_auto
ADMITTED != PROMOTED
ADMITTED != LIVE
```

`ADMITTED` means only that I16 `manual_only` assessment may read the research-evidence parent. It does not write live overrides, arm, fund, submit orders, swap a Champion, or authorize canary.

## Non-effects

```text
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
ORDER_EFFECT=false
ACCOUNT_MUTATION_EFFECT=false
MULTI_FUTURE_AUTH_EFFECT=false
FUNDING_AUTH_EFFECT=false
PROMOTION_APPLY_EFFECT=false
I82_FULL_MIGRATION=false
MD5_REMOVAL=false
IDENTITY_BACKFILL=false
G14_PRODUCTIVE_AUTHORITY=false
```
