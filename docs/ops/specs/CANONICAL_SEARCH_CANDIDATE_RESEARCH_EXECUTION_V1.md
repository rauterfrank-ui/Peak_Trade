---
docs_token: DOCS_TOKEN_CANONICAL_SEARCH_CANDIDATE_RESEARCH_EXECUTION_V1
status: active
scope: Explicit bounded offline Search candidate execution and subsequent Meta evidence
capability: CANONICAL_SEARCH_CANDIDATE_RESEARCH_EXECUTION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-11-04
---

# Explicit Search candidate research execution v1

Subordinate to Master Runbook. Newly implemented composition derived from restored
SelfLearning master sections3.1/15/22; not recovered historical executable bytes.
[Owner](../../../src/experiments/canonical_search_candidate_research_execution_v1.py).
Existing Search, Phase1/2/4/5/10/11 and GVEF definitions are unchanged.

## Explicit execution

run_search_candidate_research_execution_v1 validates an existing complete Search
record, exact single PROPOSED experiment_id and explicit UTC execution time before
one caller-owned offline provider call. Nanosecond chronology and calendar are
checked without rounding. Provider receives a read-only candidate snapshot and
returns an existing CanonicalAutomatedOfflineResearchLoopRequestV1 containing
actual observations and explicitly supplied comparison/gap context.

Before invoking existing Phase10, selected hypothesis, full constructed Phase1
identity, parameter region, strategy family, candidate ref, regime and execution
time must equal the selected Search binding. Multiple hypotheses are rejected.
No parameter aliases, metrics, stability or missing outcomes are inferred.
Phase10 remains the owner of memory binding, optional stores and research results.
No persistence from this composition's Phase10 call occurs before those checks;
provider code itself is caller-owned and not sandboxed by this API.

Output retains original Search and actual Phase10 records, provider/source-class
claims, ids/digests, explicit horizon/universe and a reusable ResearchResultMetaInputV1.
Source class is declared, never authenticated by this mechanism. The original
Search proposal still says executed=false; a separate later execution record
preserves historical truth. Read-only JSON lists preserve existing owner shape.

run_research_feedback_next_execution_v1 invokes the existing Research→Meta→Search
adapter and then exactly one proposed next candidate. Explicit budget1 is required;
zero/multiple proposed candidates fail. No recursive scheduling, policy replacement,
productive mutation or new metric definition. Existing M6 projection remains separate.

## GVEF reference and later reuse

build_research_execution_gvef_reference_v1 retains numeric canonical UTF8-JSON bytes
with allow_nan=false. A separate float-free learning artifact binds relative JSON
artifact_ref, exact payload_sha256 and Search/Loop/experiment identity. It checks
the envelope content digests and correspondence to the returned next Meta input.
No automatic file IO or path resolution; caller owns the actual artifact store.

The existing GVEF SelfLearning evaluator can evaluate the reference's artifact
digest and boundaries. This does not load or evaluate all numeric payload fields.
read_research_execution_gvef_reference_v1 verifies supplied bytes, canonical form,
reference identity and existing Search/Phase10 validators before rebuilding the
Meta input. It neither authenticates source measurements nor authorizes anything.

execution content_digest, payload byte SHA256 and GVEF sl.artifact_digest bind
three different objects. Declared evidence classes, references and COMPLETE/PASS
remain scoped; useful learning requires separate comparable measurements.

[32 tests, measured native case, persistence/reload and later Meta/GVEF proof](../evidence/search_candidate_measured_execution_meta_proof_v1_2026_11_04/README.md).
