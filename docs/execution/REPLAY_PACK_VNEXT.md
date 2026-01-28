# EXEC_SLICE3 — Deterministic Replay Pack vNext (v1 vs v2)

## Ziel
ReplayPack soll deterministisch **zwei Bundle-Versionen** unterstützen:

- **v1 (legacy)**: unverändert; bestehende golden Bundles/Hashes dürfen **nicht** ändern.
- **v2 (additiv)**: v1 **plus** FIFO Slice2 Ledger-Artefakte (neue Dateien), deterministisch und hash-validierbar.

**NO-LIVE HARD:** ReplayPack ist offline-only; keine Broker/Exchange Writes.

## Invarianten (Determinismus)
- **Keine Wall-Clock-Zeit** in Artefakten: `created_at_utc` ist injizierbar (`created_at_utc_override`) oder aus dem deterministischen Event-Stream abgeleitet.
- **Stabile Ordnung**: `events&#47;execution_events.jsonl` ist deterministisch sortiert; `seq` ist contiguous ab 0.
- **Canonical JSON/JSONL**:
  - JSON: sortierte Keys, keine Whitespace-Separators, UTF-8, `\n` am Ende.
  - JSONL: ein Objekt pro Zeile, canonical JSON pro Zeile, LF-only, `\n` am Ende.
- **Keine Floats** in Artefakten (hard fail).
- **Hashes**:
  - `hashes&#47;sha256sums.txt` listet deterministisch alle Files im Bundle (außer sich selbst).
  - `manifest.json.contents` listet deterministisch alle Content-Files (ohne `manifest.json` und ohne `hashes&#47;sha256sums.txt`), sortiert nach `path`.

## Bundle Layout
Bundle root bleibt: `replay_pack&#47;`

### v1 (legacy)
Required:
- `manifest.json`
- `events&#47;execution_events.jsonl`
- `hashes&#47;sha256sums.txt`

Weitere Dateien sind optional (z.B. `inputs&#47;`, `meta&#47;`, `outputs&#47;`).

### v2 (additiv)
Alles aus v1 **plus**:
- `ledger&#47;ledger_fifo_snapshot.json` (**required in v2**)
- `ledger&#47;ledger_fifo_entries.jsonl` (optional; Debug/Tracing)

## FIFO Slice2 Ledger Ableitung (v2)
- Quelle ist ausschließlich `events&#47;execution_events.jsonl` (BETA_EXEC_V1).
- Es werden **nur** `event_type == "FILL"` verarbeitet.
- **Keine MARK-Synthese** (keine impliziten Marks).
- Mapping:
  - `instrument` = `symbol` (z.B. `BTC&#47;EUR`)
  - `base_ccy` = Quote-Currency aus `symbol` (z.B. `EUR`)
  - `ts_utc` wird aus `event_time_utc` abgeleitet und auf **UTC `Z`** normalisiert
  - `seq` wird übernommen
  - `qty&#47;price&#47;fee` werden strikt als `Decimal` aus Strings geparsed

## Build API (Python)
`src&#47;execution&#47;replay_pack&#47;builder.py`:

- v1 (default):
  - `build_replay_pack(run_dir, out_dir, created_at_utc_override=..., include_outputs=False)`
- v2:
  - `build_replay_pack(run_dir, out_dir, bundle_version="2", include_fifo=True, include_fifo_entries=True, created_at_utc_override=...)`

## Validation
`validate_replay_pack(bundle_root)`:
- Wenn `manifest.contract_version` fehlt oder `"1"`: v1 validation (legacy) – unverändert.
- Wenn `"2"`: v1 validations **+** FIFO-Artefakte:
  - `ledger&#47;ledger_fifo_snapshot.json` muss existieren und canonical sein
  - optional `ledger&#47;ledger_fifo_entries.jsonl` muss canonical JSONL sein, falls vorhanden

## No-Regressions Checklist (v1 schützen)
- [ ] v1 Builder-Aufruf ohne neue Parameter erzeugt **identische** `manifest.json` + `hashes&#47;sha256sums.txt` (golden tests).
- [ ] v2 fügt nur neue Files hinzu; gemeinsame legacy Files sind byte-identisch zu v1:
  - `events&#47;execution_events.jsonl`
  - `inputs&#47;config_snapshot.json`
  - `meta&#47;git.json`
  - `meta&#47;env.json`
- [ ] Tests: v1 goldens bleiben unverändert; v2 determinism + schema checks neu.

## CLI (Operator UX)
Empfohlenes Tool ist das vorhandene deterministische CLI-Skript:

```bash
# Help
uv run python scripts/execution/pt_replay_pack.py --help
uv run python scripts/execution/pt_replay_pack.py build --help
```

### Build (v1)

```bash
uv run python scripts/execution/pt_replay_pack.py build \
  --events /abs/path/to/execution_events.jsonl \
  --out /abs/path/to/out_dir \
  --version 1 \
  --created-at-utc 2000-01-01T00:00:00+00:00
```

### Build (v2, additive FIFO)

```bash
uv run python scripts/execution/pt_replay_pack.py build \
  --events /abs/path/to/execution_events.jsonl \
  --out /abs/path/to/out_dir \
  --version 2 \
  --include-fifo-entries \
  --created-at-utc 2000-01-01T00:00:00+00:00
```

### Validate

```bash
uv run python scripts/execution/pt_replay_pack.py validate --bundle /abs/path/to/out_dir/replay_pack
```

### Inspect (hash/metadata/files)

```bash
# Human-readable
uv run python scripts/execution/pt_replay_pack.py inspect --bundle /abs/path/to/out_dir/replay_pack

# Machine-readable JSON (stable ordering)
uv run python scripts/execution/pt_replay_pack.py inspect --bundle /abs/path/to/out_dir/replay_pack --json
```

## Troubleshooting

### HashMismatchError
- **Symptom**: `HashMismatchError` beim `validate`.
- **Cause**: Bundle wurde nachträglich verändert oder nicht deterministisch geschrieben.
- **Fix**: Bundle neu bauen; sicherstellen, dass keine CRLF-Newlines oder Editor-Autoformatierung die Files verändert.

### Missing FIFO snapshot (v2)
- **Symptom**: `manifest.contents must include ledger&#47;ledger_fifo_snapshot.json for v2` oder missing file.
- **Cause**: v2 Build ohne FIFO oder Bundle unvollständig kopiert.
- **Fix**: v2 Build mit `--version 2` ausführen (FIFO snapshot ist required in v2).
