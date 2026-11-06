# Update Officer v9 – Operator presets (read-only)

## Goal
Add **controlled, read-only** operator presets on **`GET &#47;ops`** so Update Officer source
selection stays **explicit and query-driven** while making common navigation patterns easier.
Presets **do not** discover paths, **do not** change v7 resolution rules, and **do not** add POST
or persistence beyond the URL.

## What changed vs v8
- **`GET &#47;ops`** HTML adds an **Operator presets (GET-only)** toolbar inside the Update Officer
  source-selection card:
  - **Default — clear query** → `&#47;ops` with no parameters
  - **Manual — keep current inputs** → preserves typed fields with `update_officer_source_preset=manual`
  - **Notifier path focus** → sets `update_officer_source_preset=notifier_path` and **omits**
    `update_officer_run_dir` from the URL (still passes notifier path if present in the form)
  - **Run directory focus** → sets `update_officer_source_preset=run_dir` and **omits**
    `update_officer_notifier_path` from the URL (still passes run directory if present)
- **Active preset** summary (manual &#47; notifier path &#47; run directory) reflects the normalized
  `update_officer_source_preset` query value.
- The main **Apply source (GET)** form includes a **hidden** `update_officer_source_preset` field
  so preset context survives a normal GET submit.
- **`GET &#47;api&#47;ops-cockpit`** ignores preset (JSON contract unchanged).

## Query parameters
| Parameter | Meaning |
|-----------|---------|
| `update_officer_notifier_path` | Path to `notifier_payload.json` (v7) |
| `update_officer_run_dir` | Directory containing `notifier_payload.json` (v7) |
| `update_officer_source_preset` | Optional ergonomics label: `manual`, `notifier_path`, `run_dir` (unknown → `manual`) |

v7 rules unchanged: trim inputs; **both** notifier path and run dir non-empty → deterministic
conflict empty-state. Presets are **informational** for operators; they do not bypass conflict
detection.

## GET-only stance
- All preset affordances are **anchors** or the existing **GET** form — navigation only.
- **No** `method="post"` on this surface.

Illustrative URLs (fenced):

```text
/ops
/ops?update_officer_source_preset=notifier_path
/ops?update_officer_source_preset=run_dir&update_officer_run_dir=/abs/path/to/run_dir
```

Inline path shape (token-policy safe): `out&#47;ops&#47;update_officer&#47;&lt;run&gt;&#47;notifier_payload.json`

## Guardrails
- Read-only: no dependency bumps, no lockfile writes, no paper&#47;shadow&#47;evidence mutation.
- No background jobs, no autonomous source discovery, no external transport, no UI write actions,
  no server-side persistence of operator selections.

## Implementation references
- `normalize_update_officer_source_preset()`, `_render_update_officer_source_ergonomics_block()` in
  `src/webui/ops_cockpit.py`
- `GET &#47;ops` in `src/webui/app.py` (optional `update_officer_source_preset` query parameter)

## Verification
```bash
python3 -m pytest -q tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff check src/webui/app.py src/webui/ops_cockpit.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff format --check src/webui/app.py src/webui/ops_cockpit.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 scripts/ops/validate_docs_token_policy.py --changed --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

## Version
- v9 builds on v8 operator source selection with **deterministic, URL-transparent** presets only.
