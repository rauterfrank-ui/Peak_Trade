# P117 — Ops Loop: optional execution evidence hook (P116)

Adds an **optional** step to run P116 during ops loop in **shadow/paper only**.

Default: OFF. Enable by setting `P117_ENABLE_EXEC_EVI=YES`.

Hard guards: `MODE in {shadow,paper}`, `DRY_RUN=YES`, deny LIVE/ARMED/keys.
