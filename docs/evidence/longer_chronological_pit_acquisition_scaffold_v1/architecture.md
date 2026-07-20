# Architecture

Package: `src&#47;research&#47;longer_chronological_pit_acquisition_v1&#47;__init__.py`

| Module | Role |
|---|---|
| `archive_root.py` | `PEAK_TRADE_DATA_ARCHIVE_ROOT` resolve &#47; validate &#47; layout |
| `source_discovery.py` | Deterministic public OKX locators; UNCERTAIN coverage tags |
| `partition_planner.py` | Monthly partitions clipped to listing&#47;delisting; BTC&#47;spot fail-closed |
| `manifest.py` | Manifest rows + digest + atomic create-only write |
| `resume_state.py` | State machine + skip-verified + immutable partition writes |
| `adapter.py` | OKX adapter scaffold; network gated |
| `qualification.py` | Dry-run report |
| `cli.py` &#47; `__main__.py` | `plan` &#47; `discover` &#47; `manifest` &#47; `probe` &#47; `qualify-dry-run` |

Config: `config&#47;research&#47;longer_chronological_pit_acquisition_chrono_3y_v1.json`
