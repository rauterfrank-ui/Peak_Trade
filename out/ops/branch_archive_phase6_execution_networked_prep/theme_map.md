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

- `src/execution/networked/` — entry_contract, http_client_stub, providers, allowlist
- `docs/analysis/p122/`, `p123/`, `p124/`, `p126/`, `p127/`, `p130/` — README/analysis
- `docs/ops/runbooks/execution_wiring_runbook_v1.md`
- `tests/p122/`, `p123/`, `p124/`, `p126/`, `p127/`, `p128/`, `p129/`, `p130/`, `p132/`
