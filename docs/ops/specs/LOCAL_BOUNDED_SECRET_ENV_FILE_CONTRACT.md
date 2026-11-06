# LOCAL BOUNDED SECRET ENV FILE CONTRACT

## Status: DECOMMISSIONED

The dedicated Kraken local-secret launcher is **removed**.
This contract no longer requires or authorizes:

- KRAKEN_API_KEY
- KRAKEN_API_SECRET

Do **not** retarget these names to OKX credentials.
Do **not** treat this file as a current live/pilot credential grant.

## Purpose (historical)

Define the local non-git env file formerly used only by the bounded/acceptance Kraken secret launcher.

## Recommended File Names (historical leftovers only)

- `.bounded_pilot.env`
- `.bounded_launch.env`

## Required Properties

- local only
- gitignored
- never auto-sourced by shell startup
- never used by paper/shadow/testnet launchers
- **no current required venue credentials**

## Optional Variables

- `PT_EXEC_EVENTS_ENABLED`

## File Format

- one `KEY=value` pair per line
- blank lines allowed
- comment lines starting with `#` allowed

## Fail-Closed Rules

- there is no current Kraken secret-injection success path
- missing Kraken vars must not be treated as a blocker that implies Kraken is the operative venue
- if mode is not bounded/acceptance: abort (historical launcher behavior; launcher absent)

## Current session path

Use `scripts/ops/run_bounded_pilot_session.py` without Kraken secret injection.
This contract does not authorize live, canary, orders, or OKX credential substitution.
