---
docs_token: DOCS_TOKEN_INDEPENDENT_DEV_PANEL_QUARANTINE_RELEASE_V1
STATUS: CONTRACT_DEFINITION
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Independent DEVELOPMENT panel quarantine release v1

Canonical path:

`QUARANTINE_BYTE_IDENTICAL_RESTORE` → `RELEASED_DEVELOPMENT_ONLY`

- Source: `&#47;quarantine&#47;dev_pre_holdout_panel_v1_20260720T2052Z`
- Target: `&#47;dev_pre_holdout_panel_v1_20260720T2052Z`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Role: `DEVELOPMENT_ONLY`
- Byte-identical only; no transform; no holdout; no evaluation authorization.

Module: `src&#47;research&#47;independent_dev_panel_quarantine_release_v1.py`  
CLI: `scripts&#47;research&#47;run_release_independent_dev_panel_quarantine_v1.py`
