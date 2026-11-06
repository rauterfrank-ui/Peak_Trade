"""Closed enum domains for GVEF V1.5 contracts."""

from __future__ import annotations

from enum import Enum


class FanOutEvaluationClass(str, Enum):
    LOCAL_EVALUATION = "LOCAL_EVALUATION"
    DOWNSTREAM_IMPACT_EVALUATION = "DOWNSTREAM_IMPACT_EVALUATION"
    WHOLE_SYSTEM_REPROOF = "WHOLE_SYSTEM_REPROOF"


class DomainEvaluatorId(str, Enum):
    RANKING_UNIVERSE = "ranking_universe_evaluator_v1"
    PRODUCTIVE_TRADING_PATH = "productive_trading_path_evaluator_v1"
    SELF_LEARNING = "self_learning_evaluator_v1"
    OPTIMIZATION_UNIVERSE = "optimization_universe_evaluator_v1"
    MARKET_INTELLIGENCE = "market_intelligence_evaluator_v1"


class EvaluationDomain(str, Enum):
    RANKING_UNIVERSE = "ranking_universe"
    PRODUCTIVE_TRADING_PATH = "productive_trading_path"
    SELF_LEARNING = "self_learning"
    OPTIMIZATION_UNIVERSE = "optimization_universe"
    MARKET_INTELLIGENCE = "market_intelligence"


class DomainVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class VectorClass(str, Enum):
    """GHV vector taxonomy (V1.5 closed set)."""

    GOLDEN_HAPPY = "GoldenHappy"
    GOLDEN_NEUTRAL = "GoldenNeutral"
    GOLDEN_HOLD = "GoldenHold"
    GOLDEN_REJECT = "GoldenReject"
    GOLDEN_NATURAL_ENTER = "GoldenNaturalEnter"


class DigestVerdict(str, Enum):
    DIGEST_EQUAL = "DIGEST_EQUAL"
    DIGEST_CHANGED_EXPECTED = "DIGEST_CHANGED_EXPECTED"
    DIGEST_CHANGED_UNEXPECTED = "DIGEST_CHANGED_UNEXPECTED"
    DIGEST_UNAVAILABLE = "DIGEST_UNAVAILABLE"
    DIGEST_CONFLICTING = "DIGEST_CONFLICTING"


class ProtectedDomain(str, Enum):
    RANKING_UNIVERSE = "ranking_universe"
    SELECTION = "selection"
    MV2 = "mv2"
    DP = "dp"
    CONFIRMATION = "confirmation"
    SIDESTATE = "sidestate"
    ENTRY_EXIT = "entry_exit"
    SCOPE = "scope"
    CRS = "crs"
    SIZING = "sizing"
    ADMISSION = "admission"
    VENUE_PLAN = "venue_plan"


class CurrentReachabilityVerdict(str, Enum):
    PROVEN_CURRENT = "PROVEN_CURRENT"
    UNKNOWN_CURRENT = "UNKNOWN_CURRENT"
    CONFLICTING_CURRENT = "CONFLICTING_CURRENT"
    VIOLATED_CURRENT = "VIOLATED_CURRENT"


class PassRejectVerdict(str, Enum):
    PASS = "PASS"
    REJECT = "REJECT"


class FailureClassification(str, Enum):
    CONSTRAINT_FAILURE = "CONSTRAINT_FAILURE"
    AUTHORITY_FAILURE = "AUTHORITY_FAILURE"
    BOUNDARY_FAILURE = "BOUNDARY_FAILURE"
    CONTRACT_FAILURE = "CONTRACT_FAILURE"
    SCHEMA_FAILURE = "SCHEMA_FAILURE"
    CORPUS_DRIFT = "CORPUS_DRIFT"
    INVARIANT_FAILURE = "INVARIANT_FAILURE"
    EVALUATOR_FAILURE = "EVALUATOR_FAILURE"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    NON_DETERMINISM = "NON_DETERMINISM"
    PROTECTED_DIGEST_DRIFT = "PROTECTED_DIGEST_DRIFT"


class ExternalPromotionStatus(str, Enum):
    """External governance observation only — not a GVEF promotion decision."""

    EXTERNAL_UNSET = "EXTERNAL_UNSET"
    GOVERNANCE_REVIEW_PENDING = "GOVERNANCE_REVIEW_PENDING"
    GOVERNANCE_REVIEWED = "GOVERNANCE_REVIEWED"
    SHADOW_ELIGIBLE = "SHADOW_ELIGIBLE"
    TESTNET_ELIGIBLE = "TESTNET_ELIGIBLE"
    LIVE_ELIGIBLE = "LIVE_ELIGIBLE"


class EvidenceBundleLifecycleState(str, Enum):
    """Evidence bundle lifecycle (schema contract; registry not implemented in BWP-1)."""

    BUILT = "BUILT"
    VALIDATED = "VALIDATED"
    REGISTERED = "REGISTERED"


GVEF_CONTRACTS_PACKAGE_VERSION = "1.5.0"
