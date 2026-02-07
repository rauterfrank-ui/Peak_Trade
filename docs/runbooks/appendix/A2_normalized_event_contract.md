# Phase A2 – NormalizedEvent Contract (Minimal)

## Schema
- `event_id: str`
- `ts_ms: int` (epoch ms)
- `source: str`
- `kind: str`
- `scope: str`
- `tags: list[str]`
- `sensitivity: "public"|"internal"|"restricted"`
- `payload: object` (JSON-serializable)

## Storage
- Append-only JSONL: `<base>.jsonl`
- Manifest: `<base>.manifest.json`
  - `file_sha256`: sha256 over full JSONL bytes
  - `chain_head`: rolling sha256 chain over lines (prev_chain + line_sha256)

## Determinism rules
- JSON serialization: sorted keys, separators `,`/`:`, UTF-8, `allow_nan=false`.

## Validation
- `src&#47;ingress&#47;validate.py`: minimal contract checks (types, non-empty strings, sensitivity enum).
