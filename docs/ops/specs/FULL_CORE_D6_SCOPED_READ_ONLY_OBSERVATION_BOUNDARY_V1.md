---
docs_token: DOCS_TOKEN_FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY_V1
status: active
scope: Full-Core D6 scoped read-only observation-boundary contract; four evidence domains defined not executed; GET unauthorized; U05/U06/Residual remain REMAIN_UNKNOWN; kind-set remains unresolved; Mini-Slice 2 not released; D7 not authorized; no venue GET; no reconstruction engine; no C17; no mapping; no producer; no runtime binding; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-13
---

# Full Core D6 Scoped Read Only Observation Boundary V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.AY.

```text
OWNER_GO=OWNER_GO_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY_CONTRACT_V1
SELECTED_OPTION=OPTION_D
OPTION_D_SSOT_PERSISTED=true
OBSERVATION_BOUNDARY_CONTRACT_CREATED=true
OBSERVATION_BOUNDARY_CONTRACT_STATUS=DEFINED_NOT_EXECUTED_GET_UNAUTHORIZED
OBSERVATION_EXECUTED=false
OBSERVATION_EXECUTION_AUTHORIZED=false
OBSERVATION_NETWORK_GET_AUTHORIZED=false
EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED=false
ACCOUNT_COMPOSITION_OBSERVATION_DEFINED=true
LIABILITY_OBSERVATION_DEFINED=true
FEE_EMBEDDING_OBSERVATION_DEFINED=true
EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED=true
OBSERVATION_IS_NOT_SOURCE_AUTHORITY=true
OBSERVATION_IS_NOT_KIND_RATIFICATION=true
OBSERVATION_IS_NOT_MS2_RELEASE=true
OBSERVATION_IS_NOT_D7_AUTHORIZATION=true
OBSERVATION_IS_NOT_RAW_EQ_SOURCE_AUTHORITY=true
OBSERVATION_IS_NOT_COMPLETENESS_UNLESS_RANGE_ORDERING_PROVENANCE_PROVEN=true
U05_KIND_DECISION=REMAIN_UNKNOWN
U06_KIND_DECISION=REMAIN_UNKNOWN
RESIDUAL_KIND_DECISION=REMAIN_UNKNOWN
KIND_SET_RESOLVED=false
RATIFIED_CLASSIFIED_EVENT_KIND_SET=EMPTY_FAIL_CLOSED
MS1_KIND_SET_FULLY_CLOSED=false
MS2_AUTHORIZED=false
D6_FULLY_CLOSED=false
D7_AUTHORIZED=false
PATH_A=REJECT
PATH_B=SELECTED_BUT_BLOCKED_ON_NEW_AUTHORIZATION
PATH_C=REJECT
CANDIDATE_SURFACE_SELECTION=NONE_SELECTED
ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL=true
ATLAS_AUTHORITY=NONE
PAPER_SIMULATED_FEE_ACCOUNTING_IS_NON_VENUE_EVIDENCE=true
C01_REHABILITATION_FORBIDDEN=true
AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT=false
EVENT_KIND_SOURCE_SEAM_SELECTED=false
SOURCE_SELECTED=false
RAW_EQ_SOURCE_AUTHORITY=false
MAPPING_PROVEN=false
C17_CREATED=false
RECONSTRUCTION_ENGINE_CREATED=false
NETWORK_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT
EARLIEST_D6_KIND_SET_DEPENDENCY=NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET
EARLIEST_D6_COMPLETENESS_DEPENDENCY=RATIFIED_CLASSIFIED_EVENT_KIND_SET_AND_AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM
AUTHORITY_EFFECT=NONE
```

This persist defines the fail-closed observation boundary that a later,
separately authorized empirical read-only evidence collection may use.
It does not execute observation. It does not authorize GET. It does not
ratify kinds. Mini-Slice 2 is not authorized. D7 is not released.

Four evidence domains remain exactly separate:

1. `ACCOUNT_COMPOSITION_OBSERVATION` proves which components are already
   inside the bound checkpoint `eq`. It does not use `eq` as source
   authority, mint equity, rehabilitate C01, or derive event taxonomy
   from a snapshot.
2. `LIABILITY_OBSERVATION` proves whether genuine borrow/account
   liability exists, whether it affects EQUITY_STOCK, and whether it is
   already embedded. It may later enable U05 INCLUDE or EXCLUDE only
   under the stated preconditions.
3. `FEE_EMBEDDING_OBSERVATION` proves whether accrued/already-charged
   fees are already in `eq`, a separate account delta, or
   reconciliation-only. Paper/simulated fee accounting remains
   `NON_VENUE_EVIDENCE`. It may later enable U06 INCLUDE or EXCLUDE
   only under the stated preconditions.
4. `EXOGENOUS_EVENT_COVERAGE_OBSERVATION` records presence or absence of
   deposit, withdrawal, transfer, funding, interest, liquidation, and
   convert inside an explicit checkpoint window. None of those classes
   are ratified here. Absence in an arbitrary small window is not
   global zero. Completeness requires explicit coverage provenance.

Venue surfaces are data classes plus unselected `CANDIDATE_SURFACE`
records only. `GET &#47;api&#47;v5&#47;account&#47;bills` remains
CURRENT_NONCANONICAL with `ATLAS_AUTHORITY=NONE`.
