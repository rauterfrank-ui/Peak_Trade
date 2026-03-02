# PR-BL — PR-BJ Exec-Events Bundler (Runbook)

Problem
- PR-BG consumes only the latest PR-BJ artifact.
- If a single PR-BJ run emits too few events (often only session_start/session_end), PRBI stays blocked with `INSUFFICIENT_SAMPLE_SIZE`.

Solution
- Bundle the last N successful PR-BJ artifacts (`execution_events.jsonl`) into a single JSONL.
- Write the bundle to:
  - ``out&#47;ops&#47;prbj_bundle_latest&#47;execution_events_bundled.jsonl`` (untracked)
  - optionally ``docs&#47;ops&#47;samples&#47;execution_events_latest.jsonl`` (tracked) so PR-BG can prefer it in its fallback chain.

Safety
- No trading actions are performed.
- This is pure artifact aggregation.

Local usage
- Requires `gh` auth.
- Run:
  - ``python3 scripts&#47;ops&#47;bundle_prbj_exec_events.py --runs 20 --take 10 --write-repo-latest``

Expected
- ``docs&#47;ops&#47;samples&#47;execution_events_latest.jsonl`` grows to >=100 lines once enough PR-BJ successful runs exist.
- PRBG sample_size increases accordingly; PRBI warning `INSUFFICIENT_SAMPLE_SIZE` can clear without changing strategies.
