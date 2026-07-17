# PR-B Contract Location Analysis

## Candidate locations

| Candidate | Kind | Notes |
|---|---|---|
| `src/webui/market_dashboard_readmodels_v1/` | New package (preferred) | Runbook Phase 3 / PR-B explicit proposal |
| `src/webui/workflow_dashboard_readmodel_v1/` | Existing aggregate | Observability/workflow owner; wrong product surface |
| `src&#47;webui&#47;market_*_readmodel_v0&#47;` | Existing producers | Domain-specific builders (OHLCV/depth/tape/ranking), not page aggregate contracts |
| `src/webui/market_visual_operator_surface_v1/contracts.py` | Existing display helpers | Presentation/activity vocabulary; not immutable provenance-bearing snapshots |
| `src&#47;observability&#47;**` | Secondary allowlist | Not required; would dilute WebUI consumer ownership |

## Existing dashboard/readmodel conventions

- WebUI packages use `@dataclass(frozen=True)`, stdlib-only, explicit `to_json_dict()`.
- Versioning commonly uses `SCHEMA_VERSION` / `readmodel_id` strings.
- Validation is fail-closed via `*Error(ValueError)` helpers.
- Tests live under `tests&#47;webui&#47;test_<package>.py`.
- Runbook §3.3 additionally requires `schema_id` + provenance fields for dashboard contracts.

## Import-direction assessment

Required direction:

```text
Domain producers (unchanged) → ReadModel contracts (this PR) → Presenter/UI (later PRs)
```

Constraints for this package:

- Must not import templates, Jinja, Flask/FastAPI route modules, or CSS/JS concerns.
- Must not call Trading Core / Double Play / execution / order / strategy owners.
- Must remain a pure typed consumer contract layer.

## Chosen location

`src/webui/market_dashboard_readmodels_v1/`

Expected structure:

```text
src/webui/market_dashboard_readmodels_v1/
  __init__.py
  contracts.py
  provenance.py
  validation.py
  serialization.py
  aggregate.py
```

Package documentation (not under `src/` to avoid `central_src` selector classification for `.md`):

```text
docs/webui/MARKET_DASHBOARD_READMODELS_V1.md
```

## Rejected alternatives

- **Reuse `workflow_dashboard_readmodel_v1`:** different product owner (observability pipeline), would mix scopes and import surfaces.
- **Extend `market_*_readmodel_v0`:** those packages are producer/builders for single domains; PR-B needs page-level consumer contracts with unavailable semantics.
- **Extend `market_visual_operator_surface_v1&#47;contracts.py`:** display/runtime helpers, not versioned immutable snapshot contracts.
- **Place under `src/observability/`:** unnecessary indirection; dashboard consumer ownership belongs under `src/webui/`.

## Ownership rationale

- Package owns typed Market Dashboard **consumer** contracts only.
- No producer binding (PR-C).
- No `/market` UI binding (PR-D).
- Domain decision/authority/risk/execution owners remain untouched.
- Aligns with Master Runbook Phase 3 and PR-B sequence after PR-A reset shell.

## Field-name convention note

Repo WebUI historically prefers `readmodel_id` / `schema_version`. PR-B follows Runbook §3.3 and uses `schema_id` + `schema_version` on every snapshot/provenance contract. Package identity also exposes `PACKAGE_ID = "market_dashboard_readmodels.v1"`.
