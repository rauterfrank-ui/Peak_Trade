# Phase A6 – Ingress CLI

## Purpose
Module entrypoint to run the ingress pipeline (A2→A4). Prints absolute paths of produced artifacts; exit 0 on success, nonzero on error. Pointer-only: no raw content in outputs.

## Invocation
```bash
python -m src.ingress.cli.ingress_cli [options]
```

## Options
- `--run-id ID` — run identifier (default: timestamp-pid)
- `--input-jsonl PATH` — path to input JSONL (optional; empty ok)
- `--base-dir PATH` — base directory for views and capsules (default: `out/ops`)
- `--label KEY=VALUE` — repeatable; added to labels dict passed to `run_ingress`

## Output
- On success: two lines to stdout — absolute path to feature_view JSON, then absolute path to capsule JSON.
- Exit code: 0 on success (including empty input); 1 on unexpected error.

## Implementation
- `src&#47;ingress&#47;cli&#47;ingress_cli.py`

## Guardrail
- CLI does not emit or persist payload, raw, transcript, api_key, secret, or token.
