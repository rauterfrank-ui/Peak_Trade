# Peak_Trade Forensic STEP 15 — Non-Authoritative Transformation Invariant Contract

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_TRANSFORMATION_INVARIANT_CONTRACT
ARTIFACT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
PREVIEW_AUTHORITY=NONE
CANONICAL_AUTHORITY_CLAIMED=false
SECOND_SSOT=false
MASTER_RUNBOOK_REMAINS_SOLE_SSOT=true
NOT_CANONICAL=true
NOT_TARGET_REPLACEMENT=true
NOT_THE_TARGET=true
NOT_THE_STEP9_ARTIFACT=true
NOT_THE_STEP13_PREVIEW=true
NOT_THE_MASTER_RUNBOOK=true
NOT_THE_MAP_OF_TRUTH=true
NOT_A_REPOSITORY_FILE=true
SPECIFICATION_ONLY=true
TRANSFORMATION_EXECUTED=false
CANONICALIZATION_EXECUTED=false
AUTHORITY_PROMOTION_EXECUTED=false
TARGET_MUTATED=false
STEP_10_STARTED=false
CARRIER_PAYLOAD_SYNTHESIZED=false
TARGET_BYTE_READ_REQUIRED=false
KR8_KR9_GLYPH_RENDERING=false
EPISTEMIC_RECLASSIFICATION_EXECUTED=false
UNRESOLVED_CLOSEOUT_EXECUTED=false
H91_KR11_FUSION_EXECUTED=false
NEXT_WRITE_AUTHORIZED=false
STEP=STEP_15_BOUNDED_NON_AUTHORITATIVE_TRANSFORMATION_INVARIANT_CONTRACT_SPECIFICATION_ONLY
```

```text
RESERVED_DESTINATION_PATH=/Users/frnkhrz/Desktop/PEAK_TRADE_FORENSIC_STEP15_NON_AUTHORITATIVE_TRANSFORMATION_INVARIANT_CONTRACT.md
TARGET_PATH=/Users/frnkhrz/Desktop/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md
TARGET_SHA256=08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092
SOURCE_STEP9_PATH=/Users/frnkhrz/Desktop/PEAK_TRADE_FORENSIC_STEP9_PRODUCTION_TRANSFORMATION_AUTHORITY_NONE_NOT_TARGET_NOT_SSOT.json
SOURCE_STEP9_SHA256=53a0f29f480cf46bdb9c0a9cf25a15dd701fe9ecbe99e53f1f1822058d4fbdd8
SOURCE_PREVIEW_PATH=/Users/frnkhrz/Desktop/PEAK_TRADE_FORENSIC_STEP13_STRUCTURED_INVENTORY_PREVIEW_AUTHORITY_NONE_NOT_TARGET_NOT_SSOT.json
SOURCE_PREVIEW_SHA256=ba1a7d843826b8c008003b46fc48e8aac390ba23e241bd18291db6ed56db40da
SOURCE_PREVIEW_SIZE_BYTES=43022985
MASTER_RUNBOOK_PATH=/Users/frnkhrz/Peak_Trade/docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
MASTER_RUNBOOK_SHA256=65f833565d64517eae496e4cb3289525573dd2d3387429ba8d4ddc189c5b8b98
MAP_OF_TRUTH_PATH=/Users/frnkhrz/Peak_Trade/docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md
MAP_OF_TRUTH_SHA256=97f8d389fa93d36c09e53c65db21242a6c7f777d6f8d01531e73f6815074ee9d
ORIGIN_MAIN_SHA_BINDING=652c2cd4f9e91160a46b86f02014fd019ec33ca5
```

Eine bessere Struktur, dieser Vertrag selbst und jede spätere Einhaltung dieses Vertrags erzeugen keine Authority.

------------------------------------------------------------------------

## 0. Epistemic class legend

Jede Aussage in diesem Artefakt gehört zu genau einer der folgenden Klassen. Klassen dürfen nicht stillschweigend ineinander überführt werden.

```text
OBSERVED_BASELINE_FACT
  Am STEP-14-Preview-Artefakt (SHA256=ba1a7d843826b8c008003b46fc48e8aac390ba23e241bd18291db6ed56db40da)
  durch vollständigen JSON-Walk festgestellt; hier nur wiederholt, nicht neu gemessen.

INHERITED_ADJUDICATED_FACT
  Bereits vor STEP 15 adjudizierte Schlussfolgerung, geerbt, nicht wiedereröffnet.
  Insbesondere Envelope-H91.

TRANSFORMATION_INVARIANT
  Anforderung an eine später separat autorisierte Transformation.
  Kein Beweis, dass eine Transformation bereits stattgefunden hat.
  Kein Beweis, dass eine künftige Transformation bereits konform ist.

FORBIDDEN_OPERATION
  In STEP 15 und in jeder späteren Transformation ohne neues, engeres Owner-GO verboten.

FUTURE_POSTCONDITION
  Was eine spätere Transformation beweisen müsste, falls sie autorisiert wird.
  Nicht als gegenwärtiger Zustand behaupten.

OPEN_UNRESOLVED
  Offener Bestand. Darf durch diesen Vertrag nicht geschlossen, fusioniert
  oder umklassifiziert werden.
