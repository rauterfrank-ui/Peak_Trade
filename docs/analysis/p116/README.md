# P116 — Execution Session Evidence v1 (mocks-only)

Goal: produce a local evidence+pin bundle for the execution session runner (P115) in shadow/paper only.

Guards: mode in {shadow,paper}; DRY_RUN=YES only; deny LIVE/ARMED/keys.

Artifacts: out/ops/p116_execution_session_<TS>/ (report.json + logs + SHA256SUMS), pin out/ops/P116_EXECUTION_SESSION_DONE_<TS>.txt
