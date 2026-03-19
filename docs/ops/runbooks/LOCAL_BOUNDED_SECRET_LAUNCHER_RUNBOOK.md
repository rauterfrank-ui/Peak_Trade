# LOCAL BOUNDED SECRET LAUNCHER RUNBOOK

## Purpose
Operator workflow for bounded/acceptance sessions without repeated manual secret copy-paste.

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