```

------------------------------------------------------------------------

## 1. Scope

```text
CLASS=TRANSFORMATION_INVARIANT
SCOPE_THIS_ARTIFACT=SPECIFICATION_ONLY
SCOPE_TRANSFORMS_TARGET=false
SCOPE_REPLACES_TARGET=false
SCOPE_REPLACES_PREVIEW=false
SCOPE_REPLACES_STEP9=false
SCOPE_MUTATES_REPOSITORY=false
SCOPE_AUTHORIZES_STEP_10=false
SCOPE_AUTHORIZES_CANONICALIZATION=false
SCOPE_AUTHORIZES_TARGET_BYTE_READ=false
SCOPE_AUTHORIZES_CARRIER_PAYLOAD=false
SCOPE_AUTHORIZES_UNRESOLVED_CLOSEOUT=false
```

Dieser STEP 15 spezifiziert ausschließlich den Invariantenvertrag für eine **eventuell später, separat per Owner-GO autorisierte** verlustfreie Transformation der Desktop-MD.

Er führt keine Transformation aus.

Er ist nicht das Target, nicht die Preview, nicht STEP 9, nicht das Master Runbook, nicht die Map of Truth.

------------------------------------------------------------------------

## 2. Authority Boundary

```text
CLASS=TRANSFORMATION_INVARIANT
TARGET_AUTHORITY=NONE
PREVIEW_AUTHORITY=NONE
ARTIFACT_AUTHORITY=NONE
CANONICAL_AUTHORITY_CLAIMED=false
SECOND_SSOT=false
MASTER_RUNBOOK_REMAINS_SOLE_SSOT=true
AUTHORITY_PROMOTION_BY_BETTER_STRUCTURE=FORBIDDEN
```

```text
CLASS=OBSERVED_BASELINE_FACT
PREVIEW_ENVELOPE.PREVIEW_AUTHORITY="NONE"
PREVIEW_ENVELOPE.TARGET_AUTHORITY="NONE"
PREVIEW_ENVELOPE.MASTER_RUNBOOK_REMAINS_SOLE_SSOT=true
PREVIEW_ENVELOPE.NOT_CANONICAL=true
PREVIEW_ENVELOPE.NOT_TARGET_REPLACEMENT=true
PREVIEW_ENVELOPE.CANONICALIZATION_EXECUTED=false
PREVIEW_ENVELOPE.STEP_10_STARTED=false
PREVIEW_ENVELOPE.NEXT_WRITE_AUTHORIZED=false
CATALOG_RECORDS[*].authority_status="NONE"   # N=23961
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_IMPLIED_AUTHORITY_FROM_STRUCTURE
FORBID_AUTHORITY_PROMOTION
FORBID_SECOND_SSOT
FORBID_TREATING_THIS_CONTRACT_AS_CANONICAL_OWNER
FORBID_TREATING_PREVIEW_AS_SSOT
FORBID_TREATING_TARGET_MD_AS_SSOT
```

Map of Truth bleibt Navigation only und definiert keine Semantik.

------------------------------------------------------------------------

## 3. Source / Provenance Bindings

```text
CLASS=OBSERVED_BASELINE_FACT
TARGET_SHA256=08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092
TARGET_SIZE_BYTES=1421764
STEP9_SHA256=53a0f29f480cf46bdb9c0a9cf25a15dd701fe9ecbe99e53f1f1822058d4fbdd8
PREVIEW_SHA256=ba1a7d843826b8c008003b46fc48e8aac390ba23e241bd18291db6ed56db40da
PREVIEW_SIZE_BYTES=43022985
MASTER_RUNBOOK_SHA256=65f833565d64517eae496e4cb3289525573dd2d3387429ba8d4ddc189c5b8b98
MAP_OF_TRUTH_SHA256=97f8d389fa93d36c09e53c65db21242a6c7f777d6f8d01531e73f6815074ee9d
ORIGIN_MAIN_SHA_BINDING=652c2cd4f9e91160a46b86f02014fd019ec33ca5
```

```text
CLASS=TRANSFORMATION_INVARIANT
A later transformation, if separately authorized, MUST bind to these identities
or FAIL CLOSED if any binding drifted.
STEP9 remains an independent provenance artifact. Preview is a five-layer
inventory of STEP9 catalog/lines/carriers plus preview chrome; it is not a
byte-complete substitute for STEP9 chrome.
Target identity may be checked by SHA256/size only. Glyph/content reads of
the target are not authorized by this contract.
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_TREATING_ABSENCE_OF_STEP9_CHROME_FROM_PREVIEW_AS_NONEXISTENCE_OF_THAT_CHROME
FORBID_TARGET_GLYPH_READ_UNDER_THIS_CONTRACT
FORBID_USING_THIS_CONTRACT_TO_REPAIR_CURRENT_FORENSIC_TRUTH_SHA_LAG
```

Der bereits dokumentierte SSOT-Feld-Lag `CURRENT_FORENSIC_TRUTH_SHA` hinter HEAD ist kein Gegenstand dieses Vertrags und darf hier nicht repariert werden.

------------------------------------------------------------------------

## 4. Five-layer model

```text
CLASS=OBSERVED_BASELINE_FACT
PREVIEW_ROOT_KEY_ORDER=
  1. PREVIEW_ENVELOPE
  2. CLOSED_TYPE_ROSTER
  3. CATALOG_RECORDS
  4. LINE_ENTRIES
  5. KR8_KR9_SOURCE_BYTE_CARRIER_INDEX
PREVIEW_ROOT_KEY_COUNT=5
NO_OTHER_ROOT_KEYS
```

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT five_layers_complementary
ASSERT NOT replaceable(PREVIEW_ENVELOPE, CATALOG_RECORDS)
ASSERT NOT replaceable(CLOSED_TYPE_ROSTER, CATALOG_RECORDS)
ASSERT NOT replaceable(LINE_ENTRIES, CATALOG_RECORDS)
ASSERT NOT replaceable(KR8_KR9_SOURCE_BYTE_CARRIER_INDEX, CATALOG_RECORDS)
ASSERT NOT replaceable(KR8_KR9_SOURCE_BYTE_CARRIER_INDEX, LINE_ENTRIES)
```

Rollen:

