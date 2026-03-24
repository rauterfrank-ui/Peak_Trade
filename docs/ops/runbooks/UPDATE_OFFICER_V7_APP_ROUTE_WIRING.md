# Update Officer v7 – App route wiring (query parameters)

## Goal
Wire **optional, explicit, read-only** Update Officer inputs from the HTTP surface into
`build_ops_cockpit_payload()` / `render_ops_cockpit_html()` without changing the v6 card
semantics: **no** latest-run scanning, **no** write actions, deterministic empty or
conflict states.

## Routes
Both accept the same optional query parameters:

| Route | Response |
|-------|----------|
| `GET &#47;ops` | HTML Ops Cockpit |
| `GET &#47;api&#47;ops-cockpit` | JSON payload (includes `update_officer_ui`) |

### Query parameters
| Parameter | Meaning |
|-----------|---------|
| `update_officer_notifier_path` | Absolute or relative path to `notifier_payload.json` |
| `update_officer_run_dir` | Directory that contains `notifier_payload.json` |

Rules:
- **Omitted** or **whitespace-only** values are treated as not provided (default empty-state
  on the Update Officer card, same as v6 when no paths are passed in code).
- **Both non-empty** → deterministic **conflict** empty-state (read-only message); no
  exception is raised to the route handler.
- Only **one** non-empty source → same resolution as v6 (`resolve_update_officer_notifier_payload_path`).

Illustrative URLs (fenced; use your real host and paths):

```text
/ops?update_officer_notifier_path=/abs/path/to/notifier_payload.json
/ops?update_officer_run_dir=/abs/path/to/run_dir
/api/ops-cockpit?update_officer_run_dir=/abs/path/to/run_dir
```

Inline example segments (token-policy safe): `out&#47;ops&#47;update_officer&#47;&lt;run&gt;&#47;notifier_payload.json`

## Guardrails
- Read-only: **no** buttons, forms, or POST in this area; no dependency or lockfile writes.
- No background jobs or notification transport from these query parameters.
- Paths are **operator-supplied**; the server only reads files that exist and validates
  schema like the consumer layer.

## Implementation references
- `resolve_update_officer_route_inputs()` in `src/webui/ops_cockpit.py`
- `build_update_officer_ui_route_conflict()` in `src/ops/update_officer_consumer.py`
- `GET &#47;ops` and `GET &#47;api&#47;ops-cockpit` in `src/webui/app.py`

## Verification
```bash
python3 -m pytest -q tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff check src/webui/app.py src/webui/ops_cockpit.py src/ops/update_officer_consumer.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 -m ruff format --check src/webui/app.py src/webui/ops_cockpit.py src/ops/update_officer_consumer.py tests/webui/test_ops_cockpit.py tests/test_webui_live_track.py
python3 scripts/ops/validate_docs_token_policy.py --changed --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

## Version
- v7 extends v6 Ops Cockpit integration with optional HTTP query wiring only.
