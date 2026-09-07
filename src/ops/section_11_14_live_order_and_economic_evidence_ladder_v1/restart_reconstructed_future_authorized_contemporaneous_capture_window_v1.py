"""Adjudicate the future-authorized contemporaneous capture window.

Does not join a productive runtime caller. Does not write a handoff.
Does not GET. Does not POST. Does not execute a restart. Does not
synthesize contemporaneous Live observation. Does not backfill timestamps.
Does not generalize the frozen historical bound identity.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    CREDENTIAL_USE_ALLOWED,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
    LIVE_FILL_OBSERVED_PRODUCER,
    LIVE_RESTART_RECONSTRUCTED,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TESTNET_FIXTURE_OR_SIMULATED_RESULT_MAY_SATISFY_A_LIVE_EVIDENCE_FIELD,
    NO_TIMESTAMP_BACKFILL,
    ORDER_SUBMIT_ALLOWED,
    POST_ALLOWED,
    PRIVATE_GET_ALLOWED,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_observation_v1 import (
    COMPLETE_CAPTURE_SEAM,
    inventory_durable_write_point_and_provenance_v1,
    inventory_productive_pre_restart_capture_trigger_and_producer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    WRITER_SEAM_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    bind_restart_reader_provenance_and_consumer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_TEMPORAL_MEANING,
    PRODUCER_ID,
    SELECTED_SEMANTIC_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    validate_temporal_order_v1,
)

PRODUCER_SYMBOL = "emit_s05_handoff_pos_v1"
WRITER_SYMBOL = "commit_handoff_after_bound_fill_before_restart_v1"
PRODUCER_RELPATH = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "restart_reconstructed_handoff_pos_producer_v1.py"
)
WRITER_RELPATH = (
    "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "restart_reconstructed_handoff_owner_and_writer_v1.py"
)
READER_SYMBOL = "read_validated_durable_pre_restart_handoff_v1"
CONSUMER_SYMBOL = "adjudicate_live_restart_reconstructed_v1::consume_validated_handoff_for_restart_reconstruction_v1"
BOUND_FILL_CANONICAL_SYMBOL = "LIVE_FILL_OBSERVED_IDENTITY_BOUND_VENUE_FILL"
BOUND_FILL_PROOF_PRODUCER = LIVE_FILL_OBSERVED_PRODUCER
PRODUCTIVE_CAPTURE_OWNER = "NONE"
PRODUCTIVE_CAPTURE_OWNER_STATUS = "ABSENT"
PRODUCTIVE_CAPTURE_HOOK = "NONE"
PRODUCTIVE_CAPTURE_HOOK_STATUS = "ABSENT"
CAPTURE_WINDOW_ORDERING = "UNPROVEN"
MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE = "UNPROVEN"
PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE = False
PRODUCTIVE_BINDING_IMPLEMENTED = False
CASE_ADJUDICATION = (
    "CASE_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_CLOSED_"
    "PRODUCTIVE_BINDING_UNPROVEN_NO_RUNTIME_OWNER_OR_HOOK"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_HOOK_AND_FUTURE_IDENTITY_CONTRACT_V1"
)
REQUIRED_NEXT_AUTHORITY = (
    "OWNER_GO_FOR_PRODUCTIVE_CAPTURE_OWNER_HOOK_AND_FUTURE_IDENTITY_CONTRACT_THEN_"
    "SEPARATE_OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED"
)
MISSING_PREDICATES: tuple[str, ...] = (
    "PRODUCTIVE_CAPTURE_OWNER_UNIQUE",
    "PRODUCTIVE_CAPTURE_HOOK_UNIQUE",
    "CAPTURE_WINDOW_TIMESTAMP_ORDERING",
    "FUTURE_BOUND_IDENTITY_PARAMETERIZATION",
    "PRODUCTIVE_S05_QTY_SOURCE",
    "FUTURE_LIVE_CAPTURE_AUTHORIZATION",
    "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL",
)
_PRODUCTIVE_PREFIXES: tuple[str, ...] = (
    "src/execution/",
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/",
    "src/ops/canonical_local_launcher_and_process_supervision_v1/",
    "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/",
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/",
    "src/learning/",
    "src/risk_layer/",
    "src/governance/",
)
_SCAN_ROOTS: tuple[str, ...] = ("src", "scripts")
_SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {".venv", "__pycache__", ".git", "tests", "evidence", "artifacts"}
)


def _rel(path: Path, *, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve())).replace("\\", "/")


def _is_call_name(node: ast.AST, symbol: str) -> bool:
    if isinstance(node, ast.Name):
        return node.id == symbol
    if isinstance(node, ast.Attribute):
        return node.attr == symbol
    return False


def _call_sites_in_source(*, source: str, symbol: str) -> list[dict[str, int]]:
    tree = ast.parse(source)
    sites: list[dict[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _is_call_name(node.func, symbol):
            sites.append(
                {"lineno": int(node.lineno), "end_lineno": int(node.end_lineno or node.lineno)}
            )
    return sites


def _iter_python_files(*, repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for root_name in _SCAN_ROOTS:
        root = repo_root / root_name
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if any(part in _SKIP_DIR_NAMES for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def census_symbol_call_graph_v1(
    *,
    repo_root: Path,
    symbol: str,
    definition_relpath: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in _iter_python_files(repo_root=repo_root):
        rel = _rel(path, repo_root=repo_root)
        text = path.read_text(encoding="utf-8")
        try:
            sites = _call_sites_in_source(source=text, symbol=symbol)
        except SyntaxError as exc:
            raise Section1114OfflineSurfaceError("CALL_GRAPH_PARSE_FAILURE") from exc
        if not sites:
            continue
        if rel == definition_relpath:
            def_sites = [
                site
                for site in sites
                if f"def {symbol}(" not in text.splitlines()[site["lineno"] - 1]
            ]
            sites = def_sites
            if not sites:
                continue
        productive = any(rel.startswith(prefix) for prefix in _PRODUCTIVE_PREFIXES)
        test_only = rel.startswith("tests/")
        forensic = rel.startswith(
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
        ) or rel.startswith("scripts/ops/run_section_11_14_")
        classification = (
            "TEST_ONLY"
            if test_only
            else (
                "PRODUCTIVE_RUNTIME"
                if productive
                else ("FORENSIC_OFFLINE" if forensic else "NON_PRODUCTIVE_OTHER")
            )
        )
        for site in sites:
            rows.append(
                {
                    "NODE_ID": f"{symbol}@{rel}:{site['lineno']}",
                    "SYMBOL": symbol,
                    "FILE": rel,
                    "LINE_RANGE": f"{site['lineno']}-{site['end_lineno']}",
                    "PRODUCTIVE_OR_TEST_ONLY": classification,
                    "BOUND_OR_UNBOUND": "UNBOUND_FROM_PRODUCTIVE_ENTRYPOINT",
                    "REACHABLE_FROM_PRODUCTIVE_ENTRYPOINT": False,
                    "REQUIRES_LIVE_SURFACE": False,
                    "REQUIRES_WIRE_SEND": False,
                    "REQUIRES_VENUE_RESPONSE": False,
                    "REQUIRES_CREDENTIALS": False,
                    "FAIL_OPEN_OR_FAIL_CLOSED": "FAIL_CLOSED",
                    "AUTHORITY_CLASS": "FORENSIC_RAW_EVIDENCE",
                }
            )
    productive_count = sum(
        1 for row in rows if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    )
    test_count = sum(1 for row in rows if row["PRODUCTIVE_OR_TEST_ONLY"] == "TEST_ONLY")
    return {
        "SYMBOL": symbol,
        "DEFINITION": definition_relpath,
        "CALL_SITE_COUNT": len(rows),
        "PRODUCTIVE_RUNTIME_CALLER_COUNT": productive_count,
        "TEST_ONLY_CALL_SITE_COUNT": test_count,
        "rows": rows,
    }


def census_productive_runtime_graph_v1(*, repo_root: Path) -> dict[str, Any]:
    producer = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=PRODUCER_SYMBOL,
        definition_relpath=PRODUCER_RELPATH,
    )
    writer = census_symbol_call_graph_v1(
        repo_root=repo_root,
        symbol=WRITER_SYMBOL,
        definition_relpath=WRITER_RELPATH,
    )
    internal_producer_callers = [row for row in producer["rows"] if row["FILE"] == WRITER_RELPATH]
    # Historical future-window slice required zero productive callers. The
    # successor CREATE slice may lawfully add exactly one productive writer
    # caller. This census reports current counts and does not freeze them.
    if not internal_producer_callers:
        raise Section1114OfflineSurfaceError("WRITER_MUST_CALL_PRODUCER")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_FUTURE_CAPTURE_WINDOW_RUNTIME_GRAPH_CENSUS_V1",
        "REQUIRED_EVENT_CHAIN": (
            "REAL_BOUND_FILL",
            "PRODUCTIVE_STATE_TRANSITION",
            "CAPTURE_WINDOW_OPEN",
            "HANDOFF_PRODUCER",
            "DURABLE_WRITER",
            "DURABLE_RECORD_COMMITTED",
            "RESTART_BOUNDARY",
            "READER",
            "VALIDATION",
            "RESTART_CONSUMER",
            "LIVE_RESTART_RECONSTRUCTED_ADJUDICATION",
        ),
        "PRODUCER_ID": PRODUCER_ID,
        "PRODUCER_SYMBOL": PRODUCER_SYMBOL,
        "WRITER_SYMBOL": WRITER_SYMBOL,
        "READER_SYMBOL": READER_SYMBOL,
        "CONSUMER_SYMBOL": CONSUMER_SYMBOL,
        "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_emit_s05_handoff_pos_v1": (
            producer["PRODUCTIVE_RUNTIME_CALLER_COUNT"]
        ),
        "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_commit_handoff_after_bound_fill_before_restart_v1": (
            writer["PRODUCTIVE_RUNTIME_CALLER_COUNT"]
        ),
        "INTERNAL_WRITER_TO_PRODUCER_CALL_PRESENT": True,
        "INTERNAL_WRITER_TO_PRODUCER_IS_NOT_PRODUCTIVE_RUNTIME_JOIN": True,
        "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME": False,
        "PRODUCTIVE_S05_QTY_SOURCE_STATUS": "ABSENT",
        "producer_census": producer,
        "writer_census": writer,
    }


def bind_bound_fill_semantics_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_BOUND_FILL_SEMANTICS_V1",
        "AUTHORITY_CLASS": "CANONICAL_AUTHORITY",
        "BOUND_FILL_CANONICAL_SYMBOL": BOUND_FILL_CANONICAL_SYMBOL,
        "BOUND_FILL_PRODUCER": BOUND_FILL_PROOF_PRODUCER,
        "BOUND_FILL_INPUT": (
            "GOVERNED_CURRENT_PRIVATE_GET /api/v5/trade/fills scoped to the "
            "acknowledged Live submit identity"
        ),
        "BOUND_FILL_IDENTITY": {
            "ordId": BOUND_ORDID,
            "clOrdId": BOUND_CLORDID,
            "instId": BOUND_INSTID,
            "posSide": BOUND_POS_SIDE,
            "fillSz": BOUND_FILL_SZ,
        },
        "BOUND_FILL_TIMESTAMP": "UNPROVEN",
        "BOUND_FILL_POSITION_STATE": "NOT_S05_POS; fillSz is not handoff pos",
        "BOUND_FILL_INSTRUMENT_ID": BOUND_INSTID,
        "BOUND_FILL_POS_SIDE": BOUND_POS_SIDE,
        "BOUND_FILL_S05_RELATION": (
            "S05 pos must Decimal-equal bound fillSz and must not copy fillSz, "
            "venue GET pos, submitted sz, or accounting"
        ),
        "BOUND_FILL_ATTEMPT_IDENTITY": "REQUIRED_ON_HANDOFF_RECORD_NOT_ON_FILL_ROW",
        "BOUND_FILL_IS_PRODUCTIVE_RUNTIME_EVENT": True,
        "BOUND_FILL_IS_CURRENT_RUNTIME_EVENT": False,
        "BOUND_FILL_IS_HISTORICAL_CANARY_IDENTITY": True,
        "BOUND_FILL_REQUIRES_VENUE_ACK": True,
        "BOUND_FILL_REQUIRES_WIRE_SEND": True,
        "BOUND_FILL_CAN_EXIST_OFFLINE": False,
        "BOUND_FILL_CAN_EXIST_IN_SHADOW": False,
        "BOUND_FILL_CAN_EXIST_IN_TESTNET": False,
        "BOUND_FILL_CAN_EXIST_WITHOUT_ORDER_SUBMIT": False,
        "ORDER_INTENT_IS_NOT_BOUND_FILL": True,
        "ORDER_PLAN_IS_NOT_BOUND_FILL": True,
        "SUBMIT_INTENT_IS_NOT_BOUND_FILL": True,
        "WIRE_SEND_IS_NOT_BOUND_FILL": True,
        "VENUE_ACK_IS_NOT_BOUND_FILL": True,
        "FILL_SZ_IS_NOT_S05": True,
        "SYNTHETIC_FILL_IS_NOT_BOUND_FILL": True,
        "SIMULATED_FILL_IS_NOT_BOUND_FILL": True,
        "POSITION_OBSERVATION_IS_NOT_BOUND_FILL": True,
        "LIVE_FILL_OBSERVED_CANONICAL_DEFINITION": LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
        "NO_TESTNET_FIXTURE_OR_SIMULATED_RESULT_MAY_SATISFY_A_LIVE_EVIDENCE_FIELD": (
            NO_TESTNET_FIXTURE_OR_SIMULATED_RESULT_MAY_SATISFY_A_LIVE_EVIDENCE_FIELD
        ),
        "HANDOFF_PRODUCER_IDENTITY_IS_FROZEN_TO_HISTORICAL_CANARY": True,
        "FUTURE_FILL_WITH_NEW_ORDID_IS_IDENTITY_MISMATCH_UNDER_CURRENT_PRODUCER": True,
    }


def bind_capture_window_semantics_v1() -> dict[str, Any]:
    temporal = validate_temporal_order_v1(handoff={}, restart_at_utc=None)
    if temporal["TEMPORAL_OK"] is not True:
        raise Section1114OfflineSurfaceError("EMPTY_HANDOFF_TEMPORAL_MUST_NOT_INVERT")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_WINDOW_SEMANTICS_V1",
        "AUTHORITY_CLASS": "CANONICAL_AUTHORITY",
        "WINDOW_OPEN_CONDITION": (
            "bound fill identity exists AND Peak_Trade-owned S05 resulting "
            "current position qty is available AND restart has not occurred"
        ),
        "WINDOW_CLOSE_CONDITION": (
            "durable success acknowledgement completed OR restart boundary reached"
        ),
        "REQUIRED_ORDERING_TEXT": (
            "mutation-critical venue effect THEN bound fill identity exists "
            "THEN Peak_Trade-owned S05 resulting current position qty available "
            "THEN handoff record construction THEN durable write THEN durability "
            "success acknowledgement THEN process/host restart may occur"
        ),
        "POS_TEMPORAL_MEANING": POS_TEMPORAL_MEANING,
        "CAPTURE_WINDOW_ORDERING": CAPTURE_WINDOW_ORDERING,
        "BOUND_FILL_TIMESTAMP_LT_CAPTURE_LE_WRITE_LT_RESTART": "UNPROVEN",
        "WRITER_ASSIGNS_WRITTEN_AT_EQUAL_TO_CAPTURED_AT": True,
        "TEMPORAL_VALIDATOR_CHECKS_CAPTURED_LT_RESTART_ONLY_IF_RESTART_PRESENT": True,
        "NO_BOUND_FILL_TIMESTAMP_FIELD_ON_HANDOFF_RECORD": True,
        "REQUIRED_IDENTITY_BINDING": "FROZEN_HISTORICAL_CANARY_CLORDID_ORDID_INSTID_POSSIDE",
        "REQUIRED_PROCESS_IDENTITY": "UNPROVEN",
        "REQUIRED_ATTEMPT_IDENTITY": "REQUIRED_NONEMPTY_STRING_NO_PROCESS_BIND",
        "REQUIRED_PRODUCER_TIMESTAMP": "captured_at_utc required; not compared to fill time",
        "REQUIRED_WRITER_TIMESTAMP": "written_at_utc assigned equal to captured_at_utc",
        "REQUIRED_RESTART_IDENTITY": "UNPROVEN",
        "REQUIRED_FRESHNESS_SEMANTICS": "PARTIAL",
        "WINDOW_OWNER": "ABSENT_NO_PRODUCTIVE_RUNTIME_OWNER",
        "WHO_MAY_CALL_WRITER": "NO_PRODUCTIVE_RUNTIME_CALLER",
        "EXACTLY_ONE_WRITE": "IDEMPOTENT_SAME_RECORD_ALLOWED_SECOND_IDENTITY_FORBIDDEN",
        "RECORD_REUSE_PREVENTION": "NO_SECOND_IDENTITY and IDEMPOTENT_REJECT_DIFFERENT_RECORD",
        "STALE_RECORD_DETECTION": "IDENTITY_OR_ATTEMPT_MISMATCH_OR_OPTIONAL_RESTART_INVERSION",
        "PRIOR_ATTEMPT_EXCLUSION": "attempt_identity mismatch rejects as STALE_HANDOFF at reader",
        "CAPTURE_BOUND_TO_SAME_FILL": "FROZEN_HISTORICAL_IDENTITY_ONLY",
        "CAPTURE_BOUND_TO_SAME_PROCESS": "UNPROVEN",
        "WHAT_PREVENTS_BACKFILL": "POLICY_NO_TIMESTAMP_BACKFILL_NOT_FILL_TIMESTAMP_COMPARISON",
        "WHAT_PREVENTS_POST_RESTART_SYNTHESIS": "restart_already_occurred flag caller-supplied",
        "WHAT_PREVENTS_CAPTURE_WITHOUT_FILL": "bound_fill_identity_exists caller-supplied boolean",
        "CALLER_SUPPLIED_GUARDS_ARE_NOT_PRODUCTIVE_RUNTIME_PROOF": True,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "REQUIRED_PROVENANCE_CLASS": CONTEMPORANEOUS_PROVENANCE_CLASS,
    }


def bind_authorization_surface_matrix_v1() -> dict[str, Any]:
    rows = (
        {
            "SURFACE": "OFFLINE",
            "EXISTS": True,
            "CAN_PRODUCE_CANONICAL_BOUND_FILL": False,
            "CAN_OPEN_CANONICAL_CAPTURE_WINDOW": False,
            "CAN_CALL_PRODUCTIVE_PRODUCER": False,
            "CAN_CALL_DURABLE_WRITER": False,
            "CAN_PRESERVE_CONTEMPORANEOUS_PROVENANCE": False,
            "REQUIRES_WIRE_SEND": False,
            "REQUIRES_ORDER_SUBMIT": False,
            "REQUIRES_VENUE_MUTATION": False,
            "REQUIRES_CREDENTIALS": False,
            "CURRENTLY_AUTHORIZED": True,
            "SUFFICIENT_FOR_SECTION_11_14_PROOF": False,
        },
        {
            "SURFACE": "REPLAY",
            "EXISTS": True,
            "CAN_PRODUCE_CANONICAL_BOUND_FILL": False,
            "CAN_OPEN_CANONICAL_CAPTURE_WINDOW": False,
            "CAN_CALL_PRODUCTIVE_PRODUCER": False,
            "CAN_CALL_DURABLE_WRITER": False,
            "CAN_PRESERVE_CONTEMPORANEOUS_PROVENANCE": False,
            "REQUIRES_WIRE_SEND": False,
            "REQUIRES_ORDER_SUBMIT": False,
            "REQUIRES_VENUE_MUTATION": False,
            "REQUIRES_CREDENTIALS": False,
            "CURRENTLY_AUTHORIZED": False,
            "SUFFICIENT_FOR_SECTION_11_14_PROOF": False,
        },
        {
            "SURFACE": "SHADOW",
            "EXISTS": True,
            "CAN_PRODUCE_CANONICAL_BOUND_FILL": False,
            "CAN_OPEN_CANONICAL_CAPTURE_WINDOW": False,
            "CAN_CALL_PRODUCTIVE_PRODUCER": False,
            "CAN_CALL_DURABLE_WRITER": False,
            "CAN_PRESERVE_CONTEMPORANEOUS_PROVENANCE": False,
            "REQUIRES_WIRE_SEND": False,
            "REQUIRES_ORDER_SUBMIT": False,
            "REQUIRES_VENUE_MUTATION": False,
            "REQUIRES_CREDENTIALS": False,
            "CURRENTLY_AUTHORIZED": False,
            "SUFFICIENT_FOR_SECTION_11_14_PROOF": False,
        },
        {
            "SURFACE": "SIMULATED_EXECUTION",
            "EXISTS": True,
            "CAN_PRODUCE_CANONICAL_BOUND_FILL": False,
            "CAN_OPEN_CANONICAL_CAPTURE_WINDOW": False,
            "CAN_CALL_PRODUCTIVE_PRODUCER": False,
            "CAN_CALL_DURABLE_WRITER": False,
            "CAN_PRESERVE_CONTEMPORANEOUS_PROVENANCE": False,
            "REQUIRES_WIRE_SEND": False,
            "REQUIRES_ORDER_SUBMIT": False,
            "REQUIRES_VENUE_MUTATION": False,
            "REQUIRES_CREDENTIALS": False,
            "CURRENTLY_AUTHORIZED": False,
            "SUFFICIENT_FOR_SECTION_11_14_PROOF": False,
        },
        {
            "SURFACE": "TESTNET",
            "EXISTS": True,
            "CAN_PRODUCE_CANONICAL_BOUND_FILL": False,
            "CAN_OPEN_CANONICAL_CAPTURE_WINDOW": False,
            "CAN_CALL_PRODUCTIVE_PRODUCER": False,
            "CAN_CALL_DURABLE_WRITER": False,
            "CAN_PRESERVE_CONTEMPORANEOUS_PROVENANCE": False,
            "REQUIRES_WIRE_SEND": True,
            "REQUIRES_ORDER_SUBMIT": True,
            "REQUIRES_VENUE_MUTATION": True,
            "REQUIRES_CREDENTIALS": True,
            "CURRENTLY_AUTHORIZED": False,
            "SUFFICIENT_FOR_SECTION_11_14_PROOF": False,
        },
        {
            "SURFACE": "LIVE_READ_ONLY",
            "EXISTS": True,
            "CAN_PRODUCE_CANONICAL_BOUND_FILL": False,
            "CAN_OPEN_CANONICAL_CAPTURE_WINDOW": False,
            "CAN_CALL_PRODUCTIVE_PRODUCER": False,
            "CAN_CALL_DURABLE_WRITER": False,
            "CAN_PRESERVE_CONTEMPORANEOUS_PROVENANCE": False,
            "REQUIRES_WIRE_SEND": False,
            "REQUIRES_ORDER_SUBMIT": False,
            "REQUIRES_VENUE_MUTATION": False,
            "REQUIRES_CREDENTIALS": True,
            "CURRENTLY_AUTHORIZED": False,
            "SUFFICIENT_FOR_SECTION_11_14_PROOF": False,
        },
        {
            "SURFACE": "LIVE_ORDER_CANARY",
            "EXISTS": True,
            "CAN_PRODUCE_CANONICAL_BOUND_FILL": True,
            "CAN_OPEN_CANONICAL_CAPTURE_WINDOW": False,
            "CAN_CALL_PRODUCTIVE_PRODUCER": False,
            "CAN_CALL_DURABLE_WRITER": False,
            "CAN_PRESERVE_CONTEMPORANEOUS_PROVENANCE": False,
            "REQUIRES_WIRE_SEND": True,
            "REQUIRES_ORDER_SUBMIT": True,
            "REQUIRES_VENUE_MUTATION": True,
            "REQUIRES_CREDENTIALS": True,
            "CURRENTLY_AUTHORIZED": False,
            "SUFFICIENT_FOR_SECTION_11_14_PROOF": False,
        },
        {
            "SURFACE": "OTHER_EXISTING_RUNTIME_SURFACE",
            "EXISTS": True,
            "CAN_PRODUCE_CANONICAL_BOUND_FILL": False,
            "CAN_OPEN_CANONICAL_CAPTURE_WINDOW": False,
            "CAN_CALL_PRODUCTIVE_PRODUCER": False,
            "CAN_CALL_DURABLE_WRITER": False,
            "CAN_PRESERVE_CONTEMPORANEOUS_PROVENANCE": False,
            "REQUIRES_WIRE_SEND": False,
            "REQUIRES_ORDER_SUBMIT": False,
            "REQUIRES_VENUE_MUTATION": False,
            "REQUIRES_CREDENTIALS": False,
            "CURRENTLY_AUTHORIZED": False,
            "SUFFICIENT_FOR_SECTION_11_14_PROOF": False,
        },
    )
    sufficient = [row for row in rows if row["SUFFICIENT_FOR_SECTION_11_14_PROOF"] is True]
    if sufficient:
        raise Section1114OfflineSurfaceError("NO_SURFACE_MAY_BE_MARKED_SUFFICIENT")
    authorized_live = [
        row
        for row in rows
        if row["SURFACE"] == "LIVE_ORDER_CANARY" and row["CURRENTLY_AUTHORIZED"] is True
    ]
    if authorized_live:
        raise Section1114OfflineSurfaceError("LIVE_ORDER_CANARY_MUST_REMAIN_UNAUTHORIZED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_AUTHORIZATION_SURFACE_MATRIX_V1",
        "SUFFICIENT_SURFACE_COUNT": 0,
        "MINIMUM_SEMANTIC_CLASS_IF_LATER_AUTHORIZED": "LIVE_ORDER_CANARY",
        "MINIMUM_SEMANTIC_CLASS_IS_NOT_CURRENTLY_PROVEN_SURFACE": True,
        "rows": list(rows),
    }


def bind_minimum_future_capture_window_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_MINIMUM_FUTURE_CAPTURE_WINDOW_V1",
        "MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE": MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE,
        "MINIMUM_REQUIRED_RUNTIME": "LIVE_CANARY_AFTER_VENUE_FILL_BEFORE_RESTART",
        "MINIMUM_REQUIRED_OWNER_AUTHORITY": REQUIRED_NEXT_AUTHORITY,
        "MINIMUM_REQUIRED_PRECONDITIONS": list(MISSING_PREDICATES),
        "MINIMUM_REQUIRED_STATE": (
            "LIVE_ACCOUNTING_RECONSTRUCTED already true; open identity-bound "
            "position after a current Live bound fill; restart not yet occurred"
        ),
        "MINIMUM_REQUIRED_FILL_EVENT": "CURRENT_IDENTITY_BOUND_LIVE_VENUE_FILL",
        "MINIMUM_REQUIRED_CAPTURE_EVENT": (
            "REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART"
        ),
        "MINIMUM_REQUIRED_RESTART_EVENT": "PROCESS_OR_HOST_RESTART_AFTER_DURABLE_HANDOFF_COMMIT",
        "MINIMUM_REQUIRED_READBACK_EVENT": "read_validated_durable_pre_restart_handoff_v1",
        "LIVE_ENABLED_REQUIRED": True,
        "LIVE_ARMED_REQUIRED": True,
        "CANARY_AUTHORIZED_REQUIRED": True,
        "ORDER_SUBMIT_GO_REQUIRED": True,
        "WIRE_SEND_REQUIRED": True,
        "VENUE_FILL_REQUIRED": True,
        "PRIVATE_GET_REQUIRED": True,
        "NETWORK_AUTH_REQUIRED": True,
        "CREDENTIAL_ACCESS_REQUIRED": True,
        "CURRENT_LIVE_ENABLED": LIVE_ENABLED,
        "CURRENT_LIVE_ARMED": LIVE_ARMED,
        "CURRENT_CANARY_AUTHORIZED": CANARY_AUTHORIZED,
        "CURRENT_ORDER_SUBMIT_ALLOWED": ORDER_SUBMIT_ALLOWED,
        "CURRENT_POST_ALLOWED": POST_ALLOWED,
        "CURRENT_PRIVATE_GET_ALLOWED": PRIVATE_GET_ALLOWED,
        "CURRENT_CREDENTIAL_USE_ALLOWED": CREDENTIAL_USE_ALLOWED,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
        "HISTORICAL_CANARY_WINDOW_IS_CLOSED_REFUTED": True,
        "NEW_LIVE_FILL_REQUIRED_FOR_CONTEMPORANEOUS_CAPTURE": True,
        "CURRENT_PRODUCER_REJECTS_NEW_ORDID": True,
        "OPTION_A": (
            "Offline contract for unique capture owner, lifecycle hook, future "
            "identity parameterization, and timestamp ordering. No Live mutation."
        ),
        "OPTION_B": (
            "Fail-closed structural runtime join under a new gate default false. "
            "Rejected: owner and hook are ABSENT."
        ),
        "OPTION_C": (
            "Authorized Live canary submit/fill/capture/restart. Rejected here: "
            "this OWNER_GO does not authorize Live mutation, credentials, or restart."
        ),
        "SELECTED_NEXT_VARIANT": "OPTION_A",
        "SELECTED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
    }


def bind_productive_binding_decision_v1() -> dict[str, Any]:
    predicates = {
        "PRODUCTIVE_OWNER_UNIQUE": False,
        "LIFECYCLE_HOOK_UNIQUE": False,
        "BINDING_CHANGES_NO_ORDER_EXECUTION_SEMANTICS": "UNPROVEN",
        "BINDING_CANNOT_CAPTURE_WITHOUT_LATER_RUNTIME_GO": "UNPROVEN",
        "BINDING_FAIL_CLOSED": "UNPROVEN",
        "WRITER_CANNOT_RUN_BEFORE_BOUND_FILL": "UNPROVEN",
        "WRITER_CANNOT_RUN_AFTER_RESTART_AS_RETRO_SYNTHESIS": "UNPROVEN",
        "NO_HANDOFF_FROM_IMPORT_OR_STARTUP": True,
        "NO_TEST_HANDOFF_AS_PRODUCTIVE_EVIDENCE": True,
        "NO_LIVE_WIRE_NETWORK_CREDENTIAL_GATE_WEAKENED": True,
        "NO_EXISTING_SAFETY_GATE_BYPASSED": True,
        "EXPLICIT_FUTURE_AUTHORIZATION_GATE_BEFORE_REAL_EXECUTION": False,
    }
    if any(
        value is True
        for value in (
            predicates["PRODUCTIVE_OWNER_UNIQUE"],
            predicates["LIFECYCLE_HOOK_UNIQUE"],
            predicates["EXPLICIT_FUTURE_AUTHORIZATION_GATE_BEFORE_REAL_EXECUTION"],
        )
    ):
        raise Section1114OfflineSurfaceError("BINDING_PREDICATES_MUST_REMAIN_UNPROVEN_OR_FALSE")
    if PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_BINDING_MUST_REMAIN_FORBIDDEN")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_BINDING_DECISION_V1",
        "PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE": False,
        "PRODUCTIVE_BINDING_IMPLEMENTED": False,
        "PRODUCTIVE_BINDING_FAIL_CLOSED": False,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_STATUS": PRODUCTIVE_CAPTURE_OWNER_STATUS,
        "PRODUCTIVE_CAPTURE_HOOK": PRODUCTIVE_CAPTURE_HOOK,
        "PRODUCTIVE_CAPTURE_HOOK_STATUS": PRODUCTIVE_CAPTURE_HOOK_STATUS,
        "STORAGE_OWNER": FIRST_OWNER_ID,
        "STORAGE_OWNER_IS_NOT_PRODUCTIVE_CAPTURE_OWNER": True,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "MISSING_PREDICATES": list(MISSING_PREDICATES),
        "REQUIRED_NEXT_AUTHORITY": REQUIRED_NEXT_AUTHORITY,
        "predicates": predicates,
    }


def bind_future_authorized_contemporaneous_capture_window_v1(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    trigger = inventory_productive_pre_restart_capture_trigger_and_producer_v1()
    write_point = inventory_durable_write_point_and_provenance_v1()
    graph = census_productive_runtime_graph_v1(repo_root=repo_root)
    bound_fill = bind_bound_fill_semantics_v1()
    window = bind_capture_window_semantics_v1()
    surfaces = bind_authorization_surface_matrix_v1()
    minimum = bind_minimum_future_capture_window_v1()
    decision = bind_productive_binding_decision_v1()
    reader_binding = bind_restart_reader_provenance_and_consumer_v1()
    if trigger["PRODUCTIVE_RUNTIME_CALLER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_RUNTIME_CALLER_MUST_REMAIN_ZERO")
    if trigger["CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME"] is True:
        raise Section1114OfflineSurfaceError("CAPTURE_TRIGGER_MUST_REMAIN_UNJOINED")
    # Historical future-window persist required zero productive writer callers.
    # The successor CREATE slice may lawfully add exactly one. This bind still
    # forbids authorized-runtime join and does not freeze the live caller count.
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_MUST_REMAIN_FORBIDDEN")
    if reader_binding["COMPLETE_CAPTURE_SEAM"] != COMPLETE_CAPTURE_SEAM:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    missing = list(reader_binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"])
    if "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL" not in missing:
        raise Section1114OfflineSurfaceError("MISSING_CONTEMPORANEOUS_PREDICATE_DRIFT")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME": False,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_CAPTURE_OWNER_STATUS": PRODUCTIVE_CAPTURE_OWNER_STATUS,
        "PRODUCTIVE_CAPTURE_HOOK": PRODUCTIVE_CAPTURE_HOOK,
        "PRODUCTIVE_CAPTURE_HOOK_STATUS": PRODUCTIVE_CAPTURE_HOOK_STATUS,
        "CAPTURE_WINDOW_ORDERING": CAPTURE_WINDOW_ORDERING,
        "MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE": MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE,
        "PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE": False,
        "PRODUCTIVE_BINDING_IMPLEMENTED": False,
        "PRODUCTIVE_BINDING_FAIL_CLOSED": False,
        "MISSING_PREDICATES": list(MISSING_PREDICATES),
        "REQUIRED_NEXT_AUTHORITY": REQUIRED_NEXT_AUTHORITY,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "IMPLEMENTATION_AUTHORIZED": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "trigger": trigger,
        "write_point": write_point,
        "runtime_graph": graph,
        "bound_fill": bound_fill,
        "capture_window": window,
        "authorization_surfaces": surfaces,
        "minimum_future_window": minimum,
        "binding_decision": decision,
        "reader_binding": reader_binding,
    }
