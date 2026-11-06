# Launchd log rotation (local)

Purpose
- Prevent `out&#47;ops&#47;launchd&#47;*.log` from growing unbounded.

Script
- `scripts&#47;ops&#47;rotate_launchd_logs.sh`

Defaults
- `MAX_BYTES=10485760` (10MB)
- `KEEP=5` rotated files per log

Run
- `scripts&#47;ops&#47;rotate_launchd_logs.sh`

Integration
- `operator_all.sh` runs rotation best-effort at start.