- `PREVIEW_ENVELOPE`: Preview-Chrome, Authority-Negationen, Bindings, Zählwerte, Envelope-H91. Nicht Catalog-Schema.
- `CLOSED_TYPE_ROSTER`: geschlossene Typmenge und Instanzzählung. Erzeugt keine Records.
- `CATALOG_RECORDS`: typisierte Inventar-Records.
- `LINE_ENTRIES`: zeilenweise Rekonstruktionsbuchhaltung, nicht redundant zum Catalog.
- `KR8_KR9_SOURCE_BYTE_CARRIER_INDEX`: Byte-Index für Modell-Löcher, kein Record-Type.

```text
CLASS=FORBIDDEN_OPERATION
FORBID_DROPPING_ANY_LAYER
FORBID_MERGING_LAYERS
FORBID_TREATING_ROSTER_AS_RECORD_GENERATOR
FORBID_TREATING_CARRIER_INDEX_AS_38TH_RECORD_TYPE
```

------------------------------------------------------------------------

## 5. Closed Type Roster

```text
CLASS=OBSERVED_BASELINE_FACT
CLOSED_SCHEMA_TYPE_COUNT=37
INSTANTIATED_TYPE_COUNT=11
ABSENT_TYPE_COUNT=26
UNKNOWN_SCHEMA_TYPE_COUNT=0
NO_38TH_ENTITY=true
ROSTER_INSTANCE_SUM=23961
```

Instanziiert (OBSERVED_BASELINE_FACT):

```text
AddressableStatement=18064
DeclaredVerbatimBody=2
MarkedVerbatimRegion=5
MatrixRow=2532
NestedStructuralChild=2243
NonActionConstraint=288
OwnerDecision=73
PassNameFacet=184
PhysicalAppendUnit=99
ShaNamedValue=405
TimestampOccurrence=66
```

Absent bleiben absent (OBSERVED_BASELINE_FACT count=0; TRANSFORMATION_INVARIANT: nicht instantiieren):

```text
ClassificationCorrectionAppend
CuratedDerivation
DerivedView
EffectBoundary
EnvelopeRecord
EvidenceItem
ExternalMirrorRecord
GateAssertion
GateFamily
HeadingGapObservation
IdentifiedWorkingObject
ImplementationReport
JoinGraphSnapshot
Matrix
MatrixCell
MutationOrPersistenceEvent
OpenIssue
PreparedRecommendation
PreservationContract
ProofAxisConstraint
ProvenanceRecord
RollupSnapshot
SnapshotRecord
SourceArtifact
TransitionAssertion
UnresolvedRelation
```

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT roster_n == 37
ASSERT instantiated_n == 11
ASSERT absent_n == 26
ASSERT unknown_n == 0
ASSERT no_type not_in roster
ASSERT NOT instantiate(absent_type)
ASSERT NOT invent_record_type
ASSERT NOT entity_38
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_AUTO_INSTANTIATION_OF_ABSENT_TYPES
FORBID_SYNTHESIZING_UNRESOLVEDRELATION_FROM_THE_19
FORBID_SYNTHESIZING_ENVELOPERECORD_FROM_PREVIEW_ENVELOPE
FORBID_SYNTHESIZING_OPENISSUE_FROM_NOTES
```

------------------------------------------------------------------------

## 6. Catalog

```text
CLASS=OBSERVED_BASELINE_FACT
CATALOG_RECORD_COUNT=23961
CATALOG_KEYS_PER_RECORD=39
CATALOG_KEY_ORDER=
  seq, record_type, transform_rule, source_start, source_end, raw_text,
  raw_heading, raw_key, raw_value, classification, representation_form,
  parent_id, pau_id, fence_id, verbatim_region_id, in_fence, in_pau,
  in_verbatim, delimiter_form, facet_kind, heading_level,
  verbatim_claim_status, byte_offset_start, byte_offset_end,
  provenance_form, epistemic_status, currentness, adjudication_status,
  authority_status, navigation_status, unresolved_status,
  creates_new_parent, occurrence_index, physical_order,
  sha_field_name_literal, sha_value_raw, statement_id, child_id, notes
SEQ_UNIQUE=true
SEQ_MIN=1
SEQ_MAX=23961
SEQ_EQUALS_ARRAY_INDEX=false
SEQ_GLOBALLY_MONOTONE_IN_ARRAY=false
SEQ_DESCENTS_IN_ARRAY=1193
ARRAY_ORDER_SOURCE_START_NON_DECREASING=true
ARRAY_ORDER_SOURCE_START_STRICT_INCREASING=false
SOURCE_START_LE_SOURCE_END_ALL=true
SINGLE_LINE_RECORDS=22761
MULTI_LINE_RECORDS=1200
SOURCE_LINES_1_TO_30870_COVERED_BY_AT_LEAST_ONE_SPAN=true
NESTEDSTRUCTURALCHILD_SEQ_DESCENTS_IN_TYPE_ORDER=829
CREATES_NEW_PARENT_ALL_FALSE=true
IN_PAU_ALL_TRUE=true
FLOAT_VALUES_IN_CATALOG=0
```

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT count(CATALOG_RECORDS) == 23961
ASSERT array_order preserved as stored (physical source_start non-decreasing with nesting)
ASSERT seq is identity only
ASSERT NOT sort_by(seq) as document order
ASSERT NOT treat seq as array index
ASSERT each record retains the 39-key insertion order
ASSERT source_start/source_end integer spans preserved
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_SEQ_REORDER_AS_PHYSICAL_ORDER
FORBID_DROPPING_OR_INSERTING_CATALOG_RECORDS
FORBID_CHANGING_RECORD_TYPE_EXCEPT_BY_FUTURE_SEPARATE_GO_THAT_THIS_CONTRACT_DOES_NOT_GRANT
```

------------------------------------------------------------------------

## 7. Ordering / Chronology

```text
CLASS=OBSERVED_BASELINE_FACT
PHYSICAL_ARRAY_ORDER=source_start_non_decreasing
PAU_PHYSICAL_ORDER_1_TO_99_UNIQUE=true
PAU_SOURCE_START_NON_DECREASING=true
LINE_ENTRIES.line_strict_sequence_1_to_30870=true
CARRIER.line_strict_increasing_unique=true
currentness_field_all_null=true
```

