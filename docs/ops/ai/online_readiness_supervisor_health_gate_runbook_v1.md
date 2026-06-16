# Online Readiness — Supervisor Health Gate v1 (P79)

## Purpose
Validate supervisor health in one of two **mutually exclusive** modes:

1. **Runtime tick mode** — P78 supervisor (or P77 daemon) is healthy: ticks are recent, pidfile is valid (if present), and P76 artifacts exist per tick.
2. **Offline archive mode** — packed supervisor evidence from `pack_online_readiness_supervisor_evidence_v0.py` has valid `supervisor_session_closeout_v0.json` and verifiable `MANIFEST.sha256` (non-authorizing; no supervisor/daemon start).

## Runtime tick mode

### Prerequisites
- `OUT_DIR` contains `tick_*` subdirs (from P78 supervisor)
- Each tick dir should have at least one of: `P76_RESULT.txt`, `ONLINE_READINESS_ENV.json`, `P71_GATE.log`, `P72_PACK.log`, `readiness_report.json`, `manifest.json`

### Invocation
```bash
MODE=shadow OUT_DIR=/path/to/supervisor/out MAX_AGE_SEC=300 \
  bash scripts/ops/p79_supervisor_health_gate_v1.sh
```

### Evidence
- `OUT_DIR&#47;p79_health_gate_v1.json` — JSON with mode, newest_tick, age_sec, etc.

## Offline archive evidence-pack mode

### Prerequisites
- `ARCHIVE_ROOT` is the durable archive root produced by `pack_online_readiness_supervisor_evidence_v0.py`
- `supervisor_session_closeout_v0.json` present with successful pack `exit_code`
- `MANIFEST.sha256` present and verifiable via shared `verify_manifest_sha256()`

### Invocation
```bash
ARCHIVE_ROOT=/path/to/supervisor/evidence/archive \
  bash scripts/ops/p79_supervisor_health_gate_v1.sh
```

Direct helper (same semantics):

```bash
python3 scripts/ops/p79_supervisor_evidence_manifest_verify_v0.py \
  --archive-root /path/to/supervisor/evidence/archive
```

### Evidence
- `ARCHIVE_ROOT&#47;p79_health_gate_v1.json` — JSON with `gate_mode: archive_evidence_pack`, `manifest_verified`, `evidence_non_authorizing: true`

## Exit Codes
- `0` — gate OK
- `2` — usage/config error (missing MODE/OUT_DIR, invalid mode, ARCHIVE_ROOT + OUT_DIR both set)
- `3` — gate failed (stale ticks, stale pidfile, missing artifacts, or archive manifest/closeout failure)

## Non-authorizing
P79 success means structural health or evidence-pack integrity only. It does **not** clear HOLD, preflight BLOCKED, or grant Live/Testnet/broker authority.
