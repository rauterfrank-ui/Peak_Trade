# Evidence — ReplayPack v2 CLI Verify — PASS

**Date:** 2026-01-28  
**Result:** PASS  
**Scope:** ReplayPack v2 CLI (`build`, `validate`, `inspect`) — deterministic, offline-only (NO-LIVE)

---

## Pre-flight

```bash
pwd
git status -sb
```

```text
<repo_root>
## main...origin/main
```

---

## CLI — Build v2 (minimal fixture)

Create a minimal `BETA_EXEC_V1` events file (single `FILL` line):

```bash
python3 - <<'PY'
import json

event = {
  "schema_version": "BETA_EXEC_V1",
  "event_id": "ev_min_001",
  "run_id": "run_cli_v2_verify_001",
  "session_id": "s",
  "intent_id": "i",
  "symbol": "BTC/EUR",
  "event_type": "FILL",
  "ts_sim": 0,
  "ts_utc": "2026-01-01T00:00:00+00:00",
  "request_id": None,
  "client_order_id": "order_001",
  "reason_code": None,
  "reason_detail": None,
  "payload": {
    "fill_id": "fill_0",
    "side": "BUY",
    "quantity": "0.01000000",
    "price": "50000.00000000",
    "fee": "0.50000000",
    "fee_currency": "EUR",
  },
}

with open("tmp_replay_pack_v2_events.jsonl", "w", encoding="utf-8", newline="\n") as f:
  f.write(json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
print("WROTE tmp_replay_pack_v2_events.jsonl")
PY
```

Build v2 bundle (deterministic timestamp override + include FIFO entries):

```bash
python3 scripts/execution/pt_replay_pack.py build \
  --events tmp_replay_pack_v2_events.jsonl \
  --out tmp_replay_pack_v2_out \
  --version 2 \
  --include-fifo-entries \
  --created-at-utc 2000-01-01T00:00:00+00:00
```

Expected output:

```text
<no output on success>   # exit code 0
```

---

## CLI — Validate

```bash
python3 scripts/execution/pt_replay_pack.py validate --bundle tmp_replay_pack_v2_out/replay_pack
```

Expected output:

```text
<no output on success>   # exit code 0
```

---

## CLI — Inspect (Text)

```bash
python3 scripts/execution/pt_replay_pack.py inspect --bundle tmp_replay_pack_v2_out/replay_pack
```

Output snippet (example; hashes/IDs vary by content):

```text
ReplayPack Inspect
bundle: <abs_path>/tmp_replay_pack_v2_out/replay_pack
contract_version: 2

files:
  manifest.json: present
  hashes/sha256sums.txt: present
  events/execution_events.jsonl: present
  ledger/ledger_fifo_snapshot.json: present
  ledger/ledger_fifo_entries.jsonl: present

hashes:
  sha256sums_count: <int>
  manifest_sha256: <64hex>

events:
  lines: 1

fifo:
  has_fifo_ledger: true
  fifo_engine: null
  last_ts_utc: 1970-01-01T00:00:00Z
  last_seq: 0
  entries_lines: <int>
```

---

## CLI — Inspect (`--json`)

```bash
python3 scripts/execution/pt_replay_pack.py inspect --bundle tmp_replay_pack_v2_out/replay_pack --json
```

Output snippet (keys are stable; values vary):

```json
{
  "bundle": "<abs_path>/tmp_replay_pack_v2_out/replay_pack",
  "contract_version": "2",
  "files": {
    "manifest_json": true,
    "sha256sums_txt": true,
    "execution_events_jsonl": true,
    "ledger_fifo_snapshot_json": true,
    "ledger_fifo_entries_jsonl": true
  },
  "hashes": {
    "sha256sums_count": 6,
    "manifest_sha256": "<hex>"
  },
  "events": { "lines": 1 },
  "fifo": {
    "has_fifo_ledger": true,
    "fifo_engine": null,
    "last_ts_utc": "1970-01-01T00:00:00Z",
    "last_seq": 0,
    "entries_lines": 1
  }
}
```

---

## Notes / Risk

- NO-LIVE: ReplayPack CLI is offline-only; no broker/exchange writes.
- Determinism: No wall-clock in `inspect`; stable ordering and stable JSON keys; `--created-at-utc` override used.
- Token safety: No secrets printed; output snippets use placeholders for paths/hashes.