```text
CLASS=TRANSFORMATION_INVARIANT
Physical document order is the catalog array order / source_start order,
not seq, not grouping by record_type, not grouping by heading, not
grouping by pass name, not a newly invented implementation sequence.
Historical intermediate states MUST NOT be re-presented as current by
reordering, heading chrome, or clustering.
No new gate boundary, dependency, or implementation order may be invented.
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_REORDER_TO_MAKE_HISTORICAL_CONTENT_APPEAR_CURRENT
FORBID_INVENTING_GATE_BOUNDARIES
FORBID_INVENTING_IMPLEMENTATION_SEQUENCE
FORBID_USING_HEADINGS_AS_CURRENTNESS_PROMOTION
```

------------------------------------------------------------------------

## 8. Line Entries

```text
CLASS=OBSERVED_BASELINE_FACT
LINE_ENTRIES_COUNT=30870
LINE_KEYS=line,reason,recon_source,model_has_independent_bytes,source_line_sha256,source_line_nbytes,matches_oracle
LINE_UNIQUE_AND_STRICT_1_TO_30870=true
matches_oracle_all_true=true
source_line_nbytes_sum=1421764
model_has_independent_bytes_false=4856
model_has_independent_bytes_true=26014
```

Catalog `transform_rule` und Line `reason` sind getrennte Vokabulare.

```text
CLASS=OBSERVED_BASELINE_FACT
CATALOG_TRANSFORM_RULE_NOT_IN_LINE_REASON=
  TR-003, TR-005, TR-007, TR-009, TR-015, TR-016, TR-022, TR-024, TR-025, TR-029, TR-030
LINE_REASON_NOT_IN_CATALOG_TRANSFORM_RULE=
  KR-8, KR-9, KR-1, TR-009_MARKER, TR-015_MARKER, TR-003_PAU_START,
  TR-003f+TR-021, TR-007_DASH, TR-007_EQ, A23_TR005_LEFTOVER_FENCE_MARKER
```

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT count(LINE_ENTRIES)==30870
ASSERT LINE_ENTRIES are not redundant with CATALOG_RECORDS
ASSERT reason vocabulary remains distinct from transform_rule vocabulary
ASSERT per-line source_line_sha256 and source_line_nbytes preserved
ASSERT recon_source preserved
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_DROPPING_LINE_ENTRIES_AS_REDUNDANT
FORBID_REWRITING_LINE_REASON_TO_MATCH_TRANSFORM_RULE
FORBID_REWRITING_TRANSFORM_RULE_TO_MATCH_LINE_REASON
```

------------------------------------------------------------------------

## 9. Occupancy / Overlap

```text
CLASS=OBSERVED_BASELINE_FACT
OCCUPANCY_SPAN_HITS_SUM=73740
OCCUPANCY_PER_SOURCE_LINE_MIN=1
OCCUPANCY_PER_SOURCE_LINE_MAX=5
OCCUPANCY_HISTOGRAM=
  1:4831
  2:10417
  3:14423
  4:1189
  5:10
```

```text
CLASS=TRANSFORMATION_INVARIANT
Overlapping catalog spans are stored fact, not defect.
ASSERT occupancy_max_preserved (>=1 and allowed up to 5 as stored)
ASSERT NOT collapse_to_one_record_per_line
ASSERT NOT occupancy_concatenation
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_OCCUPANCY_DEDUPLICATION
FORBID_ONE_LINE_ONE_RECORD_REDUCTION
FORBID_CONCATENATING_OVERLAPPING_SPANS
```

------------------------------------------------------------------------

## 10. Duplicate content

```text
CLASS=OBSERVED_BASELINE_FACT
IDENTICAL_RAW_TEXT_MULTI_GROUPS=1871
RECORDS_IN_THOSE_GROUPS=9877
SHA_NAMED_VALUE_RECORDS=405
SHA_VALUE_RAW_DISTINCT=67
SHA_VALUE_RAW_LEN64=40
```

```text
CLASS=TRANSFORMATION_INVARIANT
Identical raw_text across multiple records is meaning-bearing.
ShaNamedValue records remain 405 individuals.
sha_value_raw is not a unique record identity.
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_TEXT_DEDUPLICATION
FORBID_SHA_BASED_DEDUPLICATION
FORBID_REDUCING_SHANAMEDVALUE_405_TO_67
FORBID_REDUCING_SHANAMEDVALUE_TO_THE_40_LEN64_VALUES
```

------------------------------------------------------------------------

## 11. Identity / Join / Parentage

```text
CLASS=OBSERVED_BASELINE_FACT
parent_id_null=99
parent_id_prefix_fence=15901
parent_id_prefix_pau=7961
parent_id_is_string_not_seq=true
parent_id_values_in_seq_set=0
pau_id_unique=99
pau_id_all_records_nonnull=99_unique_ids_on_23961_records
child_id_nonnull=2173
child_id_unique=2173
statement_id_nonnull=12435
statement_id_unique=12435
creates_new_parent_all_false=true
in_fence_true_and_fence_id_null=6
in_fence_false_and_fence_id_nonnull=0
```

Getrennte Identitätssysteme: `seq`, `parent_id`, `pau_id`, `child_id`, `statement_id`, `fence_id`, `verbatim_region_id`, `physical_order`, Line `line`, Carrier `line`.

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT NOT join_parent_id_via_seq
ASSERT creates_new_parent==false does not mean absence of parentage
ASSERT the 6 in_fence=true AND fence_id=null records remain exactly that
ASSERT identity systems remain unfused
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_JOIN_OVER_SEQ
FORBID_INTERPRETING_CREATES_NEW_PARENT_FALSE_AS_NO_PARENTAGE
FORBID_REPAIRING_IN_FENCE_TRUE_FENCE_ID_NULL
FORBID_FUSING_ID_SYSTEMS
```

