# Live Pilot Session Wrapper (Hard-Gated)

File
- `scripts&#47;ops&#47;run_live_pilot_session.sh`

Hard gates (must all be set)
- `PT_LIVE_ENABLED=YES`
- `PT_LIVE_ARMED=YES`
- `PT_LIVE_ALLOW_FLAGS` contains `pilot_only`
- `PT_LIVE_DRY_RUN=YES` (first pilot runs)
- `PT_CONFIRM_TOKEN_EXPECTED=<one-time token>`
- `PT_CONFIRM_TOKEN=<same token>`

Example (will FAIL unless all gates satisfied)
- `PROFILE=btc_momentum DURATION_MIN=10 CONFIG_PATH=config.toml PT_LIVE_ENABLED=YES PT_LIVE_ARMED=YES PT_LIVE_ALLOW_FLAGS=pilot_only PT_LIVE_DRY_RUN=YES PT_CONFIRM_TOKEN_EXPECTED=ABC PT_CONFIRM_TOKEN=ABC scripts&#47;ops&#47;run_live_pilot_session.sh`

Notes
- This wrapper only **gates** and then calls the existing orchestrator entrypoint.
- Default outcome is **NO_TRADE** unless the operator explicitly arms and confirms.
