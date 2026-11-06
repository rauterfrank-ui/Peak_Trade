# GGE raw and explicit legacy Scope learning configurations v2

docs_token: DOCS_TOKEN_GGE_RAW_AND_LEGACY_SCOPE_LEARNING_CONFIGURATION_V2

**SUPERSEDED by [GGE-only v3](GGE_ONLY_FUTURES_AND_COMMON_ASSET_ADMISSION_V3.md) on 2026-11-03.** The bounded comparison configuration described below is no longer executable Double Play.

Owner-directed historical local implementation, 2026-11-03. Subordinate to the Master Runbook; no activation or external-effect authority.

## Configuration and effective distance

The productive default remains `default_instrument_relative_scope_initialization_policy_v1()`. Its integrated replay envelope now selects `gge_raw_v2`: GGE supplies the positive finite distance in the instrument's price units, without a fixed economic floor or ceiling. Neutral refreshes its distance without trailing its anchor. LONG and SHORT retain their directional anchor mechanics. CHOP still freezes geometry. Existing notional, leverage, switching, admission and authorization checks remain applicable.

An explicitly supplied legacy `CanonicalScopeInitializationPolicyV1` continues to select `legacy_bounded_v1` with its configured economic bounds. The default constructor version is legacy; the productive factory explicitly selects instrument-relative policy. These are separate configurations, never simultaneous competing distance authorities. A restored snapshot with a different policy version is rejected rather than silently used. Unversioned, CHOP-frozen old runtime state cannot enter raw mode without explicit migration. Ordinary restored geometry is refreshed from GGE while preserving its reference and bookkeeping. Persistence retains the effective distance mode.

In delegated L1–L10 replay the validated seal owns D_t and R_t. Downstream runtime readmodels and Layer-C distances project those sealed values instead of an old bootstrap carrier. The learning identity records this owner separately as `sealed_explicit_dt_v1`; a seal alone is not evidence that an arbitrary proposal originated in GGE. The existing productive P5 proposal producer supplies the GGE magnitude.

The protective-stop join consumes the adverse distance actually bound to the evaluated Scope event. It must not independently recompute a fresh distance inconsistent with a bounded or CHOP-frozen decision. Invalid/missing distance remains blocking. The original entry/exit/confirmation semantics are otherwise outside this cutover.

## Capture, evaluation, ingest and export

`productive_scope_learning_config_hash_v1` hashes the versioned distance/owner contract, declared config digest, replay policies, effective Scope policy and dynamic-rule configuration. Cycle prices and resolved volatility are market evidence and do not create a new configuration. Bootstrap and restored instances of the same policy share configuration identity.

The current productive capture join and the wallclock decision/economics bridge bind this hash before observing core producers. Decision and incident identity/content includes the configuration. DDO's `code_sha` field requires SHA256: a valid declared Git SHA1 is represented by SHA256 of `git-commit-sha1:` followed by that SHA1. It binds the declared revision, not uncommitted source bytes. Invalid/unavailable revision stays `UNKNOWN`. Source-file hashes in cutover evidence bind the actual changed code.

Productive evaluation copies decision code/config identity when deriving or completing an unspecified identity. Conflicting known identity is rejected. Outcome, attribution and counterfactual must agree on code/config at learning ingest. Learning states inherit these fields from their outcome; callers cannot relabel the source. Host learning pools include session, account, code and configuration. Ingest rejects a prior state from another configuration even if a caller deliberately reuses a scope ID. Idempotent replay remains supported within a configuration.

Learning export preserves the source identity and rejects relabeling. Opaque score-label feedback requires known code provenance and the current resolved configuration. A stale learned label is cleared on mismatch; independently configured labels are not silently erased. The bridge resolves the current configuration before checking this feedback.

## Historical data and limits

Existing ledgers, outcomes and learner states are unchanged. Unknown or differently configured historical states are excluded from the new pool/feedback; they remain available for explicitly identified offline investigation. No claim is made that old numerical values are wrong. No automatic deletion, retrospective relabeling, training, search, promotion or production activation occurs.

The tests cover small/large price scales through the full offline replay, LONG/SHORT/Neutral, restored legacy bands, sealed-distance projection, capture → finalized-bar outcome → ingest → export, and rejection of cross-configuration reuse. This proves the tested contracts, not profitable learning, valid economic labels for every old run, or whole-system readiness. GitHub checks remain pending until a later authorized push.

Implementation and reproducible checks: `tests/ops/test_gge_scope_learning_configuration_cutover_v2.py`. Progress and outstanding system-wide work: [system blueprint](../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md).
