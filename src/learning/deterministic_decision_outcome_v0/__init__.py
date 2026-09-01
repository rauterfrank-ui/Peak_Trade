"""Offline Decision-Outcome Learning contract and control plane v0.

AUTHORITY_CLASS=OFFLINE_OBSERVATION_ADAPTER_WITH_PRODUCTIVE_HOST_HOOK
RUNTIME_EFFECT=NONE
CAPTURE_RUNTIME_EFFECT=OBSERVATION_ONLY
PROMOTION_AUTHORITY_EFFECT=NONE
PROMOTION_AUTHORITY_ACTIVATION=false
LEARNING_PRODUCTIVE_AUTHORITY=NONE
AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY=false
AUTONOMY_SUPERVISOR_EXECUTION_AUTHORITY=false
"""

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_CLASS,
    AUTHORITY_OWNER,
    AUTONOMY_SUPERVISOR_EXECUTION_AUTHORITY,
    AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY,
    LEARNING_PRODUCTIVE_AUTHORITY,
    OUTCOME_ENGINE_PRESENT,
    PROMOTION_AUTHORITY_ACTIVATION,
    PROMOTION_AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    WORKPACKAGE_ID,
)
from src.learning.deterministic_decision_outcome_v0.challenger_v0 import compare_challenger_v0
from src.learning.deterministic_decision_outcome_v0.contract_registry_v0 import (
    CONTRACT_REGISTRY_V0,
    get_schema_contract_v0,
    hash_scope_fields_v0,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoDuplicateConflictError,
    DdoError,
    DdoIntegrityError,
    DdoLedgerCorruptionError,
    DdoLineageError,
    DdoMalformedRecordError,
    DdoUnsupportedSchemaVersionError,
    DdoValidationError,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    EVALUATION_ENGINE_ID,
    evaluate_offline_bundle_v0,
    persist_evaluation_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_records_v0 import (
    build_attribution_record_v0,
    build_counterfactual_record_v0,
    validate_attribution_record_v0,
    validate_counterfactual_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_v0 import (
    evaluate_attribution_v0,
    evaluate_counterfactual_v0,
    evaluate_outcome_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    build_incident_record_v0,
    validate_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    build_candidate_artifact_v0,
    build_learning_hypothesis_v0,
    build_validation_evidence_pack_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
    AppendResultV0,
    validate_canonical_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import (
    build_outcome_record_v0,
    validate_outcome_record_v0,
    validate_outcome_ref_v0,
)
from src.learning.deterministic_decision_outcome_v0.promotion_controller_v0 import (
    evaluate_promotion_eligibility_v0,
)
from src.learning.deterministic_decision_outcome_v0.promotion_records_v0 import (
    build_deployment_record_v0,
    build_promotion_eligibility_record_v0,
    build_promotion_policy_v0,
    build_release_artifact_v0,
    build_rollback_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.registry_v0 import OfflineLearningRegistryV0
from src.learning.deterministic_decision_outcome_v0.replay_evaluator_v0 import (
    classify_decision_event_v0,
    classify_incident_record_v0,
    replay_ledger_record_v0,
    replay_same_incident_inputs_same_classification_v0,
    replay_same_inputs_same_classification_v0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    canonical_json_dumps_v0,
    compute_content_hash_v0,
)
from src.learning.deterministic_decision_outcome_v0.supervisor_records_v0 import (
    build_autonomy_cycle_record_v0,
    build_health_snapshot_v0,
)
from src.learning.deterministic_decision_outcome_v0.supervisor_v0 import (
    DeterministicAutonomySupervisorV0,
)

__all__ = [
    "AUTHORITY_CLASS",
    "AUTHORITY_OWNER",
    "AUTONOMY_SUPERVISOR_EXECUTION_AUTHORITY",
    "AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY",
    "AppendOnlyDdoLedgerV0",
    "AppendResultV0",
    "CONTRACT_REGISTRY_V0",
    "DeterministicAutonomySupervisorV0",
    "DdoDuplicateConflictError",
    "DdoError",
    "DdoIntegrityError",
    "DdoLedgerCorruptionError",
    "DdoLineageError",
    "DdoMalformedRecordError",
    "DdoUnsupportedSchemaVersionError",
    "DdoValidationError",
    "EVALUATION_ENGINE_ID",
    "LEARNING_PRODUCTIVE_AUTHORITY",
    "OUTCOME_ENGINE_PRESENT",
    "OfflineLearningRegistryV0",
    "PROMOTION_AUTHORITY_ACTIVATION",
    "PROMOTION_AUTHORITY_EFFECT",
    "RUNTIME_EFFECT",
    "WORKPACKAGE_ID",
    "build_attribution_record_v0",
    "build_autonomy_cycle_record_v0",
    "build_candidate_artifact_v0",
    "build_counterfactual_record_v0",
    "build_decision_event_v0",
    "build_deployment_record_v0",
    "build_health_snapshot_v0",
    "build_incident_record_v0",
    "build_learning_hypothesis_v0",
    "build_outcome_record_v0",
    "build_promotion_eligibility_record_v0",
    "build_promotion_policy_v0",
    "build_release_artifact_v0",
    "build_rollback_record_v0",
    "build_validation_evidence_pack_v0",
    "canonical_json_dumps_v0",
    "classify_decision_event_v0",
    "classify_incident_record_v0",
    "compare_challenger_v0",
    "compute_content_hash_v0",
    "evaluate_attribution_v0",
    "evaluate_counterfactual_v0",
    "evaluate_offline_bundle_v0",
    "evaluate_outcome_record_v0",
    "evaluate_promotion_eligibility_v0",
    "get_schema_contract_v0",
    "hash_scope_fields_v0",
    "persist_evaluation_bundle_v0",
    "replay_ledger_record_v0",
    "replay_same_incident_inputs_same_classification_v0",
    "replay_same_inputs_same_classification_v0",
    "validate_attribution_record_v0",
    "validate_canonical_record_v0",
    "validate_counterfactual_record_v0",
    "validate_decision_event_v0",
    "validate_evaluation_observation_v0",
    "validate_incident_record_v0",
    "validate_outcome_record_v0",
    "validate_outcome_ref_v0",
]
