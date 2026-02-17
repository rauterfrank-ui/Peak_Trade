# P124 — Execution Networked Entry Contract v1

Scope: networkless, mocks-only.
Purpose: freeze the "entry contract" + hard guardrails before adding any transport, auth, or secrets.

Guards:

- mode ∈ {shadow, paper}
- dry_run must be True
- deny env vars (LIVE, TRADING_ENABLE, PT_ARMED, …)
- reject any env var that looks like an API key/secret

Files:

- src&#47;execution&#47;networked&#47;entry_contract_v1.py
- tests&#47;p124&#47;test_p124_entry_contract_guards.py
