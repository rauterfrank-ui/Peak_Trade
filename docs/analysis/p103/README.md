# P103 — P91 launchd dynamic OUT_DIR v1

## Goal
Avoid pinned `OUT_DIR` in launchd for P91. The job resolves the newest `run_*` under `SUP_BASE_DIR` at runtime.

## Install
```bash
bash scripts&#47;ops&#47;install_launchd_p91_audit_snapshot_runner_v1.sh
```
