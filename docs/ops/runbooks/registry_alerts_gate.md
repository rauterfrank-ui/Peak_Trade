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

Note (WebUI scope)
- `alerts_latest.txt` is **not** shown in the WebUI. It is a CLI&#47;operator-only surface.
- For WebUI-visible alerts, use:
  - `/api/live/alerts` and `/live/alerts` (Live Alert Storage, Phase 83)
  - `/api/telemetry/alerts/latest` (Execution&#47;Telemetry alerts, Phase 16I)
