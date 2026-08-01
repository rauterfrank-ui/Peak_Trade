"""Constants for productive max-age research evidence accumulation v1."""

from __future__ import annotations

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_RESEARCH_"
    "EVIDENCE_ACCUMULATION_CAPABILITY_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_CAPABILITY_V1"
)
CAPABILITY_VERSION = "canonical_volatility_max_age_productive_research_evidence_accumulation/v1"
EVIDENCE_SCHEMA_VERSION = "canonical_volatility_max_age_productive_research_evidence_record/v1"
LEDGER_SCHEMA_VERSION = "canonical_volatility_max_age_productive_research_evidence_ledger/v1"
SESSION_CONTRACT_VERSION = "canonical_volatility_max_age_productive_research_evidence_session/v1"
COVERAGE_SCHEMA_VERSION = "canonical_volatility_max_age_productive_research_evidence_coverage/v1"

OWNER = "research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1"

# Hard safety — accumulation only; never trading / threshold authority.
NUMERIC_MAX_AGE_DECIDED = False
THRESHOLD_STATUS = "UNRESOLVED_MAX_AGE"
NUMERIC_THRESHOLD_SELECTED = False
PARAMETER_PROMOTED = False
ENFORCEMENT_APPLIED = False
ALPHA_MUTATION_OCCURRED = False
PRODUCTIVE_POLICY_MUTATION_OCCURRED = False
CONFIG_MUTATION_OCCURRED = False
PRODUCTIVE_TRADING_BEHAVIOR_CHANGED = False
LIVE_TESTNET_ORDER_ACTIVATION_OCCURRED = False
ORDER_AUTHORITY_INTRODUCED = False
REGIME_LABEL_MUTATES_ALPHA = False
REGIME_LABEL_MUTATES_POLICY = False
REGIME_LABEL_MUTATES_POSITION = False
REGIME_LABEL_IS_RESEARCH_METADATA_ONLY = True
LIVE_AUTHORIZATION = False
HARD_STOP = True
READY_FOR_THRESHOLD_SELECTION = False
READY_FOR_PARAMETER_PROMOTION = False
READY_FOR_ENFORCEMENT = False

AGE_REFERENCE_CLOCK = "MARKET_EVENT_TIME"
AGE_FORMULA_VERSION = "reference_market_event_time_minus_volatility_as_of_event_time/v1"

EVIDENCE_WRITE_FAILURE_BEHAVIOR = (
    "DIAGNOSTIC_ONLY_NO_TRADING_MUTATION;"
    "NO_SILENT_FALSE_RESEARCH_RECORD;"
    "QUARANTINE_OR_SKIP;"
    "NEVER_ALTER_ALPHA_POSITION_RISK_SAFETY_OR_TRADING_GATE"
)

DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "productive_research_evidence_ledger.jsonl"
)
DEFAULT_JOIN_LEDGER_RELATIVE_PATH = (
    "docs/evidence/canonical_volatility_numeric_max_age_research_evidence_ledger_v1/"
    "research_evidence_ledger.jsonl"
)
DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "productive_research_evidence_quarantine.jsonl"
)

KNOWN_VOLATILITY_UNITS = frozenset(
    {
        "DECIMAL_FRACTION",
        "PERCENT",
        "ANNUALIZED_DECIMAL",
        "ANNUALIZED_PERCENT",
        "UNKNOWN",
    }
)

FORBIDDEN_IMPORT_SUBSTRINGS: tuple[str, ...] = (
    "trading.execution",
    "src.execution",
    "trading.live",
    "src.live",
    "exchange_order",
    "place_order",
    "submit_order",
    "broker_adapter",
)

CLI_REL_PATH = (
    "scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py"
)
SPEC_REL_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_RESEARCH_"
    "EVIDENCE_ACCUMULATION_CAPABILITY_V1.md"
)

AUTHORITY_SCOPE = "PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_ONLY"
NON_AUTHORITY_SCOPE = (
    "NOT_THRESHOLD_SELECTION;"
    "NOT_CANDIDATE_PROMOTION;"
    "NOT_POLICY_MUTATION;"
    "NOT_ALPHA_MUTATION;"
    "NOT_ENFORCEMENT;"
    "NOT_ORDER_AUTHORITY;"
    "NOT_LIVE_AUTHORITY"
)
