# P113 — Execution Router CLI v1 (mocks only)

## Goal
Provide a minimal CLI to run the new execution stack end-to-end in **shadow/paper** using the registry + router (mocks only).

## Safety
- Modes: `shadow` | `paper` only.
- Default: `--dry-run YES`
- No networking, no keys.

## Usage
```bash
python3 -m src.execution.router.cli_v1 --mode shadow
python3 -m src.execution.router.cli_v1 --mode paper --adapter mock --market BTC-USD --intent place_order --qty 0.1 --side buy --order-type market --dry-run YES
```
