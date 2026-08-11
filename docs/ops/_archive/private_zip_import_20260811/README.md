# Private ZIP import archive — 2026-08-11

```text
DOCUMENT_CLASS=HISTORICAL_ARCHIVE_ONLY
DOCUMENT_ROLE=NON_CANONICAL_IMPORT_PROVENANCE
STATUS=HISTORICAL / NON_AUTHORIZING
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
ORDERS_ALLOWED=false
CANONICAL_SSOT_OVERWRITE=false
IMPORT_DATE=2026-08-11
OWNER_GO=OWNER_GO_IMPORT_LOCAL_PRIVATE_ZIPS_TO_PEAK_TRADE
```

**Rule:** Canonical Peak_Trade docs, Master Runbook, Map of Truth, gates, and specs
supersede everything here. This archive does **not** authorize Live, Testnet, Paper
Exchange, credentials, orders, or autonomy activation.

Localized macOS source directory resolved from `~/Documents/Privat/` →
`/Users/frnkhrz/Documents/Dokumente Privat/`.

---

## Source 1 — Peak_Trade AI autonomy audit docs

| Field | Value |
|-------|-------|
| Original filename | `peak_trade_ai_autonomy_audit_docs.zip` |
| Absolute source path | `/Users/frnkhrz/Documents/Dokumente Privat/peak_trade_ai_autonomy_audit_docs.zip` |
| Size (bytes) | `6158` |
| SHA256 | `c41e43eb628bc193c30254f6855da7b8164d04e6c3cc5419a565ab05245645b8` |
| Classification | `PEAK_TRADE_AI_AUTONOMY_AUDIT_DOCS_HISTORICAL` |
| Decision | `HISTORICAL_ARCHIVE_ONLY` — do **not** overwrite active governance |

### Contained members

| Member (zip-internal path; not a live repo claim) | Member SHA256 | In-repo archive path |
|---------------------------------------------------|---------------|----------------------|
| ZIP member GO_NO_GO overview <!-- pt:ref-target-ignore --> | `e4bb4303ec8bc0c3d4bfa13a9523e7bfe0102092bed2f98e395ec14f6a638d62` | [historical_ai_autonomy_audit_docs/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md.archived](historical_ai_autonomy_audit_docs/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md.archived) |
| ZIP member Evidence Pack template <!-- pt:ref-target-ignore --> | `1f81dff5957f2dc56e44c5b28ecc4d6442326f2d82a11d1301a2c860b0b437d1` | [historical_ai_autonomy_audit_docs/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE.md.archived](historical_ai_autonomy_audit_docs/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE.md.archived) |

### Active canonical owners (do not replace with this archive)

| Topic | Active canonical path |
|-------|------------------------|
| AI Autonomy Go/No-Go | `docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md` (repo copy is newer / more complete than ZIP) |
| Evidence Pack Template | `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE.md` |
| Evidence Pack Template v2 | `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md` |
| Layer/Model matrix | `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` |

Operator recovery copy of the original ZIP (outside git):

`/Users/frnkhrz/Documents/Peak_Trade_Archive/private_zip_import_20260811_peak_trade_ai_autonomy_audit/original_zip_copy/peak_trade_ai_autonomy_audit_docs.zip`

---

## Source 2 — eSign / Vertragsunterlagen pack

| Field | Value |
|-------|-------|
| Original filename | `83940723_20251006_05533c0e0a08 2.zip` |
| Absolute source path | `/Users/frnkhrz/Documents/Dokumente Privat/83940723_20251006_05533c0e0a08 2.zip` |
| Size (bytes) | `2332682` |
| SHA256 | `10d8cc1e9a1096fbef2ecfe3a2c1d045d345decf464ee2355cb92298f14ed256` |
| Classification | `NON_PEAK_TRADE_PERSONAL_LEGAL_ESIGN_CONTRACT_PACK` |
| Decision | `EXTERNAL_ARCHIVE_ONLY` — **not** mixed into active Peak_Trade docs; **PDF bytes not committed** |

### Contained members (metadata only in git)

| Member | Size | Member SHA256 | Git committed? |
|--------|------|---------------|----------------|
| `AGB eSign.pdf` | `335900` | `8f5f63492c6b600c5fed3cde81731137ea2609fd2fbbb9b459781079442bd4ac` | `false` |
| `Vertragsunterlagen.pdf` | `1996506` | `b5cf939eeb8bf51215c7e6e3af953749cdcd67a335f290ce510a42e489ce2658` | `false` |

### Why not in Peak_Trade git

- No Peak_Trade / AI / Autonomy / Runbook relevance.
- Personal/legal eSign contract material (`AGB`, `Vertragsunterlagen`, SEPA keyword signal).
- Fail-closed: do not commit personal/legal PDFs into the repository tree.

External (non-git) archive path:

`/Users/frnkhrz/Documents/Peak_Trade_Archive/private_zip_import_20260811_non_peak_trade_personal_legal/`

Machine-readable provenance: [IMPORT_PROVENANCE.json](IMPORT_PROVENANCE.json)

---

## Safety notes

- Zip-slip / path traversal: none observed.
- No executable members observed.
- No canonical SSOT/runbook status fields were mutated by this import.
- No trading logic, Live/Testnet/Paper execution, or credentials touched.
