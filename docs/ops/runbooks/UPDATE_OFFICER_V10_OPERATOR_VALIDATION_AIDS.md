# Update Officer v10 – Operator validation aids (read-only)

## Goal
Add a **deterministic, read-only** validation and explainability block on **`GET &#47;ops`** so
operators see how the **current query state** will be interpreted for Update Officer sources and
presets — without changing v7 resolution, without POST, and without hidden discovery.

## What changed vs v9
- Inside the **Update Officer source selection** card, a **Validation / explainability (read-only)**
  subsection (`uo-validation-aids`) renders **before** the Active source line.
- Content is **derived only** from normalized route inputs and `update_officer_source_preset`:
  - **Source mode** — `conflict`, explicit notifier path, run directory, or none (omitted)
  - **Preset meaning** — short explanation for manual / notifier path / run directory preset
  - **Resolution interpretation** — how the consumer will treat the resolved source (or why not)
  - **Conflict** — extra line only when both trimmed parameters are non-empty
  - **Safe default** — extra line only in the omitted-source empty state
- **`GET &#47;api&#47;ops-cockpit`** is unchanged (JSON only; no validation aids block).

## Query parameters
Same as v7/v9:

| Parameter | Meaning |
|-----------|---------|
| `update_officer_notifier_path` | Path to `notifier_payload.json` |
| `update_officer_run_dir` | Directory containing `notifier_payload.json` |
| `update_officer_source_preset` | Optional label: `manual`, `notifier_path`, `run_dir` |

Explanations **do not** add new resolution rules; they describe the existing v7 behavior.

## GET-only stance
- The aids block is static HTML alongside existing GET forms and links.
- **No** `method="post"`.

## Guardrails
- Read-only: no dependency bumps, no lockfile writes, no paper&#47;shadow&#47;evidence mutation.
- No background jobs, no latest-run scanning, no external transport, no persistence beyond the URL.

## Implementation references
- `build_update_officer_validation_aids()`, `_render_update_officer_validation_aids_html()` in
  `src/webui/ops_cockpit.py` (used from `_render_update_officer_source_ergonomics_block()`)
- `GET &#47;ops` in `src/webui/app.py` (unchanged wiring vs v9)

## Verification
```bash
python3 -m pytest -q tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff check src/webui/app.py src/webui/ops_cockpit.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff format --check src/webui/app.py src/webui/ops_cockpit.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 scripts/ops/validate_docs_token_policy.py --changed --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

## Version
- v10 builds on v9 presets with **operator-facing validation/explainability** text only.