------------------------------------------------------------------------

## 12. PhysicalAppendUnit

```text
CLASS=OBSERVED_BASELINE_FACT
PAU_COUNT=99
PAU_RAW_TEXT_JSON_NULL=99
PAU_RAW_HEADING_NONNULL=99
PAU_PHYSICAL_ORDER_1_TO_99=true
PAU_TRANSFORM_RULE=TR-003
PAU_NOTES='full-span raw_text not a required PAU field'  # n=99
```

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT pau_n==99
ASSERT pau.raw_text is JSON null
ASSERT physical_order preserved 1..99 unique
ASSERT NOT synthesize PAU payload from heading, children, or other records
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_PAU_BODY_SYNTHESIS
FORBID_FILLING_PAU_RAW_TEXT_FROM_CHILDREN
FORBID_REORDERING_PAU_PHYSICAL_ORDER
```

------------------------------------------------------------------------

## 13. Carrier contract

```text
CLASS=OBSERVED_BASELINE_FACT
CARRIER_COUNT=4856
CARRIER_KEYS=line,keeping_rule,independent_model_bytes,mechanism,synthesis,normalization,source_byte_offset,source_byte_length,source_line_sha256
CARRIER_HAS_RECORD_TYPE=false
CARRIER_HAS_PAYLOAD=false
KEEPING_RULE_KR9=4243
KEEPING_RULE_KR8=613
independent_model_bytes_all_false=true
mechanism_all=SOURCE_FILE_IDENTITY_COPY
synthesis_all_false=true
normalization_all_false=true
CARRIER_LINE_UNIQUE_STRICT_INCREASING=true
CARRIER_VS_LINE_SHA_MISMATCH=0
CARRIER_BYTE_LENGTH_VS_LINE_NBYTES_MISMATCH=0
MODEL_ONLY_HOLE_COUNT=4856
KR8_KR9_PARENT_SPAN_RECOVERABLE_FROM_LINE_ENTRIES=493
KR8_KR9_HOLES_FROM_LINE_ENTRIES=4856
```

Die 493 Parent-Span-KR-8/KR-9-Zeilen stehen in LINE_ENTRIES mit `reason in {KR-8,KR-9}` und `model_has_independent_bytes=true` und `recon_source` der Form `PARENT_SPAN:…`. Sie sind nicht im Carrier-Index.

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT carrier_n==4856
ASSERT SOURCE_BYTE_CARRIER_IS_NOT_A_SCHEMA_RECORD_TYPE
ASSERT NO_38TH_ENTITY
ASSERT no glyph / no payload / no synthesis / no normalization
ASSERT mechanism remains SOURCE_FILE_IDENTITY_COPY
ASSERT parent_span_493 NOT moved into carrier index
ASSERT carrier_holes_4856 NOT synthesized from parent spans
ASSERT preview_alone_insufficient_for_byte_identical_reconstruction
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_CARRIER_PAYLOAD_SYNTHESIS
FORBID_KR8_KR9_GLYPH_RENDERING
FORBID_TARGET_BYTE_READ_TO_FILL_CARRIERS_UNDER_THIS_CONTRACT
FORBID_PROMOTING_CARRIER_TO_RECORD_TYPE
FORBID_MOVING_493_PARENT_SPAN_LINES_INTO_CARRIER_INDEX
FORBID_SYNTHESIZING_4856_HOLES_FROM_PARENT_SPANS
FORBID_RECONSTRUCTING_BLANK_LINES_OR_DASH_RULES_INTO_CARRIERS
```

```text
CLASS=FUTURE_POSTCONDITION
If a later Owner-GO authorizes byte-identical reconstruction, that step
must use an explicitly authorized target-byte identity copy for the 4856
carrier lines and must prove:
  carrier_n remains 4856
  parent_span_493 remain accounted in LINE_ENTRIES not as synthesized carriers
  no glyph invention
  SHA256 of reconstructed target equals
    08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092
This contract does not authorize that step.
```

------------------------------------------------------------------------

## 14. Unresolved / H91 separation

```text
CLASS=OPEN_UNRESOLVED
UNRESOLVED_RECORD_COUNT=19
KR11_UNRESOLVED=14
TR005_UNRESOLVED=5
ALL_UNRESOLVED_RECORD_TYPE=AddressableStatement
ALL_UNRESOLVED_authority_status=NONE
ALL_UNRESOLVED_adjudication_status=null
ALL_UNRESOLVED_epistemic_status=null
ALL_UNRESOLVED_currentness=null
KR11_representation_form_string_NULL=14
KR11_raw_key_string_NULL=14
KR11_raw_value_string_NULL=14
KR11_heading_level=1
KR11_notes='KR-11 leftover ATX-H1 existing occupancy only'
TR005_raw_key_JSON_null=5
TR005_raw_value_JSON_null=5
TR005_notes_A23_leftover_fence_marker=5
```

KR-11 seq (OPEN_UNRESOLVED, identity only): 4158, 4159, 4319, 4320, 4321, 4323, 4371, 4384, 5020, 5060, 5061, 5886, 6960, 7026.

TR-005 seq (OPEN_UNRESOLVED, identity only): 23067, 23141, 23736, 23737, 23738.

