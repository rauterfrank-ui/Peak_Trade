# Update Officer v11 – Consolidation + operator trace

## Goal
Provide a **small, deterministic operator trace** shared across read-only Update Officer surfaces
(WebUI, consumer helpers, CLI wording) so **source_mode**, **origin**, and **resolution target** stay
aligned — without new autonomy, POST, scans, or paper&#47;shadow&#47;evidence mutation.

## What changed vs v10
- **`src/ops/update_officer_consumer.py`**: `build_update_officer_source_trace(...)` returns string
  fields derived only from explicit route resolution and preset:
  - `source_mode` — `conflict` &#124; `explicit_notifier_path` &#124; `run_directory` &#124; `none`
  - `source_origin` — `query_conflict` &#124; `query_notifier_path` &#124; `query_run_directory` &#124; `none`
  - `active_preset` — `manual` &#124; `notifier_path` &#124; `run_dir` (normalized)
  - `source_conflict` — `true` &#124; `false`
  - `effective_resolution_target` — resolved `notifier_payload.json` path, or a fixed token:
    - `BLOCKED_ROUTE_CONFLICT`
    - `NONE_NO_EXPLICIT_SOURCE`
    - `NONE_PAYLOAD_MISSING_AT_EXPLICIT_SOURCE`
  - `safe_default_active` — `true` only when **no** conflict and **no** explicit source after trim
- **`GET &#47;ops`**: read-only **Operator trace** block (`uo-operator-trace`) after validation aids.
- **`scripts/ops/update_officer_summary.py`**: argparse description notes explicit inputs and WebUI
  alignment (behavior unchanged).

## Resolution semantics
Trace uses the same rules as v7: `resolve_update_officer_notifier_payload_path` on the effective
notifier path or run directory after trim; **both** query parameters non-empty → conflict branch,
no payload read.

## Guardrails
- Read-only only; no dependency bumps; no lockfile writes; no latest-run scanning; no POST on
  `&#47;ops`.

## Implementation references
- `build_update_officer_source_trace()` — `src/ops/update_officer_consumer.py`
- `_render_update_officer_operator_trace_html()` — `src/webui/ops_cockpit.py`

## Verification
```bash
python3 -m pytest -q tests/ops/test_update_officer_consumer.py tests/ops/test_update_officer_summary.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff check src/ops/update_officer_consumer.py scripts/ops/update_officer_summary.py src/webui/ops_cockpit.py tests/ops/test_update_officer_consumer.py tests/ops/test_update_officer_summary.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff format --check src/ops/update_officer_consumer.py scripts/ops/update_officer_summary.py src/webui/ops_cockpit.py tests/ops/test_update_officer_consumer.py tests/ops/test_update_officer_summary.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 scripts/ops/validate_docs_token_policy.py --changed --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

## Version
- v11 adds **shared trace tokens** and WebUI visibility; v7–v10 behavior preserved.
