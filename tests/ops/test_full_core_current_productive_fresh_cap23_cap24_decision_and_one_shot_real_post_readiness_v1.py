"""CURRENT_PRODUCTIVE fresh Cap-23/24 and one-shot real-POST readiness tests.

Injected acquisition/GET only. No venue POST. REAL_POST_COUNT=0.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM,
    EXTERNAL_EFFECT_AUTHORIZED,
    FOLLOW_ON_SUBMIT_ISOLATED,
    FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    MAX_EXTERNAL_EFFECT_POST_COUNT,
    ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT,
    ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN,
    ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED,
    POST_ALLOWED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    REPLAY_PROTECTION_DURABLE,
    SUBMISSION_AUTHORIZED,
    WIRE_SEND_PERMITTED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT,
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    attempt_envelope_bound_external_effect_send_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ONE_SHOT_REAL_POST_AUTHORITY_REFS,
    issue_external_effect_permit_v1,
    permit_authorizes_one_shot_real_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreNonNetworkingTestPostTransportV1,
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
    FullCoreTradeOrderPostResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_DECISION_AND_ONE_SHOT_REAL_POST_READINESS_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveFreshCap23Cap24ReadinessError,
    execute_current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    InjectedPayloadsFreshGetTransportV1,
    _eligible_transport,
    _identity_payloads,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _envelope,
    _handle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_"
    "DECISION_AND_ONE_SHOT_REAL_POST_READINESS_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DJ_HEADING = (
    "### 11.2.1.DJ FULL_CORE_CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_"
    "DECISION_AND_ONE_SHOT_REAL_POST_READINESS"
)
NEXT_BLOCKER = "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
LATER_POST_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


class _RecordingOneShotTransport:
    transport_class = "RECORDING_ONE_SHOT_TEST_DOUBLE"
    post_count = 0
    venue_live_contact = False
    last_one_shot = False

    def post_trade_order(self, **kwargs: object) -> FullCoreTradeOrderPostResultV1:
        one_shot = kwargs.get("one_shot_real_post") is True
        self.last_one_shot = one_shot
        self.post_count += 1
        self.venue_live_contact = one_shot is True
        return FullCoreTradeOrderPostResultV1(
            post_attempted=True,
            venue_live_contact=one_shot is True,
            method="POST",
            endpoint="/api/v5/trade/order",
            http_status=0,
            payload={"mocked": True, "code": "0"},
            transport_class=self.transport_class,
            unknown_outcome=False,
        )


def _run(tmp_path: Path, **overrides):
    payload = {
        "owner_go": OWNER_GO,
        "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "evidence_root": tmp_path / "store",
        "acquisition_transport": _eligible_transport(),
        "fresh_get_transport": InjectedPayloadsFreshGetTransportV1(payloads=_identity_payloads()),
        "execute_network": False,
        "producer_observed_at_unix": 1_700_000_100.0,
        "replay": None,
    }
    payload.update(overrides)
    return (
        execute_current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1(
            **payload
        )
    )


def test_standing_flags_keep_real_post_fail_closed() -> None:
    assert (
        CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_DECISION_AND_ONE_SHOT_REAL_POST_READINESS_CREATED
        is True
    )
    assert ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED is True
    assert ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT is True
    assert ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN is True
    assert ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM is True
    assert FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED is True
    assert int(MAX_EXTERNAL_EFFECT_POST_COUNT) == 1
    assert REPLAY_PROTECTION_DURABLE is True
    assert FOLLOW_ON_SUBMIT_ISOLATED is True
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert SUBMISSION_AUTHORIZED is True
    assert LIVE_AUTHORIZED is True
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert EXPECTED_ORIGIN_MAIN_SHA == "114a68670bdd552fc1fcc90352a01b4dd7dc4dc5"
    assert current_productive_first_real_blocker_v1() == NEXT_BLOCKER
    assert LATER_POST_GO in ONE_SHOT_REAL_POST_AUTHORITY_REFS
    assert OWNER_GO not in ONE_SHOT_REAL_POST_AUTHORITY_REFS


def test_readiness_go_does_not_authorize_one_shot_real_post() -> None:
    envelope = _envelope()
    readiness_permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=OWNER_GO,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    later_permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=LATER_POST_GO,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    assert permit_authorizes_one_shot_real_post_v1(readiness_permit) is False
    assert permit_authorizes_one_shot_real_post_v1(later_permit) is True


def test_default_http_transport_still_forbids_socket() -> None:
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle())
    with pytest.raises(FullCoreProductiveHttpPostError, match="REAL_VENUE_POST_FORBIDDEN"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="eep-fixture",
            envelope_id="env-fixture",
            envelope_digest="0" * 64,
        )
    assert transport.post_count == 0
    assert transport.venue_live_contact is False


def test_one_shot_http_without_signing_handle_does_not_open_socket() -> None:
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle())
    with pytest.raises(FullCoreProductiveHttpPostError, match="SIGNING_HANDLE_MISSING"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="eep-fixture",
            envelope_id="env-fixture",
            envelope_digest="0" * 64,
            one_shot_real_post=True,
        )
    assert transport.post_count == 0
    assert transport.venue_live_contact is False


def test_send_seam_mocked_path_unchanged_for_non_one_shot_permit(tmp_path: Path) -> None:
    envelope = _envelope()
    permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=OWNER_GO,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    transport = FullCoreNonNetworkingTestPostTransportV1()
    result = attempt_envelope_bound_external_effect_send_v1(
        envelope=envelope,
        permit=permit,
        store_root=tmp_path / "mocked",
        transport=transport,
        handle=_handle(),
    )
    assert result.mocked_post_count == 1
    assert result.real_post_count == 0
    assert result.venue_live_contact is False


def test_send_seam_one_shot_flag_reaches_full_core_transport_double(tmp_path: Path) -> None:
    envelope = _envelope()
    permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=LATER_POST_GO,
        kill_switch_blocked=False,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        filegate_denied=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    transport = _RecordingOneShotTransport()
    result = attempt_envelope_bound_external_effect_send_v1(
        envelope=envelope,
        permit=permit,
        store_root=tmp_path / "one-shot",
        transport=transport,  # type: ignore[arg-type]
        handle=_handle(),
    )
    assert transport.last_one_shot is True
    assert result.real_post_count == 1
    assert result.mocked_post_count == 0
    assert result.venue_live_contact is True
    assert result.durable_consumed is True


def test_missing_replay_is_truthful_non_executable() -> None:
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=None,
        bound_instrument=None,  # type: ignore[arg-type]
        session_id="x",
        run_id="y",
        composed_epoch="2026-09-15T20:15:00Z",
    )
    assert status is CompositionStatusV1.DENY
    assert CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT in reasons
    assert plan is None


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveFreshCap23Cap24ReadinessError, match="OWNER_GO_MISMATCH"):
        _run(tmp_path / "a", owner_go="WRONG")
    with pytest.raises(
        CurrentProductiveFreshCap23Cap24ReadinessError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        _run(tmp_path / "b", origin_main_sha="0" * 40)


def test_injected_path_mints_fresh_cap23_cap24_without_fabricating_enter(
    tmp_path: Path,
) -> None:
    result = _run(tmp_path)
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.cap23_selected_instrument_id
    assert result.cap23_selected_instrument_id != CANARY_DEFAULT_INSTRUMENT_ID
    assert result.cap23_selected_instrument_id != DEFAULT_INSTRUMENT_ID
    assert result.cap24_bound_instrument_id
    assert result.decision_result == "NO_EXECUTABLE_DECISION"
    assert result.decision_provenance == CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT
    assert result.envelope_readiness == "false"
    assert result.one_shot_real_post_seam_implemented == "true"
    assert result.real_external_effect_authorized == "false"
    assert result.post_count == "0"
    assert result.first_real_blocker == CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT
    assert claims["POST_COUNT"] == "0"
    assert claims["TRANSPORT_ATTEMPTED"] == "false"
    assert claims["VENUE_MUTATION_PERFORMED"] == "false"
    assert claims["PERMIT_CONSUMED_DURABLY"] == "false"
    assert claims["STEP_29Q_STATUS"] == STEP_29Q_PLAN_ONLY
    assert claims["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert claims["CANARY_INSTRUMENT_AUTHORITY_IMPORTED"] == "false"
    assert claims["FRESH_PRE_SUBMIT_EVIDENCE"] == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    assert claims["PROTECTED_SURFACES_CHANGED"] == "false"
    assert verify_manifest_sha256_v1(store_root=Path(result.store_root)) == 0


def test_protected_algorithm_files_unchanged_vs_origin_main() -> None:
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", *PROTECTED_ALGORITHM_FILES],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert diff.stdout.strip() == ""


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert DJ_HEADING in runbook
    assert THIS_SLICE in runbook
    dj_section = runbook[
        runbook.index(
            "11.2.1.DJ FULL_CORE_CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_"
            "DECISION_AND_ONE_SHOT_REAL_POST_READINESS"
        ) : runbook.index("## 11.3 Autonomy state model")
    ]
    assert "ONE_SHOT_REAL_POST_SEAM_IMPLEMENTED=true" in dj_section
    assert "EXTERNAL_EFFECT_AUTHORIZED=false" in dj_section
    assert "REAL_EXTERNAL_EFFECT_AUTHORIZED=false" in dj_section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in dj_section
    assert "POST_COUNT=0" in dj_section
    assert "REAL_EXTERNAL_EFFECT_AUTHORIZED=false" in dj_section
    assert SPEC_PATH.name in mot
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_FRESH_CAP23_CAP24_"
        "DECISION_AND_ONE_SHOT_REAL_POST_READINESS_V1"
    ) in spec
    assert "11.2.1.DJ" in atlas
    assert (
        "current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1.py"
        in atlas
    )
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["ONE_SHOT_REAL_POST_SEAM_IMPLEMENTED"] == "true"
    assert claims["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert claims["REAL_EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert claims["POST_COUNT"] == "0"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["CANARY_INSTRUMENT_AUTHORITY_IMPORTED"] == "false"
    assert claims["CAP23_SELECTED_INSTRUMENT_ID"] != CANARY_DEFAULT_INSTRUMENT_ID
    assert claims["CAP23_SELECTED_INSTRUMENT_ID"] != DEFAULT_INSTRUMENT_ID
    assert claims["TRANSPORT_ATTEMPTED"] == "false"
    assert claims["VENUE_MUTATION_PERFORMED"] == "false"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