```text
CLASS=INHERITED_ADJUDICATED_FACT
PREVIEW_ENVELOPE.H91_ACCOUNTING="14/14"
PREVIEW_ENVELOPE.STEP8_ADJUDICATED_H91_STATUS="CLOSED"
PREVIEW_ENVELOPE.STEP8_ADJUDICATED_H91_STATUS_EPISTEMIC_CLASS=
  ALREADY_ADJUDICATED_CONCLUSION_INHERITED_NOT_REOPENED
PREVIEW_ENVELOPE.H91_ENVELOPE_AND_KR11_RECORD_UNRESOLVED_ARE_NOT_FUSED=true
H91 string does not occur inside the 14 KR-11 record values.
```

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT unresolved_n==19
ASSERT kr11_unresolved_n==14
ASSERT tr005_unresolved_n==5
ASSERT KR11_class and TR005_class remain unfused
ASSERT envelope H91 CLOSED is NOT copied into KR-11 records
ASSERT unresolved_status remains UNRESOLVED
ASSERT classification remains UNRESOLVED on those 19
ASSERT KR11 string "NULL" vs TR005 JSON null preserved
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_UNRESOLVED_CLOSEOUT
FORBID_H91_KR11_FUSION
FORBID_RECLASSIFYING_KR11_TO_NESTEDSTRUCTURALCHILD_OR_PAU
FORBID_RECLASSIFYING_TR005_TO_MARKED_OR_NESTED_CHILD
FORBID_USING_ENVELOPE_H91_AS_RECORD_LEVEL_ADJUDICATION
```

```text
CLASS=OPEN_UNRESOLVED
The 19 records remain unresolved after STEP 15.
This contract does not adjudicate their future type, occupancy, or closeout.
```

------------------------------------------------------------------------

## 15. Literal-type preservation

```text
CLASS=OBSERVED_BASELINE_FACT
JSON_null != string_"NULL" != empty_string != false != 0
raw_key: JSON_null=11006, str=12941, string_NULL=14
raw_value: JSON_null=11006, str=12937, string_NULL=18
representation_form: JSON_null=23130, str=817, string_NULL=14
notes: JSON_null=0, empty_string=23841, nonempty_str=120
creates_new_parent: JSON false on all 23961, never 0, never "false"
```

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT type_and_literal_identity preserved for every catalog/line/carrier field
ASSERT KR11 "NULL" strings remain strings
ASSERT TR005 raw_key/raw_value remain JSON null
ASSERT notes empty string is not coerced to null
ASSERT false is not coerced to 0 or "false"
ASSERT integers remain integers
ASSERT no float coercion
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_NULL_NULLSTRING_EMPTY_FALSE_ZERO_NORMALIZATION
FORBID_STRING_NUMBER_COERCION
FORBID_UNICODE_NFC_NFKC
FORBID_STRIP_REFLOW
```

------------------------------------------------------------------------

## 16. Epistemic fields

```text
CLASS=OBSERVED_BASELINE_FACT
epistemic_status_all_null=23961
currentness_all_null=23961
adjudication_status_all_null=23961
provenance_form_all_null=23961
authority_status_all_NONE=23961
navigation_status_NAVIGATION_LITERAL_AS_STORED=76
navigation_status_null=23885
```

Die Acht-Klassen-Trennung (kanonische Authority; forensische Rohdaten; bereits adjudizierte Schlüsse; historische Zwischenstände; Navigation; Interpretation; Hypothesen; offen/widersprüchlich) ist **nicht** als befülltes First-Class-Catalog-Dimensionssystem vorhanden. Vorhanden sind Proxies (Envelope, `authority_status=NONE`, 76 Navigation-Literale, 19 Unresolved). Das Befüllen der Null-Felder aus Proxies wäre Invention.

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT epistemic_status remains JSON null where stored null
ASSERT currentness remains JSON null where stored null
ASSERT adjudication_status remains JSON null where stored null
ASSERT provenance_form remains JSON null where stored null
ASSERT NOT derive those fields from notes, record_type, chronology, heading, or plausibility
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_EPISTEMIC_RECLASSIFICATION_INTO_NULL_FIELDS
FORBID_CURRENTNESS_PROMOTION
FORBID_INTERPRETATION_WRITTEN_AS_STORED_STATUS
FORBID_HYPOTHESIS_WRITTEN_AS_FACT
```

------------------------------------------------------------------------

## 17. Navigation

```text
CLASS=OBSERVED_BASELINE_FACT
NAVIGATION_LITERAL_COUNT=76
record_type=AddressableStatement
transform_rule=TR-010
navigation_status=NAVIGATION_LITERAL_AS_STORED
authority_status=NONE
unresolved_status=null
```

```text
CLASS=TRANSFORMATION_INVARIANT
NAVIGATION_LITERAL_AS_STORED remains navigation.
Navigation does not create authority.
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_PROMOTING_NAVIGATION_TO_AUTHORITY
FORBID_DROPPING_NAVIGATION_STATUS
```

------------------------------------------------------------------------

## 18. Verbatim contract

```text
CLASS=OBSERVED_BASELINE_FACT
DeclaredVerbatimBody_n=2
  in_verbatim=false
  verbatim_claim_status=DECLARED
  verbatim_region_id prefix=declared:
MarkedVerbatimRegion_n=5
  in_verbatim=true
  verbatim_claim_status=MARKED
  verbatim_region_id prefix=verbatim:
PhysicalAppendUnit_in_verbatim_true=5
  verbatim_region_id=null on those 5 PAUs
