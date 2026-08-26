# Peak_Trade Information Corpus Persistence Base

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_INFORMATION_CORPUS_PERSISTENCE_BASE
DOCUMENT_ROLE=REGISTRY_AND_NAVIGATION_ONLY
AUTHORITY=NONE
TARGET_AUTHORITY=NONE
CANONICAL=false
SECOND_SSOT=false
SEMANTIC_AUTHORITY=false
RUNTIME_AUTHORIZATION_EFFECT=NONE

MASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT=true
MAP_OF_TRUTH_REMAINS_NAVIGATION_ONLY=true
THIS_BASE_MUST_NOT_OVERRIDE_MASTER_RUNBOOK=true
THIS_BASE_MUST_NOT_OVERRIDE_MAP_OF_TRUTH=true
THIS_BASE_MUST_NOT_BE_USED_AS_OWNER_DECISION_AUTHORITY=true
THIS_BASE_MUST_NOT_BE_USED_AS_TYPE_ONTOLOGY_AUTHORITY=true
THIS_BASE_MUST_NOT_ACTIVATE_LIVE_TESTNET_ORDERS_OR_CREDENTIALS=true

EXTERNAL_SOURCE_FOLDER_IS_NOT_THIS_BASE=true
OWNER_NAMED_PEAK_TRADE_FORENSIK_FOLDER_IS_NOT_SSOT=true
```

Purpose: persist discovery, identity, and provenance registration for
Peak_Trade information-corpus work so a later main agent can continue
without chat memory.

This directory may register locators and hashes from repo sources and
from authorized external read-only surfaces. It must not rewrite those
sources. It must not present an external locator as originally
repo-internal.

## Layout

| Path | Role |
|------|------|
| `AUTHORITY_NONE.txt` | Authority containment |
| `PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md` | This index |
| `registries/EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md` | P2 discovery closeout plus P1/P3–P7 inventory |
| `registries/CROSS_CORPUS_RELATION_REGISTER_V1.md` | Proven vs unknown relations |
| `inventories/P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.json` | Repo forensic-tree file identities |
| `inventories/P5_DOCUMENTS_PEAK_TRADE_FORENSICS_FILE_INVENTORY_V1.json` | Evidence-bound local `Documents/Peak_Trade/forensics` identities |
| `inventories/CROSS_CORPUS_RELATION_FACTS_V1.json` | Machine relation facts |

## Provenance classes used here

```text
SOURCE_CLASS=REPO_INTERNAL
SOURCE_CLASS=LOCAL_EXTERNAL_FORENSIC_SOURCE
SOURCE_CORPUS=OWNER_NAMED_PEAK_TRADE_FORENSIK_FOLDER
SOURCE_CORPUS_P2_STATUS=NOT_UNIQUELY_RESOLVED
P2_CONTENT_INVENTORY_STATUS=NOT_PERFORMABLE_WITHOUT_RESOLVED_CORPUS
P2_UNRESOLVED_IS_NOT_P2_EMPTY=true
SOURCE_CORPUS=DOCUMENTS_PEAK_TRADE_FORENSICS_EVIDENCE_BOUND_P5_NOT_OWNER_NAMED_FORENSIK_FOLDER
```

BYTE_IDENTICAL does not merge source identity. Both locators remain.
Unresolved P2 is not an empty-corpus claim.
