# P114 — Execution Router Wiring v1 (mocks only)

Goal: Wire router -> registry selector -> provider adapters with strict guards.
Scope: shadow/paper only, DRY_RUN default YES. No network. No keys.

Notes:
- CLI lives in `src&#47;execution&#47;router&#47;cli_v1.py`
- Router lives in `src&#47;execution&#47;router&#47;router_v1.py`
- Registry lives in `src&#47;execution&#47;adapters&#47;registry_v1.py`