in_verbatim_true_total=10
```

```text
CLASS=TRANSFORMATION_INVARIANT
ASSERT DECLARED != MARKED
ASSERT DeclaredVerbatimBody and MarkedVerbatimRegion remain unfused
ASSERT in_verbatim true/false not unified
ASSERT PAUs with in_verbatim=true and verbatim_region_id=null remain unrepaired
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_FUSING_DECLARED_AND_MARKED
FORBID_BACKFILLING_PAU_VERBATIM_REGION_ID
FORBID_FORCING_DECLARED_BODY_IN_VERBATIM_TRUE
```

------------------------------------------------------------------------

## 19. Round-trip / reconstruction

```text
CLASS=OBSERVED_BASELINE_FACT
Preview does not contain carrier source bytes/glyphs.
PREVIEW_ENVELOPE.TARGET_BYTE_READ_REQUIRED=false
PREVIEW_ENVELOPE.KR8_KR9_GLYPH_RENDERING=false
LINE nbytes sum equals historically bound target byte count 1421764
```

```text
CLASS=TRANSFORMATION_INVARIANT
Preview alone is insufficient for byte-identical reconstruction.
Absence of STEP9 chrome from the five preview root keys does not mean that
chrome is false or nonexistent; STEP9 remains independent provenance.
```

```text
CLASS=FORBIDDEN_OPERATION
FORBID_INVENTING_FULL_PAYLOAD_FROM_PREVIEW_ALONE
FORBID_MARKDOWN_REWRITE_AS_THIS_STEP
FORBID_LAYOUT_FAITHFUL_SOURCE_RECONSTRUCTION_UNDER_THIS_CONTRACT
FORBID_ATX_HEADING_CHROME_INJECTION
FORBID_CODE_FENCE_CHROME_INJECTION
FORBID_INVENTED_BEGIN_END_MARKERS
```

```text
CLASS=FUTURE_POSTCONDITION
A later authorized reconstruction, if any, must prove byte/text/line identity
against TARGET_SHA256=08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092
without collapsing the 19 unresolved, without fusing H91 into KR-11, and
without synthesizing carrier glyphs except by authorized identity copy.
This contract does not perform or authorize that proof.
```

------------------------------------------------------------------------

## 20. No invention

```text
CLASS=FORBIDDEN_OPERATION
FORBID_NEW_FACTS
FORBID_RECONSTRUCTING_MISSING_VALUES_FROM_PLAUSIBILITY
FORBID_HEURISTIC_CLASSIFICATION
FORBID_SILENT_REPAIR
FORBID_SEMANTIC_SMOOTHING
FORBID_UNICODE_NORMALIZATION
FORBID_STRIP_REFLOW
FORBID_SORT_KEYS_ON_STORED_OBJECTS
```

------------------------------------------------------------------------

## 21. Forbidden transformations (aggregate)

Jede spätere Transformation ohne neues, engeres Owner-GO ist unzulässig. Auch mit späterem GO bleiben ohne ausdrückliche Gegenerlaubnis verboten:

```text
CLASS=FORBIDDEN_OPERATION
occupancy concatenation
layout-faithful source reconstruction under this contract
ATX heading chrome injection
Markdown code-fence chrome as rewrite mechanism
--- chrome injection
invented BEGIN/END markers
Unicode NFC/NFKC
strip / reflow
sort_keys of stored catalog/line/carrier objects
NaN / Infinity
wall-clock fields added into stored records
STEP_10 progression
canonicalization
target replacement
authority promotion
currentness promotion
H91/KR-11 fusion
carrier payload synthesis
STEP8 candidate impersonation
mutation of target, STEP9, preview, master runbook, map of truth, or repository
seq-sort as physical order
deduplication
instantiation of absent types
38th entity
epistemic null-field fill
unresolved closeout
```

------------------------------------------------------------------------

## 22. Preconditions for a later transformation

Eine spätere Transformation darf nur beginnen, wenn **alle** folgenden Bedingungen wahr sind. Dieses Artefakt setzt keine davon auf true außer den bereits beobachteten Bindings.

```text
CLASS=TRANSFORMATION_INVARIANT
PRECONDITION_SEPARATE_OWNER_GO_FOR_THE_EXACT_TRANSFORMATION_STEP=required
PRECONDITION_THIS_CONTRACT_UNCHANGED_OR_EXPLICITLY_SUPERSEDED_BY_NEW_GO=required
PRECONDITION_TARGET_SHA256_STILL=08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092
PRECONDITION_STEP9_SHA256_STILL=53a0f29f480cf46bdb9c0a9cf25a15dd701fe9ecbe99e53f1f1822058d4fbdd8
PRECONDITION_PREVIEW_SHA256_STILL=ba1a7d843826b8c008003b46fc48e8aac390ba23e241bd18291db6ed56db40da
PRECONDITION_MASTER_RUNBOOK_SHA256_STILL=65f833565d64517eae496e4cb3289525573dd2d3387429ba8d4ddc189c5b8b98
PRECONDITION_MAP_OF_TRUTH_SHA256_STILL=97f8d389fa93d36c09e53c65db21242a6c7f777d6f8d01531e73f6815074ee9d
PRECONDITION_ORIGIN_MAIN_STILL=652c2cd4f9e91160a46b86f02014fd019ec33ca5
PRECONDITION_FIVE_LAYERS_INTACT=required
PRECONDITION_UNRESOLVED_19_STILL_UNRESOLVED=required
PRECONDITION_H91_NOT_FUSED_INTO_KR11=required
PRECONDITION_CARRIER_STILL_INDEX_ONLY=required
PRECONDITION_NO_AUTHORITY_PROMOTION=required
PRECONDITION_TARGET_BYTE_READ_ONLY_IF_THAT_LATER_GO_EXPLICITLY_ALLOWS_IT=required
PRECONDITION_STEP_10_REMAINS_FALSE_UNLESS_SEPARATELY_AUTHORIZED=required
```

Fehlt eine Precondition: HARD STOP. Kein stilles Angleichen.

------------------------------------------------------------------------

## 23. Future postconditions a later transformation would have to prove

```text
CLASS=FUTURE_POSTCONDITION
NOT claimed as current fact.

