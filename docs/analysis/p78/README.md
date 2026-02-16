# P78 — Online Readiness Supervisor v1

Goal: single daemon-style wrapper that periodically runs **P76 go/no-go** (which itself runs P71 → P72),
writes per-tick evidence under OUT_DIR, and manages a pidfile.

Safety:
- MODE allowed: paper|shadow only (hard-block live/record).
- No model calls; relies on existing gates.
