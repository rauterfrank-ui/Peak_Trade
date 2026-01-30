## Slice 3: BetaEventBridge → LedgerEngine (deterministisch)

### Ziel
Deterministische Brücke von Slice‑1 `beta_events` (Schema `BETA_EXEC_V1`) in die Slice‑2 `LedgerEngine` inkl. stabiler Export‑Artefakte (JSON/JSONL) für Reporting/CI‑Regressionen.

### Invarianten (MUST)
- **Determinism**: Gleiche Inputs (Events + Price‑Refs + Config) → **byte‑identische Artefakte**.
- **No wall‑clock / randomness**: Bridge erzeugt **keine** `datetime.now()`, `time.time()`, `uuid4()`, `random.*`.
- **Stable ordering**: Events werden **explizit** sortiert nach `(t, rank, seq, event_id)`.
- **Replay‑safe**: Dedupe per `event_id` (erste Instanz nach Sortierung gewinnt).
- **Float discipline**: **keine** `float` in normalisierten Events/Artefakten (Hard Error).
- **Canonical JSON**: `sort_keys=True`, `separators=(",", ":")`, UTF‑8, `\n` als Zeilenende.
- **Keine env‑Felder**: Artefakte enthalten keine absoluten Pfade/Hostnames/Environment‑abhängige Metadaten.

### Implementierung
Package: `src/execution/bridge/`

- **Bridge**: `BetaEventBridge`
  - Input: `beta_events: Iterable[dict]` (in‑memory)
  - Normalisierung: Schema `{event_type,t,seq,source,payload,event_id}` (ohne Floats)
  - Output (via Sink) unter `out&#47;<run_fingerprint>&#47;...`:
    - `normalized_beta_events.jsonl`
    - `ledger_applied_events.jsonl`
    - `ledger_final_state.json`
    - optional: `equity_curve.jsonl` (wenn `emit_equity_curve=True`)

- **Reporting Hook / Sink**: `FileSystemArtifactSink`
  - schreibt **atomar** (tmp + rename) **exakt** die Bytes, die die Bridge erzeugt
  - **run_fingerprint**: siehe `src/execution/bridge/run_fingerprint.py`

### Artefakt‑Contract (Dateinamen + Inhalte)
- **`normalized_beta_events.jsonl`**: kanonisierte, sortierte, deduplizierte BetaEvents (Schema `{event_type,t,seq,source,payload,event_id}`).
- **`ledger_applied_events.jsonl`**: pro Event eine Zeile mit `{event_id,t,seq,event_type,applied}`.
- **`ledger_final_state.json`**: deterministischer Ledger‑State (Integer‑Contract, siehe unten).
- **`equity_curve.jsonl`** (optional): Snapshots (Integer) nach jedem N‑ten Event.
  - Snapshot-Schema (Golden Contract): `{t, seq, symbol, price_int, cash_int, equity_int, qty_int, avg_price_int, fees_paid_int, realized_pnl_int, unrealized_pnl_int, state_hash}`

### Default `event_type_rank`
Fixe Mapping‑Defaults (Override nur via Config):

- `Price`: 0
- `OrderIntent`: 10
- `OrderRequest`: 20
- `Order`: 30
- `Fill`: 40
- `Cancel`: 50
- `Reject`: 60
- `Adjustment`: 70
- `Fee`: 80
- `SnapshotMarker`: 90
- Unbekannt: 999

### `seq` Ableitung (wenn fehlt)
1) Nach Normalisierung: **stable sort** nach `(t, rank, original_index)`
2) `seq = 0..n-1` in genau dieser Reihenfolge
3) **Dann** `event_id = sha256(canonical_json({event_type,t,seq,source,payload}))`
4) Replay‑Sort: `(t, rank, seq, event_id)`

### Scales (Defaults in Tests)
- `money_scale = 10000` (1 Tick = 0.0001 Währungseinheit)
- `price_scale = 10000` (1 Tick = 0.0001 Preis)
- `qty_scale = 1`

