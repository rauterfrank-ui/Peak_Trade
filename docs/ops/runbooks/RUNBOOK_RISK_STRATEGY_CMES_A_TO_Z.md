# RUNBOOK — Risk/Strategy CMES (7 Facts) A→Z (Cursor Multi-Agent)

## Objective
Implement a **Controlled Measurement & Evidence Stream (CMES)** for Risk/Strategy derived outputs:
- **pointer-only** (no payload/raw/transcript/content/secrets)
- **deterministic** (canonical order, stable hashes)
- **auditable** (artifacts only as {path, sha256})
- **gated learning** (deny-by-default allowlist via learnable surfaces)
- **orchestrator-integrated** (Ingress → Orchestrator → LayerEnvelope → L2/L3/L4/L5)

## CMES 7 Core Facts (Contract)
Required facts at the end of the pipeline:

1. `risk_score` (float, 0..1 or 0..100)
2. `risk_decision` (enum: ALLOW|REDUCE|BLOCK)
3. `risk_reason_codes` (list[str], stable codes)
4. `no_trade_triggered` (bool)
5. `no_trade_trigger_ids` (list[str], stable ids)
6. `strategy_state` (enum: ENABLED|DISABLED|PAUSED|DEGRADED) + optional `strategy_reason_codes` (list[str])
7. `data_quality_flags` (list[str], stable flags)

**Rule:** everything outbound is pointer-only; facts are allowed; no raw keys.

## Hard Safety Rules
- Outbound JSON must not include keys: payload|raw|transcript|api_key|secret|token|content
- Artifacts must be only `[{path, sha256}]`
- Deterministic sorting:
  - `risk_reason_codes`, `no_trade_trigger_ids`, `strategy_reason_codes`, `data_quality_flags` sorted
- Learning surfaces gate:
  - validate envelope learnable surfaces (deny-by-default)
  - L3 runtime gate is fail-closed

## Implementation Plan (A→Z)

### A) Define CMES Fact Schema + Canonicalization
- New module: `src/risk/cmes/facts.py`
  - dataclass / typed dict `CMESFacts`
  - `canonicalize_facts(facts) -> dict`: sorts lists, normalizes enums, validates required keys
  - `validate_facts(facts)`: raises on missing/invalid types

### B) Define Reason Code Registries (stability)
- `src/risk/cmes/reason_codes.py`
  - stable constants for:
    - risk_reason_codes
    - strategy_reason_codes
    - data_quality_flags
    - no_trade_trigger_ids (ids)
- Rule: tests enforce "uppercase snake" patterns and stable identifiers.

### C) Integrate CMES into FeatureView
- Extend FeatureView builder (ingress):
  - `src/ingress/views/feature_view_builder.py`
  - add `facts` block that includes CMES facts (computed / extracted / defaulted)
- Ensure pointer-only: facts only + artifact refs; no raw.

### D) Integrate CMES into EvidenceCapsule
- `src/ingress/capsules/evidence_capsule_builder.py`
  - capsule includes `facts` (same canonical dict), `labels` stays minimal
- Writer already produces json + sha256.

### E) Orchestrator wires facts into Envelope
- `src/ingress/orchestrator/ingress_orchestrator.py`
  - `run_ingress()` returns view + capsule paths as before
  - Add helper: load capsule dict (pointer-only) and build LayerEnvelope if needed by downstream
- Prefer passing capsule dict as `inputs` (pointer-only) and keep facts inside.

### F) LayerEnvelope Contract (tooling + learnable surfaces + pointer-only)
- Use/extend existing `src/ai_orchestration/layer_envelope.py`
  - envelope contains:
    - `layer_id`
    - `inputs` (pointer-only capsule/view-like dict)
    - `tooling_allowlist` from capability scope (via `get_envelope_tooling_allowlist`)
    - `learnable_surfaces` (empty by default or from inputs)
- Enforce at boundaries:
  - missing tooling_allowlist => violation
  - learnable surfaces validated per layer allowlist

### G) L2→L3 Handoff (optional, but recommended)
- Build envelope for L3 from L2-derived capsule:
  - ensure learnable surfaces for L3 are either empty or ["prompt_template_variants"]
  - ensure tooling allowlist is ["files"]

### H) L3 Runner Consumes Capsule + CMES Facts
- L3 input boundary checks already:
  - pointer-only keys
  - tooling files-only
  - learnable surfaces gate
- Confirm L3 does not persist raw; produces `run_manifest.json` + `operator_output.md`.

### I) L5 Risk Gate Uses CMES Facts Deterministically
- Introduce a deterministic adapter:
  - `src/risk/cmes/l5_adapter.py` reads facts and produces an allow/block decision
- Ensure kill-switch + existing risk gate wiring remains primary.

### J) Governance Evidence + Determinism
- EvidencePack runtime already deterministic; extend to ensure CMES facts hashed deterministically:
  - store canonical facts hash in run metadata or audit artifact.

### K) Tests — Unit + Contract + E2E
1) `tests/risk/test_cmes_facts_canonicalization.py`
   - required keys present
   - sorted lists canonical
   - invalid enum/type rejected
2) `tests/ingress/test_feature_view_contains_cmes_facts.py`
   - feature view has facts; pointer-only scan passes
3) `tests/ingress/test_evidence_capsule_contains_cmes_facts.py`
   - capsule has facts; pointer-only scan passes
4) `tests/governance/test_cmes_no_raw_keys_contract.py`
   - forbidden keys absent in generated artifacts
5) `tests/e2e/test_ingress_to_l3_with_cmes_facts.py`
   - run_ingress(empty) => capsule with facts
   - feed capsule to L3 dry-run => artifacts created, no raw
6) `tests/risk/test_l5_adapter_determinism.py`
   - same facts => same decision + same reason codes ordering

### L) CI Gates
- ruff format/check
- run suites:
  - ingress
  - governance
  - ai_orchestration (L3)
  - e2e (ingress→l3)
  - risk (new CMES tests)

### M) Evidence Bundle (Local, Non-Repo)
- one-shot evidence script:
  - generate ingress artifacts + l3 artifacts
  - pointer-only scan
  - canonical facts hash
  - tarball + sha256 copied to ~/Downloads

### N) Closeout
- Merge PR, delete branch
- main health checks green
- snapshot /tmp and ~/Downloads

**Implementation complete (A→L):** CMES facts module, reason codes, FeatureView/EvidenceCapsule wiring, L5 adapter, all tests (unit, contract, e2e), evidence bundle script at `scripts/ops/cmes_evidence_bundle.py`.

## Operator Commands (Canonical)
### Dev loop
- `python3 -m ruff format src tests scripts`
- `python3 -m ruff check .`
- `python3 -m pytest -q tests/risk tests/ingress tests/governance tests/ai_orchestration tests/e2e`

### Pointer-only scan helper
- `rg -n "payload|raw|transcript|api_key|secret|token|content" <DIR>`
