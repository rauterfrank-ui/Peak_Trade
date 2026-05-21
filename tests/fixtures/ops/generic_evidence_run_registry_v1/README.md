# Generic Evidence Run Registry v1 — test fixtures

Synthetic archive roots for offline registry builder tests.

Layout per archive:

- `runs/paper/{run_id}/` — manifest required; review optional
- `runs/shadow/{run_id}/` — manifest + review PASS required
- `runs/testnet/{run_id}/` — manifest + review PASS required
- `planning/` — optional governance machine lines

Fixtures are created programmatically in tests; this directory documents conventions only.
