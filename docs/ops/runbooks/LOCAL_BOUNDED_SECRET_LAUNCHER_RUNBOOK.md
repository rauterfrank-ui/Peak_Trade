# LOCAL BOUNDED SECRET LAUNCHER RUNBOOK

## Purpose
Operator workflow for bounded/acceptance sessions without repeated manual secret copy-paste.

> **Authority and scope**  
> This file is a **local** **bounded** **secret** **launcher** **operator** **runbook** and **review / operator navigation** for the `.bounded_pilot.env` + bounded secret launcher path. Wording about *secret* **source**, `KRAKEN`, `.bounded_pilot.env`, *launcher*, *bounded*, *trial*, *run*, or *local* **ops** is **not** an automatic **operational authorization** — it does **not** grant real-money go, any **live** / first-live / `PRE_LIVE` release, **signoff**, **evidence**, or a **gate pass** in the current **Master V2** enablement sense. **Secret** and **credential** steps are **local**, **technical**, and *fails closed* by design; they do **not** substitute for a governed signoff. This runbook confers **no** order, exchange, arming, routing, or enablement authority, and it does **not** create a **Master V2** or **Double Play** handoff. **Master V2 / Double Play** and the canonical **PRE_LIVE** / readiness / signoff contracts remain the governing authority.  
> Optional pointers: [`../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) · [`../specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md`](../specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) · [`../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md`](../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md) · [`../AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md`](../AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md)

## Secret Source
Expected local non-git env file:
- `.bounded_pilot.env`

Example template:
- `docs&#47;ops&#47;examples&#47;bounded_pilot.env.example`

## Guardrails
- only the dedicated bounded secret launcher reads the local env file
- paper/shadow/testnet launchers must not read it
- launcher fails closed if file is missing or incomplete
- launcher supports only bounded/acceptance-oriented modes

## Dry Check
```bash
cd ~/Peak_Trade
python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --dry-check
```

## Setup
1. Copy the example template:
   ```bash
   cp docs/ops/examples/bounded_pilot.env.example .bounded_pilot.env
   ```
2. Edit `.bounded_pilot.env` and set `KRAKEN_API_KEY` and `KRAKEN_API_SECRET`.
3. Ensure `.bounded_pilot.env` is gitignored (it is by default).

## Launch Bounded Session
```bash
cd ~/Peak_Trade
python3 scripts/ops/run_bounded_pilot_with_local_secrets.py
```

## Options
- `--dry-check` — validate env file and exit without invoking session
- `--env-file PATH` — use a different env file (default: `.bounded_pilot.env`)
- `--steps N` — max steps for session (default: 25)
- `--position-fraction F` — order size fraction (default: 0.0005)

## Reference
- `docs&#47;ops&#47;specs&#47;LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT.md`
- `docs&#47;ops&#47;architecture&#47;LOCAL_BOUNDED_SECRET_LAUNCH_PATH_PROPOSAL.md`
