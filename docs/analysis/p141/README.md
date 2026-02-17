# P141 — Exec-Net Paper Runner (Onramp) v1 (networkless)

## Scope
Add an operator-only **paper runner** that calls `src.execution.networked.onramp_cli_v1` in `MODE=paper` with `DRY_RUN=YES`.
This produces reproducible evidence (JSON + manifest + SHA256SUMS + bundle + DONE pin), but still stays **networkless**:
- `transport_allow=NO` (default deny)
- no secrets required
- no live execution

## Entry
- Script: `scripts/ops/p141_exec_net_paper_runner_onramp_v1.sh`
- Intended usage: local operator run or LaunchAgent (optional later)

## Preconditions
- Repo clean on `main`
- Python env ready
- `src.execution.networked.onramp_cli_v1` available

## Outputs
Evidence lives under `out&#47;ops&#47;` (illustrative paths use &#47;):
- Evidence dir: `out&#47;ops&#47;p141_exec_net_paper_runner_onramp_<TS>&#47;`
- Bundle: `out&#47;ops&#47;p141_exec_net_paper_runner_onramp_<TS>.bundle.tgz`
- DONE pin: `out&#47;ops&#47;P141_EXEC_NET_PAPER_RUNNER_ONRAMP_DONE_<TS>.txt`

Evidence contents:
- `manifest.json`
- `onramp_markets.json`
- `onramp_orderbook.json`
- `pytest.log`
- `SHA256SUMS.txt`

## Verifications
- `shasum -a 256 -c SHA256SUMS.txt`
- `shasum -a 256 -c <PIN>.sha256`
- JSON asserts:
  - `mode="paper"`
  - `dry_run="YES"`
  - `transport_allow="NO"`
