# P140 — Exec-Net Paper Evidence Pack v1 (networkless, DRY_RUN only)

## Scope
Generate a deterministic evidence pack for the networked onramp CLI in **paper mode**, while staying **networkless**:
- `MODE=paper`
- `DRY_RUN=YES` (required)
- `transport_allow=NO` (default deny)
- no secrets, no live execution

## Entry
- Script: `scripts/ops/p140_exec_net_paper_evidence_pack_v1.sh`

## Outputs
Evidence dir under `out&#47;ops&#47;`:
- `out&#47;ops&#47;p140_paper_evidence_pack_<TS>&#47;`
- `manifest.json`
- `onramp_markets.json`
- `onramp_orderbook.json`
- `pytest.log`
- `SHA256SUMS.txt` (style-guarded, repo-root-relative paths)
- bundle: `...bundle.tgz` + `...bundle.tgz.sha256`
- DONE pin: `out&#47;ops&#47;P140_EXEC_NET_PAPER_EVI_DONE_<TS>.txt` + `.sha256`

## Verifications
- `shasum -a 256 -c <PIN>.sha256`
- `shasum -a 256 -c <BUNDLE>.sha256`
- JSON asserts:
  - `mode=paper`
  - `dry_run=YES`
  - `transport_allow=NO`

## Guardrails
- No network, no secrets.
- If any guard fails, script must exit non-zero.
