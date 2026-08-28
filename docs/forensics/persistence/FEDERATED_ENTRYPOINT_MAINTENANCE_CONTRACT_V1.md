# FEDERATED_ENTRYPOINT_MAINTENANCE_CONTRACT_V1

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_FEDERATED_ENTRYPOINT_MAINTENANCE_CONTRACT
DOCUMENT_ROLE=PROCESS_CONTRACT_FOR_FUTURE_FORENSIC_PERSISTENCE
AUTHORITY=NONE
TARGET_AUTHORITY=NONE
NAVIGATION_ONLY_OR_REFERENCE_LAYER=true
SECOND_SSOT=false
SEMANTIC_AUTHORITY=false
CANONICAL=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
THIS_CONTRACT_IS_NOT_CANONICAL_AUTHORITY=true
THIS_CONTRACT_MUST_NOT_OVERRIDE_MASTER_RUNBOOK=true
THIS_CONTRACT_MUST_NOT_OVERRIDE_MAP_OF_TRUTH=true
THIS_CONTRACT_MUST_NOT_REPLACE_PRIMARY_EVIDENCE=true
THIS_CONTRACT_MUST_NOT_RECOMPUTE_DOMAIN_DECISIONS=true
NEW_DOMAIN_ONTOLOGY_CREATED=false
NEW_OBSERVATION_CREATED=false
OWNER_GO=PEAK_TRADE_FEDERATED_FORENSIC_ENTRYPOINT_MAINTENANCE_CONTRACT_PERSIST_V1
bound_origin_main_sha=ec5e6eef3d316277feb448b40ae0da223cd9ce53
```

Purpose: keep the PR-#6108 federated entrypoint from going stale.
Every later create or change under `docs&#47;forensics&#47;persistence&#47;`
must run the checks below. Silent non-update is forbidden.

This file is process, not a subject projection and not an observation.

## Reuse adjudication

```text
CAN_EXISTING_CONTRACT_BE_EXTENDED_LOSSLESSLY=false
EXISTING_CANDIDATES_CONSIDERED=PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md;AUTHORITY_NONE.txt;P1_REPO_FORENSIC_TREES_FILE_INVENTORY_V1.contract.json;FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md;INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md;CURRENT_STATE_PROJECTION_V1.md;EXTERNAL_FORENSIC_CORPUS_DISCOVERY_V1.md
LOSSLESS_EXTENSION_BLOCKED_BECAUSE=Base is navigation/bootstrap not a mutation-process contract; AUTHORITY_NONE.txt is containment only; P1 sidecar binds a historical inventory snapshot; L0/L2/L4 are architecture layers not a maintenance process over themselves; discovery registry is P2/P5-scoped
NEW_ARTIFACT_ROLE=FEDERATED_ENTRYPOINT_MAINTENANCE_PROCESS_CONTRACT
```

## Bound architecture names (PR #6108)

These names must remain the federated layers. Do not invent parallel L0/L2/L4 files.

| Layer | Stable filename | Locator from this file |
|-------|-----------------|------------------------|
| Bootstrap | `PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md` | [Persistence Base](PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md) |
| L0 | `FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md` | [L0 Source Surface Registry](registries/FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md) |
| L2 | `INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md` | [L2 Information Object Reference Registry](registries/INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md) |
| L4 | `CURRENT_STATE_PROJECTION_V1.md` | [L4 Current State Projection](registries/CURRENT_STATE_PROJECTION_V1.md) |

```text
L0_STABLE_NAME=FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md
L2_STABLE_NAME=INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md
L4_STABLE_NAME=CURRENT_STATE_PROJECTION_V1.md
PARALLEL_L0_L2_L4_REGISTRY_CREATION_FORBIDDEN=true
```

## Scope

Applies to every new or changed file under:

`docs&#47;forensics&#47;persistence&#47;`

including inventories, registries, this contract, and the Persistence Base.

Does not authorize Live, Testnet, Canary, trading, canonical mutation,
source-code mutation, config mutation, or external-corpus copy.

## Default discovery order

Future forensic workpackages MUST start here, in this order:

1. [Persistence Base](PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md)
2. L0 [FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md](registries/FEDERATED_SOURCE_SURFACE_REGISTRY_V1.md)
3. L2 [INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md](registries/INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md)
4. L4 [CURRENT_STATE_PROJECTION_V1.md](registries/CURRENT_STATE_PROJECTION_V1.md)
5. targeted primary evidence named by L2/L4 locators

```text
DEFAULT_DISCOVERY_ORDER_ENFORCED=true
BROAD_REDISCOVERY_REQUIRES_INSUFFICIENCY_FINDING=true
```

Broad repo / external / transcript rediscovery is allowed only when:

```text
FEDERATED_ENTRYPOINT_INSUFFICIENT=true
MISSING_INFORMATION_TYPE=<named>
```

Absence of a preferred narrative is not insufficiency. P2 unresolved
remains unresolved, not empty.

## 1. SUBJECT_IMPACT_CHECK

Required for every persistence mutation.

Against subjects already registered in
[INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md](registries/INFORMATION_OBJECT_REFERENCE_REGISTRY_V1.md),
determine whether the new or changed artifact:

- supplements a registered subject,
- supersedes a supporting artifact for that subject,
- newly adjudicates that subject,
- adds new evidence for that subject,
- changes an open residual status,
- changes an Owner-decision status,
- or introduces a new relevant artifact locator.

Record:

