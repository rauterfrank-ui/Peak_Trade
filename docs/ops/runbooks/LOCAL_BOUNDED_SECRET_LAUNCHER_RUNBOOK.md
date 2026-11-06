# LOCAL BOUNDED SECRET LAUNCHER RUNBOOK

## Status: DECOMMISSIONED

`scripts&#47;ops&#47;run_bounded_pilot_with_local_secrets.py` is **removed**. <!-- pt:ref-target-ignore -->
It must not inject, require, or accept `KRAKEN_API_KEY` / `KRAKEN_API_SECRET`.

This runbook no longer describes a current Kraken secret-injection success path.
It does **not** create an OKX secret launcher and does **not** authorize live/canary/orders.

## Current bounded-pilot session path (no Kraken secret injection)

```bash
cd ~/Peak_Trade
python3 scripts/ops/run_bounded_pilot_session.py --steps 25 --position-fraction 0.0005
```

Do not export Kraken credentials as a current bounded-pilot setup step.

## Historical context

The former local `.bounded_pilot.env` launcher existed only to inject Kraken credentials.
That purpose is retired. Remaining `.bounded_pilot.env` files are operator-local leftovers, not a current credential contract.

## Authority and scope

This file is review / operator navigation only. It confers **no** order, exchange, arming, routing, or enablement authority.

Optional pointers:
- [`../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md)
- [`../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md`](../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md)
