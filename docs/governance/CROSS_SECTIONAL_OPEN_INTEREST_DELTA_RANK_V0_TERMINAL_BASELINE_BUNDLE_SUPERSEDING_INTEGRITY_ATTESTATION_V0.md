# Cross Sectional Open Interest Delta Rank v0 — Terminal Baseline Bundle Superseding Integrity Attestation

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_TERMINAL_BASELINE_BUNDLE_SUPERSEDING_INTEGRITY_ATTESTATION_V0
STATUS: EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION_COMPLETE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Attestiert die semantische Terminal-Baseline-Wahrheit des historischen Target-Bundles aus unabhängiger verifizierter Provenance, konserviert den kryptografischen Defekt (`final_report.txt` Digest-Drift, `MANIFEST_VERIFY_RC=1`), und registriert `EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION` ausschließlich für Integrity-Consumption. Keine Target-Reparatur, keine Economic Evaluation, keine Runtime-Authority.

## A. Zweck

Das historische Target-Bundle `cross_sectional_open_interest_delta_rank_v0_terminal_inconclusive_baseline_evidence_and_unchanged_retry_block_v0_20260712T011717Z` bleibt byte-identisch und kryptografisch kompromittiert (`TARGET_MANIFEST_VERIFY_RC=1`, Drift nur in `final_report.txt`). Diese Attestation ersetzt die semantische Terminal-Baseline-Wahrheit nicht, sondern attestiert sie aus unabhängigen manifest-verifizierten Quellen und ermöglicht operative Downstream-Freigabe für den Implementierungs-Scope `CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING_IMPLEMENTATION_V0`.

## B. Scope

| Feld | Wert |
|---|---|
| `PROCESS_CLASSIFICATION` | `BOUNDED_FUTURES_ONLY_TERMINAL_BASELINE_EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION_V0` |
| `GO_TOKEN` | `GO_SOURCE_EVIDENCE_TERMINAL_BASELINE_BUNDLE_SUPERSEDING_INTEGRITY_ATTESTATION_IMPLEMENTATION_V0` |
| `STRATEGY_ID` | `cross_sectional_open_interest_delta_rank` |
| `STRATEGY_VERSION` | `v0` |
| `RESEARCH_SCOPE` | `cross_sectional_open_interest_delta_rank&#47;v0` |
| `SUPERSESSION_MODE` | `EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION` |
| `offline_only` | `true` |
| `non_authorizing` | `true` |

Ausgeschlossen: Target-Manifest-Rewrite, `final_report.txt`-Rewrite, Byte-exact-Original-Fabrication, Semantic-Baseline-Change, Economic Evaluation, Hypothesis-Binding-Implementation, Runtime, Shadow, Paper, Testnet, Scheduler, Orders, Credentials, Arming, Live.

## C. Target Integrity Defect (konserviert)

| Feld | Wert |
|---|---|
| `TARGET_SOURCE_EVIDENCE_DIR` | `...&#47;cross_sectional_open_interest_delta_rank_v0_terminal_inconclusive_baseline_evidence_and_unchanged_retry_block_v0_20260712T011717Z` |
| `TARGET_MANIFEST_VERIFY_RC` | `1` |
| `DRIFTED_FILE` | `final_report.txt` |
| `EXPECTED_FILE_DIGEST` | `460c164f5d659e53817fab7ec19216550ddf7b2f6909ec25acdf131580e5b4e6` |
| `ACTUAL_FILE_DIGEST` | `65d45a3ee7150cfc2a733c918135e5da145e895c854a4bbcb41ce4a751732dd9` |
| `DRIFT_CLASSIFICATION` | `MANIFEST_GENERATED_FROM_DIFFERENT_CONTENT` |
| `CRYPTOGRAPHIC_TARGET_BUNDLE_INTEGRITY` | `COMPROMISED` |
| `SEMANTIC_TERMINAL_BASELINE_TRUTH` | `PRESERVED` |

## D. Supersession Contract

| Feld | Wert |
|---|---|
| `SUPERSESSION_EXPLICIT` | `true` |
| `SUPERSEDES_TARGET_FOR_INTEGRITY_CONSUMPTION_ONLY` | `true` |
| `DOES_NOT_SUPERSEDE_SEMANTIC_BASELINE_CLASSIFICATION` | `true` |
| `DOES_NOT_CREATE_BYTE_EXACT_TARGET_INTEGRITY` | `true` |
| `DOES_NOT_CONVERT_TARGET_MANIFEST_RC_TO_ZERO` | `true` |
| `HISTORICAL_TARGET_BUNDLE_MUTATED` | `false` |
| `HISTORICAL_TARGET_MANIFEST_REWRITTEN` | `false` |
| `UNCHANGED_RETRY_BLOCKED` | `true` |
| `BASELINE_CLASSIFICATION` | `INCONCLUSIVE` |
| `BASELINE_BINDING_DIGEST` | `49e444fddf31c2da877e2c30eb0135848a657d58febfbb1827affcb6154dfb64` |

## E. Downstream Admissibility

| Feld | Wert |
|---|---|
| `DOWNSTREAM_RANKING_OPERATIVELY_ADMISSIBLE` | `true` (nur Integrity-Consumption via additive Contract) |
| `PROVISIONAL_RANK1` | `cross_sectional_open_interest_level_rank_v0` |
| `NEXT_RECOMMENDED_SCOPE` | `CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING_IMPLEMENTATION_V0` |
| `SEPARATE_OPERATOR_GO_REQUIRED` | `true` |

## F. Evidence Bundle Referenzen

| Feld | Wert |
|---|---|
| `RECONCILIATION_EVIDENCE_REF` | `...&#47;source_evidence_manifest_reconciliation_for_terminal_baseline_bundle_read_only_v0_20260712T032521Z` |
| `DOWNSTREAM_RANKING_EVIDENCE_REF` | `...&#47;cross_sectional_open_interest_delta_rank_v0_post_terminal_evidence_distinct_hypothesis_ranking_read_only_v0_20260712T032121Z` |
| `Governance config ref` | `config/research/cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_superseding_integrity_attestation_v0.json` |

## G. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `PASS` |
| `RUNTIME_EFFECT` | `NONE` |
| `AUTHORITY_EFFECT` | `NONE` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
