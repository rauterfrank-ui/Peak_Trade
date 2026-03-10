# Execution-Networked — Theme / Path Mapping

**Erstellt:** 2026-03-10

---

## Subthemes

| Subtheme | Branches | Touched Areas |
|----------|----------|---------------|
| runbook | p122 | docs/ops/runbooks/execution_wiring_runbook_v1.md, docs/analysis/p122 |
| runner/onramp | p123 | docs/analysis/p123, WORKBOOK_EXECUTION_NETWORKED_ONRAMP_A2Z_V1.md |
| execution control/gating | p124, p127, p130 | src/execution/networked/entry_contract_v1.py, providers/base_stub_v1.py, allowlist_v1.py |
| transport | p126, p128 | src/execution/networked/http_client_stub_v1.py (p128: already on main) |
| handshake wiring | p132 | tests/p128, p129, p132; transport_allow handshake |

---

## Path Hints

- `src&#47;execution&#47;networked&#47;` — entry_contract, http_client_stub, providers, allowlist
- `docs&#47;analysis&#47;p122&#47;`, `p123&#47;`, `p124&#47;`, `p126&#47;`, `p127&#47;`, `p130&#47;` — README/analysis
- `docs&#47;ops&#47;runbooks&#47;execution_wiring_runbook_v1.md`
- `tests&#47;p122&#47;`, `p123&#47;`, `p124&#47;`, `p126&#47;`, `p127&#47;`, `p128&#47;`, `p129&#47;`, `p130&#47;`, `p132&#47;`