```text
SUBJECT_IMPACT_CHECK=PERFORMED
IMPACTED_INFORMATION_OBJECT_IDS=<none|list>
SUBJECT_SUPPLEMENTED=true|false
SUBJECT_SUPERSEDED=true|false
SUBJECT_NEWLY_ADJUDICATED=true|false
SUBJECT_NEW_EVIDENCE_ADDED=true|false
SUBJECT_RESIDUAL_STATUS_CHANGED=true|false
SUBJECT_OWNER_DECISION_STATUS_CHANGED=true|false
SUBJECT_NEW_ARTIFACT_LOCATOR_INTRODUCED=true|false
```

## 2. L0 impact check

`L0_UPDATE_REQUIRED=true` if the persist introduces a new source surface
or a new source-identity class not already in L0.

Otherwise `L0_UPDATE_REQUIRED=false`.

Adding files under an already registered surface (for example SS-03) is
not by itself a new source surface.

## 3. L2 impact check

`L2_UPDATE_REQUIRED=true` if artifact / locator / subject bindings
change: new alias, changed locator, new or retired information object,
or changed `SUPPORTING_ARTIFACT_IDS_OR_LOCATORS` /
`OPEN_RESIDUAL_IDS` / `RELATED_REGISTER_IDS`.

Otherwise `L2_UPDATE_REQUIRED=false`.

## 4. L4 impact check

`L4_UPDATE_REQUIRED=true` if any of the following changes for a
registered projected subject:

- `CURRENT_KNOWN_STATE`
- latest forensic adjudication
- Owner decision
- open residual
- historical predecessor
- conflict
- implementation binding

Otherwise `L4_UPDATE_REQUIRED=false`.

L4 remains derived navigation. Updating L4 is not a new domain
adjudication.

## 5. No-change proof

If L0, L2, and L4 are not updated:

```text
FEDERATED_ENTRYPOINT_UPDATE_NOT_REQUIRED=true
FEDERATED_ENTRYPOINT_NO_CHANGE_PROOF=<short verifiable reason>
```

Silent omission is a contract fail.

A Persistence Base **index/layout pointer** to a new architecture or
contract file is not an L0/L2/L4 subject-state update. It is still
required when a new durable persistence file must be discoverable.

## 6. Primary-evidence rule

```text
AUTHORITY=NONE
NAVIGATION_ONLY_OR_REFERENCE_LAYER=true
PROJECTION_IS_NOT_CANONICAL=true
PROJECTION_IS_NOT_NEW_ADJUDICATION=true
L0_L2_L4_DO_NOT_REPLACE_PRIMARY_EVIDENCE=true
L0_L2_L4_DO_NOT_REPLACE_CANONICAL_AUTHORITY=true
```

Payloads stay in original artifacts. L2/L4 reference; they do not copy
external large files.

## 7. Immutability rule

```text
HISTORICAL_OBSERVATION_REWRITE_DEFAULT=false
HISTORICAL_OBSERVATION_REWRITE_COUNT_MUST_BE_ZERO_UNLESS_EXISTING_CONTRACT_REQUIRES_INDEX_UPDATE=true
```

Do not rewrite historical observations merely to add backlinks.
New registry or projection bindings point **to** historical artifacts.

## 8. Required report block for future persistence mutates

Every authorized persist under this tree must include:

```text
SUBJECT_IMPACT_CHECK=PERFORMED
IMPACTED_INFORMATION_OBJECT_IDS=
L0_UPDATE_REQUIRED=
L2_UPDATE_REQUIRED=
L4_UPDATE_REQUIRED=
FEDERATED_ENTRYPOINT_UPDATE_NOT_REQUIRED=
FEDERATED_ENTRYPOINT_NO_CHANGE_PROOF=
FEDERATED_ENTRYPOINT_INSUFFICIENT=false
MISSING_INFORMATION_TYPE=
HISTORICAL_OBSERVATION_REWRITE_COUNT=0
```

If any of `L0_UPDATE_REQUIRED`, `L2_UPDATE_REQUIRED`, or
`L4_UPDATE_REQUIRED` is true, the corresponding PR-#6108 layer file
must be updated in the **same** persist, or the persist is incomplete.

## This persist (dogfood)

This file is the maintenance contract itself. It does not change any
registered subject's evidence, residuals, or Owner decisions. L0/L2/L4
bodies are unchanged. The Persistence Base gains a discoverability
pointer only.

```text
SUBJECT_IMPACT_CHECK=PERFORMED
IMPACTED_INFORMATION_OBJECT_IDS=none
SUBJECT_SUPPLEMENTED=false
SUBJECT_SUPERSEDED=false
SUBJECT_NEWLY_ADJUDICATED=false
SUBJECT_NEW_EVIDENCE_ADDED=false
SUBJECT_RESIDUAL_STATUS_CHANGED=false
SUBJECT_OWNER_DECISION_STATUS_CHANGED=false
SUBJECT_NEW_ARTIFACT_LOCATOR_INTRODUCED=false
L0_UPDATE_REQUIRED=false
L2_UPDATE_REQUIRED=false
L4_UPDATE_REQUIRED=false
FEDERATED_ENTRYPOINT_UPDATE_NOT_REQUIRED=true
FEDERATED_ENTRYPOINT_NO_CHANGE_PROOF=process_contract_only_no_new_source_surface_no_subject_binding_change_no_current_state_change;_Base_index_pointer_required_for_discoverability
FEDERATED_ENTRYPOINT_INSUFFICIENT=false
MISSING_INFORMATION_TYPE=
HISTORICAL_OBSERVATION_REWRITE_COUNT=0
NEW_OBSERVATION_CREATED=false
```