If a later transformation is authorized, it MUST prove at least:
  TARGET_AUTHORITY remains NONE unless a later GO explicitly changes that
  PREVIEW_AUTHORITY remains NONE
  MASTER_RUNBOOK_REMAINS_SOLE_SSOT=true
  CATALOG_RECORD_COUNT=23961 or an explicitly authorized successor count
    that accounts 1:1 for every prior record without silent drop
  LINE_ENTRIES_COUNT=30870 with line 1..30870 identity preserved
  CARRIER_COUNT=4856 still not a record type
  PARENT_SPAN_493 still separated from carrier 4856
  UNRESOLVED_RECORD_COUNT=19 still UNRESOLVED
  KR11=14 and TR005=5 still distinct
  H91 envelope not copied into KR-11
  null/"NULL"/"" /false/0 distinction preserved
  epistemic_status/currentness/adjudication_status/provenance_form still
    null where previously null
  Declared vs Marked verbatim unfused
  ShaNamedValue still 405 records
  physical array order not seq-sorted
  overlapping occupancy not collapsed
  duplicate raw_text groups not collapsed
  pau.raw_text still JSON null
  in_fence=true AND fence_id=null (n=6) unrepaired
  no 38th record type
  if reconstruction claimed: TARGET_SHA256 unchanged
    08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092
```

------------------------------------------------------------------------

## 24. Hard-stop conditions

```text
CLASS=TRANSFORMATION_INVARIANT
HARD_STOP if any source binding SHA drifted
HARD_STOP if destination collision on a later write without GO
HARD_STOP if unresolved_n != 19
HARD_STOP if H91 fused into KR-11
HARD_STOP if carrier gains record_type or payload
HARD_STOP if 38th entity appears
HARD_STOP if seq-sort is used as physical order
HARD_STOP if occupancy collapsed
HARD_STOP if line entries dropped
HARD_STOP if epistemic null fields filled
HARD_STOP if target mutated without exact GO
HARD_STOP if canonicalization or authority promotion occurs
HARD_STOP if CURRENT_FORENSIC_TRUTH_SHA lag is "repaired" under this contract
HARD_STOP if this contract is treated as SSOT
```

------------------------------------------------------------------------

## 25. Non-goals

Dieses Artefakt ist nicht:

```text
CLASS=TRANSFORMATION_INVARIANT
NOT a transformation
NOT a transformed target
NOT a target replacement
NOT a canonical file
NOT a second SSOT
NOT an authority promotion
NOT an adjudication of the 19 unresolved records
NOT an epistemic reclassification artifact
NOT a reconstruction attempt
NOT STEP 10
NOT a license to read target glyphs
NOT a license to synthesize carrier payloads
NOT a license to instantiate absent types
NOT a repair of Master Runbook CURRENT_FORENSIC_TRUTH_SHA lag
NOT a Map of Truth semantic change
NOT a repository mutation
```

------------------------------------------------------------------------

## 26. Machine-checkable predicates for a later verifier

Diese Predicates sind **Anforderungen**, nicht gegenwärtig an einer Transformation bewiesene Resultate.

```text
CLASS=TRANSFORMATION_INVARIANT
P01: preview_root_keys == [PREVIEW_ENVELOPE, CLOSED_TYPE_ROSTER, CATALOG_RECORDS, LINE_ENTRIES, KR8_KR9_SOURCE_BYTE_CARRIER_INDEX]
P02: len(CLOSED_TYPE_ROSTER)==37 AND sum(INSTANCE_COUNT)==23961
P03: instantiated_types==11 AND absent_types==26 AND unknown_types==0
P04: len(CATALOG_RECORDS)==23961
P05: len(LINE_ENTRIES)==30870 AND lines==range(1,30871)
P06: len(KR8_KR9_SOURCE_BYTE_CARRIER_INDEX)==4856
P07: all(authority_status=="NONE" for catalog records)
P08: all(epistemic_status is JSON null)
P09: all(currentness is JSON null)
P10: all(adjudication_status is JSON null)
P11: all(provenance_form is JSON null)
P12: count(navigation_status==NAVIGATION_LITERAL_AS_STORED)==76
P13: count(unresolved_status==UNRESOLVED)==19
P14: count(transform_rule==KR-11 AND unresolved_status==UNRESOLVED)==14
P15: count(transform_rule==TR-005 AND unresolved_status==UNRESOLVED)==5
P16: no carrier has key record_type
P17: no carrier has payload/glyph keys
P18: count(model_has_independent_bytes==false)==4856
P19: count(reason in {KR-8,KR-9} AND model_has_independent_bytes==true)==493
P20: all(PhysicalAppendUnit.raw_text is JSON null)
P21: count(PhysicalAppendUnit)==99 AND physical_order unique 1..99
P22: count(ShaNamedValue)==405
P23: count(DeclaredVerbatimBody)==2 AND claim==DECLARED AND in_verbatim==false
P24: count(MarkedVerbatimRegion)==5 AND claim==MARKED AND in_verbatim==true
P25: count(in_fence==true AND fence_id is JSON null)==6
P26: creates_new_parent is JSON false for all records
P27: catalog array is not a seq-sorted permutation used as physical order
P28: KR11 raw_key/raw_value/representation_form are string "NULL"
P29: TR005 raw_key/raw_value are JSON null
P30: notes empty string is not JSON null
P31: NO_38TH_ENTITY
P32: TARGET_AUTHORITY==NONE AND PREVIEW_AUTHORITY==NONE
```

------------------------------------------------------------------------

## 27. STEP 15 execution claims

```text
CLASS=OBSERVED_BASELINE_FACT
These claims apply to STEP 15 itself after this artifact exists:
TRANSFORMATION_EXECUTED=false
TARGET_MUTATED=false
CANONICALIZATION_EXECUTED=false
AUTHORITY_PROMOTION_EXECUTED=false
CARRIER_PAYLOAD_SYNTHESIZED=false
UNRESOLVED_CLOSEOUT_EXECUTED=false
H91_KR11_FUSION_EXECUTED=false
EPISTEMIC_RECLASSIFICATION_EXECUTED=false
STEP_10_STARTED=false
SPECIFICATION_ONLY=true
ARTIFACT_AUTHORITY=NONE
```

Ende des Vertrags.
