# LOCAL BOUNDED SECRET ENV FILE CONTRACT

## Purpose
Define the local non-git env file used only by the bounded/acceptance launcher.

## Recommended File Names
- `.bounded_pilot.env`
- `.bounded_launch.env`

## Required Properties
- local only
- gitignored
- loaded only by the explicit bounded launcher
- never auto-sourced by shell startup
- never used by paper/shadow/testnet launchers

## Required Variables
- KRAKEN_API_KEY
- KRAKEN_API_SECRET

## Optional Variables
- `PT_EXEC_EVENTS_ENABLED`

## File Format
- one `KEY=value` pair per line
- blank lines allowed
- comment lines starting with `#` allowed

## Fail-Closed Rules
- if file missing: launcher aborts
- if required vars missing: launcher aborts
- if mode is not bounded/acceptance: launcher aborts
