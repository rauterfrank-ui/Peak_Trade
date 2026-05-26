# Generic Evidence Run Registry v1 — test fixtures

Synthetic archive roots for offline registry builder tests.

Layout per archive:

- `runs&#47;paper&#47;{run_id}&#47;` — manifest required; review optional
- `runs&#47;shadow&#47;{run_id}&#47;` — manifest + review PASS required
- `runs&#47;testnet&#47;{run_id}&#47;` — manifest + review PASS required
- `runs&#47;daemon_paper_24h&#47;{run_id}&#47;` — composition-index directory (not a lane)
- `planning&#47;` — optional governance machine lines

## Projection consumer smoke fixtures v0

**Module:** `projection_consumer_v0.py` (test-only; **non-authorizing**)

Shared helpers and canonical field constants for Registry v1 projection consumers:

- Post-Closeout Projection Automation Charter (taxonomy §6a.0.8)
- Notion post-closeout sync projection (taxonomy §6a.1)
- Market Dashboard read-only run projection (taxonomy §6a.2)
- Future S3 finalized-evidence export gate contract tests (metadata only; no S3 implementation)

### Canonical field contract

- `ALLOWED_PROJECTION_FIELDS` — pointer/status fields for `runs[]` and `compositions[]`
- `RUN_PROJECTION_FIELDS` — minimum `runs[]` row fields for consumer smoke tests
- `S3_RELEVANT_PROJECTION_FIELDS` — `evidence_transport`, `manifest_verified`, `archive_path`, `evidence_status` for future export gate tests
- `TOP_LEVEL_PROJECTION_SUMMARY_FIELDS` — `verdict`, `issues`, `blockers`, `archive_root`

### Authority posture (fixtures only)

```
REGISTRY_V1_PROJECTION_CONSUMER_SMOKE_FIXTURES_V0=true
NOTION_AUTHORITY=false
MARKET_DASHBOARD_AUTHORITY=false
S3_AUTHORITY=false
RUNTIME_AUTHORITY=false
SCHEDULER_CLEARANCE_AUTHORITY=false
LIVE_AUTHORITY=false
TESTNET_AUTHORITY=false
BROKER_AUTHORITY=false
DOUBLE_PLAY_AUTHORITY=false
```

Fixtures build offline archives and validate Registry v1 JSON only. They do **not** grant runtime, scheduler, testnet, live, broker, Notion, Dashboard, or S3 export authority.

### Usage

Import from tests:

```python
from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as registry_fixtures
```

Helpers: `write_lane`, `write_composition`, `write_minimal_paper_run`, `build_registry`, `assert_non_authorizing_run_projection_defaults`.

Fixtures are created programmatically in tests; this directory documents conventions and hosts shared test-only helpers.