### LedgerEngine State Contract (Minimum)
`ledger_final_state.json` enthält ausschließlich:
- `version` (int)
- `base_ccy` (str)
- `money_scale` / `price_scale` / `qty_scale` (int)
- `cash_int`, `equity_int` (int)
- `positions`: `dict[str, {"qty_int": int, "avg_price_int": int}]`
- `realized_pnl_int`, `unrealized_pnl_int`, `fees_paid_int` (int)
- `last_price_by_symbol`: `dict[str,int]` (price_int)

Rechenregel (deterministisch, Integer‑Math):
\[
equity\_int = cash\_int + \sum\_s \left\lfloor \frac{qty\_{int}(s)\cdot last\_price\_{int}(s)\cdot money\_scale}{price\_scale\cdot qty\_scale}\right\rfloor_{\text{toward 0}}
\]

### Safety rails (wichtig)
- Die Slice‑3 Regressionstests verwenden eine **deterministische Referenz‑Engine** `IntLedgerEngine` (Integer‑State‑Contract) ausschließlich für **CI/Artefakt‑Determinismus**.
- Die Production‑Engine `src.execution.ledger.LedgerEngine` bleibt **unverändert** und wird hier nicht automatisch “umgeschaltet”.

### Usage (minimal)

```python
from pathlib import Path
from src.execution.bridge import BetaEventBridge, BetaEventBridgeConfig, FileSystemArtifactSink
from src.execution.bridge.int_ledger_engine import IntLedgerEngine

eng = IntLedgerEngine(base_ccy="USD", money_scale=10000, price_scale=10000, qty_scale=1, cash_int=10_000_000)

bridge = BetaEventBridge(
    eng,
    prices_manifest_or_ref={"prices_ref": "sha256:..."},
    config=BetaEventBridgeConfig(emit_equity_curve=False),
)

bridge.run(
    beta_events=[{"event_type": "Price", "t": 0, "payload": {"symbol": "ACME", "price_int": 123450000}}],
    sink=FileSystemArtifactSink(Path("artifacts")),
)
```

### Tests

```bash
python3 -m pytest -q tests/execution/test_beta_event_bridge_determinism.py
python3 -m pytest -q tests/execution/test_beta_event_bridge_ordering.py
```

### Golden Regression (Equity Curve)

#### Was ist “Golden”?
- **Golden** ist ein **byte-identischer Referenz-Output** (`equity_curve.jsonl`) für einen **fixierten Minimal-Fixture-Input**.
- Ziel: Jede unbeabsichtigte Änderung an Snapshot-Format, Ordering, Scales oder Persistenz (z.B. Float-Leaks) wird in CI als Regression sichtbar.

#### Welche Dateien sind Golden?
- `tests/golden/slice3_equity_curve_minimal.jsonl` (kanonisches JSONL, **LF-only**)
- optional: `tests/golden/slice3_artifact_manifest_minimal.json` (Liste `{relpath, sha256}` für **alle** deterministischen Artefakte unter `out&#47;<fingerprint>&#47;...`)

#### Wie wird Golden aktualisiert? (explizite Operator-Aktion)
Golden wird **niemals automatisch** in CI aktualisiert. Update ist ein bewusster Operator-Schritt:

```bash
python3 scripts/testing/update_slice3_golden.py --fixture tests/fixtures/slice3_beta_events_minimal.jsonl
```

#### Strikte Invarianten (Review-Checklist)
- **No wall-clock / randomness**: kein `datetime&#47;time&#47;uuid&#47;random` im Slice‑3 Bridge-Pfad.
- **Canonical JSON**: `sort_keys=True`, `separators=(",", ":")`, UTF‑8, **`\n`** Zeilenende.
- **Integer-only persistence**: keine Floats in Artefakten; State/Snapshots persistieren Integer (oder explizit Strings, niemals float).
- **Stable ordering**: deterministische Sortierung (Events & Position-Keys).
- **Stable filenames**: Artefakt-Relpaths stabil; `run_fingerprint` hängt **nur** von normalisierten Event-Bytes + Manifest/Refs + Config ab.
- **Golden Review**: bei Änderungen an Golden immer prüfen:
  - Ist die Änderung fachlich beabsichtigt?
  - Sind die Diffs rein format-/contract-relevant (nicht “zufällig”)?
  - Läuft `scripts/testing/update_slice3_golden.py` zweimal hintereinander **identisch**?

### Annahmen
- Bridge persisted ausschließlich Integer‑State (no floats).
