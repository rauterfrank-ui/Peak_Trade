# Update Officer v8 – Operator source selection ergonomics

## Goal
Add **visible, read-only** operator affordances on the Ops Cockpit so explicit Update Officer
sources are easier to set **without** changing v7 resolution rules: still **no** latest-run
scanning, **no** writes, **no** POST.

## What changed vs v7
- **`GET &#47;ops`** HTML includes an **Update Officer source selection** block:
  - **Active source** summary (none / explicit path / run directory / conflict)
  - **`method="get"`** form targeting **`&#47;ops`** with the same query parameter names as v7
  - **Clear** link to **`&#47;ops`** with no query (deterministic reset to empty-state)
- **`GET &#47;api&#47;ops-cockpit`** is unchanged (JSON only; no ergonomics block).

## Query parameters (unchanged from v7)
| Parameter | Meaning |
|-----------|---------|
| `update_officer_notifier_path` | Path to `notifier_payload.json` |
| `update_officer_run_dir` | Directory containing `notifier_payload.json` |

Rules match v7: trim inputs, **both non-empty** → deterministic conflict empty-state; **neither**
→ safe empty-state; **one** → explicit resolution via the consumer layer.

## GET-only stance
- Form uses **`method="get"`** only — navigation with query string, **no** server-side mutation.
- **No** `method="post"` on this surface.
- Submit control is **GET navigation**, not a write action.

Illustrative URLs (fenced):

```text
/ops
/ops?update_officer_notifier_path=/abs/path/to/notifier_payload.json
/ops?update_officer_run_dir=/abs/path/to/run_dir
```

Inline path shape (token-policy safe): `out&#47;ops&#47;update_officer&#47;&lt;run&gt;&#47;notifier_payload.json`

## Guardrails
- Read-only: no dependency bumps, no lockfile writes, no paper/shadow/evidence mutation.
- No background jobs, no autonomous source discovery, no external transport.

## Implementation references
- `_render_update_officer_source_ergonomics_block()` in `src/webui/ops_cockpit.py`
- `render_ops_cockpit_html(..., update_officer_form_notifier_path=..., update_officer_form_run_dir=...)`
- `GET &#47;ops` in `src/webui/app.py` (form pre-fill on conflict uses trimmed query strings)

## Verification
```bash
python3 -m pytest -q tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff check src/webui/app.py src/webui/ops_cockpit.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff format --check src/webui/app.py src/webui/ops_cockpit.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 scripts/ops/validate_docs_token_policy.py --changed --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

## Version
- v8 builds on v7 app-route wiring with **operator-visible** GET-only source selection only.
