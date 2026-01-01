---
description: Peak_Trade governance & safety rules (always apply)
globs:
  - "**/*"
alwaysApply: true
---

# Peak_Trade Governance (Cursor Rules)

- Never enable live trading by default. No flags like enable_live_trading=true, no hidden defaults, no automatic switching.
- Treat execution/routing/risk as safety-critical: explicit configuration, gated behavior, and tests required.
- Prefer docs-only changes unless explicitly requested.
- Always propose verification commands (tests + relevant CI gates) before claiming completion.
- Respect repository conventions (paths, naming, invariants, locked paths).
