# Registry Alerts Gate — Runbook

Purpose
- Turns Trend-Report alerts into a strict local gate.
- Exit code:
  - `0` = no alerts
  - `2` = alerts present

Input
- `out&#47;ops&#47;registry&#47;morning_one_shot_done_registry.jsonl`

Command
- `python3 scripts&#47;ops&#47;registry_alerts_gate.py`

Output (untracked)
- `out&#47;ops&#47;registry&#47;reports&#47;alerts_latest.txt`
