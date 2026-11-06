# Workflow Dashboard Archive Root v1

## Purpose

Sole configuration owner for the **durable archive root location** used by
Workflow Dashboard V1 and Market Landscape V2 consumers that read
`universe_selection_readmodel.v1` under `{ARCHIVE_ROOT}&#47;readmodels&#47;`.

This contract owns **where** the archive root is resolved. It does **not**:

- authorize live trading, orders, runtime activation, or scheduler work;
- create directories during import or resolution;
- write or copy readmodels;
- invent Universe &#47; Selected Future &#47; OHLCV when the readmodel is absent.

**Market Landscape consumer (authorized after archive-root contract):**
`GET &#47;market` resolves this archive root (explicit → Env override → canonical
default) and read-only-loads `universe_selection_readmodel.v1` via
`bind_market_universe_slots`. No Env var is required when the canonical default
directory exists with a manifest-verified readmodel. Missing &#47; invalid
readmodels remain fail-closed `MISSING_SOURCE` &#47; `INVALID`. OHLCV, Decision,
Risk, Execution, and Timeline stay unbound in the Universe default-path slice.

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
- `scripts/webui/review_server.sh` `.run&#47;webui_review_server` process state
- `tests&#47;fixtures&#47;**`

## Precedence

1. Explicit function/CLI/config injection (`explicit=` / binder `archive_root=`)
2. Environment override `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT`
3. Canonical platform-aware local default

## Canonical default

Deterministic, absolute, cwd-independent user-state location:

| Platform | Default |
|----------|---------|
| macOS | `~&#47;Library&#47;Application Support&#47;Peak_Trade&#47;workflow_dashboard_v1` |
| Linux | `${XDG_STATE_HOME:-~&#47;.local&#47;state}&#47;peak_trade&#47;workflow_dashboard_v1` |
| Windows | `%LOCALAPPDATA%&#47;Peak_Trade&#47;workflow_dashboard_v1` |

Default selection rejects:

- repository working tree / tracked truth
- `tests&#47;fixtures`
- `&#47;tmp` (and tmp-backed `XDG_STATE_HOME`)
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
