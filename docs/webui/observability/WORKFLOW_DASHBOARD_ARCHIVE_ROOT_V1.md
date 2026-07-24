# Workflow Dashboard Archive Root v1

## Purpose

Sole configuration owner for the **durable archive root location** used by
Workflow Dashboard V1 and Market Landscape V2 consumers that read
`universe_selection_readmodel.v1` under `{ARCHIVE_ROOT}/readmodels/`.

This contract owns **where** the archive root is resolved. It does **not**:

- authorize live trading, orders, runtime activation, or scheduler work;
- create directories during import or resolution;
- write or copy readmodels;
- autoload Universe onto `GET /market`;
- change visible dashboard panels by itself.

## Ownership

| Field | Value |
|-------|-------|
| Contract id | `workflow_dashboard_archive_root_v1` |
| Config | `config/webui/workflow_dashboard_archive_root_v1.json` |
| Owner module | `src.webui.workflow_dashboard_archive_root_v1` |
| Owner symbol | `resolve_workflow_dashboard_archive_root` |
| Env override | `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT` |

Non-owners (must not become a second dashboard archive convention):

- `PEAK_TRADE_DATA_ARCHIVE_ROOT` (research data archive)
- `scripts/webui/review_server.sh` `.run/webui_review_server` process state
- `tests/fixtures/**`

## Precedence

1. Explicit function/CLI/config injection (`explicit=` / binder `archive_root=`)
2. Environment override `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT`
3. Canonical platform-aware local default

## Canonical default

Deterministic, absolute, cwd-independent user-state location:

| Platform | Default |
|----------|---------|
| macOS | `~/Library/Application Support/Peak_Trade/workflow_dashboard_v1` |
| Linux | `${XDG_STATE_HOME:-~/.local/state}/peak_trade/workflow_dashboard_v1` |
| Windows | `%LOCALAPPDATA%/Peak_Trade/workflow_dashboard_v1` |

Default selection rejects:

- repository working tree / tracked truth
- `tests/fixtures`
- `/tmp` (and tmp-backed `XDG_STATE_HOME`)
- bare filesystem root / bare home directory

## Resolution semantics

- Returned paths are absolute after normalization.
- Resolver **never** creates filesystem entries.
- Consumer call sites use `require_existing_directory=True` so a not-yet-created
  default remains `None` → existing `unconfigured` / `MISSING_SOURCE` /
  `UNIVERSE_ARCHIVE_ROOT_UNSET` behavior is preserved until an explicit writer
  creates the directory and persists readmodels.
- An empty directory is **not** valid dashboard data.
- Missing / invalid / unverified readmodels under a resolved root remain
  fail-closed at the reader/binder (`MISSING_SOURCE` / `INVALID`).

## Non-authority

`non_authorizing: true`. Evidence and path ownership ≠ approval, live unlock,
or Market Dashboard product completion.
