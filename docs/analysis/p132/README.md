# P132 — Networked transport_allow handshake v1 (still networkless)

Scope: shadow/paper only, dry_run enforced. No real HTTP. No secrets.

Goal:
- Wire `transport_allow` into onramp flow/CLI.
- Enforce: allowlist must pass before transport gate can allow.
- Even when allowed, HTTP client remains stubbed: default deny unless explicit simulation flag.

Outputs:
- Updated CLI/runner.
- Tests covering allow/deny combinations and "still networkless" behavior.
