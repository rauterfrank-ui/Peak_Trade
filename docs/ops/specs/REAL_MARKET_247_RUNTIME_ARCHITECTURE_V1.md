# Real Market 24/7 Runtime Architecture v1

## Purpose

This document defines the runtime contract for a future always-on or near-always-on Paper/Shadow real-market evidence runner.

It exists to prevent blind AWS/IAM/S3 expansion before the runtime responsibilities, evidence contract, and safety boundaries are explicit.

**Authority:** This is a design and navigation spec. It does not grant go-live, testnet, bounded pilot, or Master V2 handoff. Governance and explicit gates remain canonical elsewhere.

## Current proven baseline

The repository currently has a GitHub Actions based real-market evidence baseline:

- `Real Market Forward Evidence Smoke`
- `workflow_dispatch`
- scheduled every 6 hours via cron
- uses Kraken historical-real OHLCV
- validates `market_data_provenance_v1`
- uploads GitHub Actions artifacts
- does not place orders
- does not use S3/rclone/IAM in the workflow

This is laptop-independent scheduled evidence, not a permanent 24/7 daemon.

## Target runtime classes

### Class A: Scheduled evidence runner

A scheduled runner executes periodically, for example every 15 minutes, hourly, or every 6 hours.

Examples:

- GitHub Actions schedule
- AWS EventBridge rule invoking a job
- AWS Batch job
- ECS/Fargate task on schedule
- VPS cron/systemd timer

Use this class first.

### Class B: Durable 24/7 daemon

A durable daemon keeps a long-running Paper/Shadow process alive.

Examples:

- ECS/Fargate service
- EC2 or VPS systemd service
- long-running Data Node container

Use this class only after scheduled evidence is stable and the operational contract is proven.

## Non-negotiable safety boundaries

The runtime must not unlock live trading.

Required boundaries:

- no order placement
- no live broker/exchange execution
- no testnet/live promotion authority
- no Master V2 / Double Play governance bypass
- no secret logging
- no broad S3 bucket permissions
- no mutable registry writes without explicit artifact integrity
- no local laptop dependency

Dry-run execution is allowed. Realness is about market data provenance, not execution mode.

## Real-market evidence contract

Every evidence run must produce a manifest or summary containing at least the following invariants (field names as produced by the forward-evaluation path today):

```text
market_data_provenance.schema_version == market_data_provenance_v1
source_kind in {"historical_real", "real"}
provider / exchange / ohlcv_source metadata present
symbols present
timeframe present
n_bars or equivalent sample count present
fetched_at_utc or equivalent retrieval timestamp present
is_synthetic == false
is_fixture == false
dry_run_execution == true
```

The workflow or runner must fail closed if any required field is missing or contradicted. Synthetic/negative-control paths remain CI-only, not production evidence.

## Staged rollout (recommended)

1. **Prove scheduled Class A** on a small cadence in a managed environment (e.g. GHA, then optionally cloud scheduler) with the same contract as the forward smoke.
2. **Add observability** (run id, duration, success/fail, rate-limit signals) before tightening cadence.
3. **Optionally** attach export to S3 or registry in a follow-on slice, with read-after-verify and least-privilege object prefixes—only after the manifest contract is stable.
4. **Consider Class B** (daemon) only if continuous near-real-time read-only state is required and Class A is insufficient.

## Optional future extensions (out of scope for v1)

- Streaming or websocket-based provenance (different `source_kind` and schema revision).
- Cross-region redundancy for the evidence runner.
- Tighter coupling to registry pointers—must not blur authority between documentation and go-live.

## Related repository surfaces

- Forward evaluation and provenance: `scripts/evaluate_forward_signals.py`, `scripts/_market_data_provenance.py`
- GHA: `.github/workflows/real-market-forward-evidence-smoke.yml`
- Data node / long-running operation (documentation context): `docs/ops/runbooks/PHASE_T_DATA_NODE_EXPORT_CHANNEL.md`, `docs/SCHEDULER_DAEMON.md`

## Document control

- **Version:** v1
- **Change discipline:** Any runtime that alters the evidence contract or safety boundaries should bump version or add an explicit addendum, not silently extend this file.
