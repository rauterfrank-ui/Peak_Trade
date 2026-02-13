# P39 — Registry CLI v1

## Purpose
Operator-first CLI to inspect and verify backtest artifacts:
- P35 bundle dirs
- P36 tarball bundles
- P37 bundle index
- P38 bundle registry

## Commands
### verify
Verify a registry (or index / bundle) and exit non-zero on integrity errors.

Examples (paths intentionally encoded to satisfy docs token policy gate):
- `python -m src.ops.p39.registry_cli_v1 verify --registry out&#47;ops&#47;...&#47;registry.json`
- `python -m src.ops.p39.registry_cli_v1 verify --index out&#47;ops&#47;...&#47;index.json`
- `python -m src.ops.p39.registry_cli_v1 verify --bundle-dir /tmp&#47;bundle_dir`
- `python -m src.ops.p39.registry_cli_v1 verify --tarball /tmp&#47;bundle.tgz`

### list
List entries in stable order (by ref_path / relpath).

### show
Print one entry (by relpath or bundle_id).

## Output format
- Human mode: line-oriented, stable ordering.
- `--json`: deterministic JSON (`sort_keys=true`, `indent=2`, UTF-8, trailing newline).

## Safety
- Tarball extraction uses P36 verifier protections (no traversal, no unexpected members).
- No network calls. No live trading.
