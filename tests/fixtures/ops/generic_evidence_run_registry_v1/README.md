# Generic Evidence Run Registry v1 — test fixtures

Synthetic archive roots for offline registry builder tests.

Layout per archive:

- `runs&#47;paper&#47;{run_id}&#47;` — manifest required; review optional
- `runs&#47;shadow&#47;{run_id}&#47;` — manifest + review PASS required
- `runs&#47;testnet&#47;{run_id}&#47;` — manifest + review PASS required
- `planning&#47;` — optional governance machine lines

Fixtures are created programmatically in tests; this directory documents conventions only.
