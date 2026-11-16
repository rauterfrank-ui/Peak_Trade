# Governed Runtime Primary → Offline Observation Projection v1

```text
WORKPACKAGE_ID=GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1
PROJECTION_AUTHORITY=NONE
PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION=false
P5_EVIDENCE_INTAKE_IMPLIES_PRODUCTIVE_AUTHORIZATION=false
P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY=false
RUNTIME_APPLY_STARTED=false
EXTERNAL_EFFECT=false
```

Owner:

- `src/governance/governed_runtime_primary_to_offline_observation_projection_v1.py`

Purpose:

Mechanically project **preexisting durable validated** Paper / Shadow / Testnet primary
evidence into the existing offline observation / research evidence plane. This is a
**projection / normalization boundary** only.

This component is **not** a runtime executor, primary evidence producer, trading/risk/
promotion/apply owner, or Testnet/Live runner.

## Direction

```text
PREEXISTING DURABLE PRIMARY EVIDENCE (PAPER | SHADOW | TESTNET)
  → validate_durable_primary_evidence_root (scripts.ops.primary_evidence_retention_v0)
  → canonical runtime-primary identity / provenance binding
  → GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1
  → OfflineExperimentObservationsV1 + identity-bound offline observation binding
  → runtime_observation_feedback_v1 (runtime_to_learning_input_v1 ingress)
  → existing M4–M8 research return loop (fixture-bounded proof)
```

Reuse:

- `scripts/ops/primary_evidence_retention_v0.py`
- `src/experiments/canonical_identity_bound_offline_observation_binding_v1.py`
- `src/meta/learning_loop/runtime_observation_feedback_v1.py`
- `src/experiments/canonical_m4_m8_evidence_return_loop_v1.py`

Field-level adjudication:

- `config/governance/governed_runtime_primary_to_offline_observation_projection_v1_field_mapping_ledger_v1.json`

## Fail closed

Reject projection when source archive is missing, under `/tmp`, fails durable validation,
manifest verify fails, unsupported mode, mode mismatch, missing mandatory run/session
identity, instrument, observation time, or config identity where required by source mode.

Do not fabricate missing downstream fields. Do not mutate primary evidence archives.

The original `MANIFEST.sha256` must cover each file required by the selected
archive contract. Its entries resolve to regular files at their declared
paths inside the archive. The projection records `MANIFEST.sha256` and the
mode-specific evidence manifest as `STORE_RELATIVE` artifact references. Resolve
them against `source_archive_root_ref` in the projection provenance and verify
the recorded digests. This works with the original durable archive outside the
checkout, without staging a copy in Git. Archive integrity and a PASS review
do not establish the provenance of an individual outcome or fill.

## I17 Shadow outcomes

`GovernedI17ShadowProjectionRequestV1` admits a completed Shadow handoff
through its original I17 session, O4 Mark archive, outcome receipt and DDO
ledger. The projection and optimization binding both use the original I17
verifier in readback mode. The expected handoff digest is required.
This offline intake expects the source class `DECLARED_OFFLINE_DATA`.

The canonical optimization-input validator receives the original Learning
Evidence. The binding also returns the original measurement receipt. Its
decision identity, knowledge time, `SHADOW_COUNTERFACTUAL`, `N_BARS` and
`LOG_RETURN` keep the semantics of a dimensionless public Mark-price
measurement. The source verifier retains the decision-time and evaluation-time
inputs and rechecks the selected O4 window.

```bash
./scripts/pt scripts/ops/run_offline_ddo_learning_follow_up_v1.py \
  --root /absolute/i17-learning --cycle i17 verify-shadow-g2 \
  --shadow-evidence /absolute/i17-session/evidence \
  --o4-mark-archive /absolute/o4 --shadow-outcome-receipt /absolute/shadow-outcome.json \
  --shadow-handoff-digest '<digest>'
```

## Closed Paper episodes

`GovernedPaperEpisodeProjectionRequestV1` admits a selected closed episode
from its original Paper archive and persisted DDO handoff. Pass the typed
projection to `bind_from_g2_projection_result_v1`. It rechecks the archive,
simulated fills, accounting and DDO readback before forwarding the original
Learning Evidence to the canonical optimization-input validator. The
binding retains the verified measurement with the net PnL and its quote
currency, entry decision, episode close time and outcome digest. The
optimization acknowledgement binds the digest of the original Learning
Evidence. The complete measured outcome is available through that evidence's
outcome reference and the verified handoff.

```bash
./scripts/pt scripts/ops/read_bounded_paper_episode_outcome_v1.py \
  --run-root /absolute/paper-run --episode-id 'simulated-accounting:<digest>' \
  --verify-g2-handoff-root /absolute/paper-learning
```

## M10 / P5 isolation

Primary runtime evidence and this projection output do **not** authorize M10 promotion,
runtime apply, or P5 productive ingress. P5 bridges remain separate optional downstream
producers only.
