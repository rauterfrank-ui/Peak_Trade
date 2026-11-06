# Update Officer v6 – Ops-Cockpit/WebUI integration

## Goal
Expose a **read-only** Update Officer notifier summary on the Ops Cockpit (same truth-first,
no-write posture as the rest of `src/webui/ops_cockpit.py`).

## Data source
- `build_update_officer_ui_model()` in `src/ops/update_officer_consumer.py` loads and validates
  `notifier_payload.json` via `load_notifier_payload()` and `build_notifier_view_model()`.
- `build_ops_cockpit_payload()` accepts optional:
  - `update_officer_notifier_path` — explicit file path
  - `update_officer_run_dir` — directory containing `notifier_payload.json`

When both are omitted (default HTTP `/ops` route), the UI shows a **deterministic empty state**
(no directory scanning).

## Payload shape (`update_officer_ui`)
| Field | Meaning |
|-------|---------|
| `available` | Whether a valid payload was loaded |
| `headline` | Operator headline (empty if unavailable) |
| `status` | Consumer status or `unavailable` |
| `next_topic` | Next recommended topic id |
| `why_now` | `top_priority_reason` |
| `next_action` | `recommended_next_action` |
| `review_paths` | List of paths |
| `queue_preview` | Ranked queue entries |
| `requires_manual_review` | Boolean |
| `severity` | Notifier severity |
| `reminder_class` | Reminder class |
| `empty_state_message` | Fixed text when unavailable or invalid |

## Empty-state behavior
- No path / missing file: deterministic *not available* message.
- Invalid JSON or schema violation: deterministic *could not be loaded or validated* message.

## Guardrails
- Read-only only; **no** buttons, forms, or write actions in this section.
- No dependency bumps, no lockfile writes, no paper/shadow/evidence mutation.
- No background jobs or notification transport.

## Operator wiring (optional)
The default app does not pass paths. To surface a specific run from Python/tests, pass
`update_officer_notifier_path` or `update_officer_run_dir` into `build_ops_cockpit_payload()`.

Illustrative run layout (fenced block only):

```text
out/ops/update_officer/<timestamp>/notifier_payload.json
```

## Verification
```bash
python3 -m pytest -q tests/ops/test_update_officer_consumer.py tests/webui/test_ops_cockpit.py
python3 -m ruff check src/ops/update_officer_consumer.py src/webui/ops_cockpit.py tests/ops/test_update_officer_consumer.py tests/webui/test_ops_cockpit.py
python3 -m ruff format --check src/ops/update_officer_consumer.py src/webui/ops_cockpit.py tests/ops/test_update_officer_consumer.py tests/webui/test_ops_cockpit.py
python3 scripts/ops/validate_docs_token_policy.py --changed --base origin/main
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

## Version
- v6 builds on v4 consumer layer and v5 CLI contract (`v3-min` notifier schema).
