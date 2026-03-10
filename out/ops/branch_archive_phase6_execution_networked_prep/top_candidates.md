# Top Candidates — Salvage-Now

**Erstellt:** 2026-03-10

---

## STRONGLY_UNIQUE (7 Branches)

| Branch | Lines | Rationale |
|--------|-------|-----------|
| recover/p124-execution-networked-entry-contract-v1 | 220 | entry_contract_v1.py; guards; core execution gating |
| recover/p132-networked-transport-allow-handshake-v1 | 185 | transport_allow handshake; tests p128/p129/p132 |
| recover/p126-execution-networked-transport-stub-v1 | 173 | http_client_stub_v1.py; transport layer |
| recover/p127-networked-provider-adapter-stub-v1 | 129 | base_stub_v1.py; provider adapter |
| recover/p122-execution-runbook-v1 | 89 | execution wiring runbook |
| recover/p130-networked-allowlist-stub-v1 | 88 | allowlist_v1.py; default-deny |
| recover/p123-execution-networked-onramp-v1 | 63 | workbook A2Z; shadow/paper |

---

## LIKELY_ALREADY_ON_MAIN (1 Branch)

| Branch | Rationale |
|--------|-----------|
| recover/p128-execution-networked-transport-stub-v1 | git log main..branch empty; diff empty → defer/archive |

---

## Recommended Order (Salvage)

1. p124 (entry contract) — core gating
2. p126 (http client stub) — transport
3. p127 (provider adapter) — adapter layer
4. p130 (allowlist) — gating
5. p132 (handshake) — wiring
6. p122 (runbook) — docs
7. p123 (workbook) — docs
