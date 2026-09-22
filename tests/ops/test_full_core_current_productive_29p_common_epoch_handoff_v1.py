"""CURRENT_PRODUCTIVE 29P common-epoch handoff tests — injected transport only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
    FreshPretradeGetTransportResultV1,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_CREATED,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    ALLOWED_OWNER_GOS,
    CAP24_SUPPLY_PIN_OWNER_GO,
    EXPECTED_ORIGIN_MAIN_SHA,
    HISTORICAL_PROVENANCE_REF_ONLY,
    MAXIMUM_AUTHORIZED_DEDUPLICATED_GET_COUNT,
    MINIMUM_DEDUPLICATED_GET_COUNT,
    OWNER_GO,
    PIN_OWNER_GO,
    CurrentProductive29PCommonEpochHandoffError,
    compose_current_productive_29p_common_epoch_handoff_v1,
    enforce_deduplicated_get_budget_v1,
    execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1,
    extract_usdc_details_availeq_from_balance_payload_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_full_core_fresh_pretrade_runtime_get_seam_v1 import (
    InjectedFreshGetTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_V1.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
_TEST_INST = "ADA-USDT-SWAP"
_TEST_TD = "cross"
_EPOCH = "2026-09-22T05:14:58Z"


def _bound(*, instrument_id: str = _TEST_INST) -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=f"cap24-{instrument_id}",
        venue_native_id=instrument_id,
        ranking_snapshot_id="rank-ei-1",
        ranking_integrity_digest="rank-digest-ei-1",
        universe_snapshot_id="uni-ei-1",
        selection_id="sel-ei-1",
        selection_integrity_digest="sel-digest-ei-1",
        selection_state=STATE_SELECTED_ACTIVE,
        selected_future_count=1,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
    )


def _identity_payloads(
    *,
    instrument_id: str = _TEST_INST,
    uid: str | None = None,
    acct_lv: object = "2",
    avail_eq: str = "123.45",
    extra_usdc_row: bool = False,
) -> dict[str, object]:
    uid_value = uid or REUSED_BINDING_ACCOUNT_SCOPE
    inst_row = {"instId": instrument_id, "tdMode": _TEST_TD, "mgnMode": _TEST_TD}
    details: list[dict[str, object]] = [
        {
            "ccy": "USDC",
            "availEq": avail_eq,
            "availBal": "10.00",
            "cashBal": "11.00",
            "eq": "200.00",
            "uTime": "1726400000000",
        }
    ]
    if extra_usdc_row:
        details.append(
            {
                "ccy": "USDC",
                "availEq": "1.00",
                "uTime": "1726400000000",
            }
        )
    config_row: dict[str, object] = {
        "uid": uid_value,
        "posMode": "net_mode",
    }
    if acct_lv is not None:
        config_row["acctLv"] = acct_lv
    return {
        ENDPOINT_PUBLIC_INSTRUMENTS: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_PUBLIC_PRICE_LIMIT: {"code": "0", "data": [{"instId": instrument_id}]},
        ENDPOINT_ACCOUNT_MAX_SIZE: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_ACCOUNT_LEVERAGE_INFO: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_ACCOUNT_CONFIG: {"code": "0", "data": [config_row]},
        ENDPOINT_ACCOUNT_POSITIONS: {"code": "0", "data": []},
        ENDPOINT_ACCOUNT_BALANCE: {
            "code": "0",
            "msg": "",
            "data": [
                {
                    "uTime": "1726400000000",
                    "availEq": "999.00",
                    "uid": uid_value,
                    "details": details,
                }
            ],
        },
    }


class CountingInjectedFreshGetTransportV1(InjectedFreshGetTransportV1):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.get_call_count = 0
        self.payloads_by_path = dict(self.payloads)

    def get(self, *, endpoint, auth_required, pretrade_decision_id):
        self.get_call_count += 1
        if self.get_call_count > MAXIMUM_AUTHORIZED_DEDUPLICATED_GET_COUNT:
            raise CurrentProductive29PCommonEpochHandoffError("GET_BUDGET_EXCEEDS_MAXIMUM")
        return super().get(
            endpoint=endpoint,
            auth_required=auth_required,
            pretrade_decision_id=pretrade_decision_id,
        )


class MismatchInstrumentTransportV1(InjectedFreshGetTransportV1):
    def __init__(self, *, payloads, wrong_inst: str) -> None:
        super().__init__(payloads=payloads)
        self.payloads_by_path = dict(payloads)
        self._wrong_inst = wrong_inst

    def get(self, *, endpoint, auth_required, pretrade_decision_id):
        path = str(endpoint or "").split("?", 1)[0]
        if path == ENDPOINT_PUBLIC_INSTRUMENTS:
            payload = dict(self.payloads.get(path, {"code": "0", "data": []}))
            payload["data"] = [{"instId": self._wrong_inst, "tdMode": _TEST_TD}]
            return FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=endpoint,
                http_status=200,
                payload=payload,
                auth_header_sent=bool(auth_required),
                transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
                venue_live_contact=False,
                historical_reuse=False,
                error_class="",
            )
        return super().get(
            endpoint=endpoint,
            auth_required=auth_required,
            pretrade_decision_id=pretrade_decision_id,
        )


def _transport(**kwargs) -> CountingInjectedFreshGetTransportV1:
    return CountingInjectedFreshGetTransportV1(
        payloads=_identity_payloads(**kwargs),
    )


def _compose(**overrides):
    bound = overrides.pop("bound", _bound())
    transport = overrides.pop("transport", _transport())
    payload = {
        "decision_epoch": _EPOCH,
        "bound_instrument": bound,
        "fresh_get_transport": transport,
    }
    payload.update(overrides)
    return compose_current_productive_29p_common_epoch_handoff_v1(**payload), transport


def test_standing_flags_and_owner_go_tokens() -> None:
    assert CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_CREATED is True
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert P01_RUNTIME_INSTANCE_PRESENT is False
    assert OWNER_GO in ALLOWED_OWNER_GOS
    assert PIN_OWNER_GO in ALLOWED_OWNER_GOS
    assert CAP24_SUPPLY_PIN_OWNER_GO in ALLOWED_OWNER_GOS
    assert EXPECTED_ORIGIN_MAIN_SHA == "ac227cf8be852b0987833c5eb354610ee37e3cf5"
    assert MINIMUM_DEDUPLICATED_GET_COUNT == 7
    assert MAXIMUM_AUTHORIZED_DEDUPLICATED_GET_COUNT == 7


def test_happy_path_seven_gets_same_epoch_full_chain() -> None:
    handoff, transport = _compose()
    assert transport.get_call_count == 7
    assert handoff.deduplicated_get_count == 7
    assert handoff.config_get_count == 1
    assert handoff.balance_get_count == 1
    assert handoff.adaptation.status == "ELIGIBLE"
    assert handoff.eligibility is not None
    assert handoff.eligibility.decision_epoch == _EPOCH
    assert handoff.observation is not None
    assert handoff.observation.decision_epoch == _EPOCH
    assert handoff.p01_fact is not None
    assert handoff.produced is True
    assert handoff.lab_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    assert handoff.instrument_bound is True
    assert handoff.evaluator_29p is True
    assert handoff.get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value


def test_acct_lv_missing_fail_closed_u01() -> None:
    transport = _transport(acct_lv=None)
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=_EPOCH,
        bound_instrument=_bound(),
        fresh_get_transport=transport,
    )
    assert handoff.eligibility is None
    assert handoff.produced is False


@pytest.mark.parametrize(
    "avail_eq",
    ["", "NaN", "not-a-number"],
)
def test_usdc_row_fail_closed(avail_eq: str) -> None:
    if avail_eq == "":
        payloads = _identity_payloads()
        payloads[ENDPOINT_ACCOUNT_BALANCE] = {
            "code": "0",
            "data": [{"uid": REUSED_BINDING_ACCOUNT_SCOPE, "details": []}],
        }
        transport = CountingInjectedFreshGetTransportV1(payloads=payloads)
        handoff = compose_current_productive_29p_common_epoch_handoff_v1(
            decision_epoch=_EPOCH,
            bound_instrument=_bound(),
            fresh_get_transport=transport,
        )
        assert handoff.observation is None
        return
    with pytest.raises(CurrentProductive29PCommonEpochHandoffError):
        extract_usdc_details_availeq_from_balance_payload_v1(
            {
                "code": "0",
                "data": [
                    {
                        "details": [{"ccy": "USDC", "availEq": avail_eq}],
                    }
                ],
            }
        )


def test_duplicate_usdc_row_fail_closed() -> None:
    transport = _transport(extra_usdc_row=True)
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=_EPOCH,
        bound_instrument=_bound(),
        fresh_get_transport=transport,
    )
    assert handoff.observation is None


def test_cap24_missing_fail_closed() -> None:
    with pytest.raises(CurrentProductive29PCommonEpochHandoffError, match="BOUND_INSTRUMENT"):
        compose_current_productive_29p_common_epoch_handoff_v1(
            decision_epoch=_EPOCH,
            bound_instrument=None,
            fresh_get_transport=_transport(),
        )


def test_cap24_untrusted_fields_fail_closed() -> None:
    bad = _bound()
    bad_dict = bad.to_dict()
    bad_dict["selection_integrity_digest"] = ""
    with pytest.raises(CurrentProductive29PCommonEpochHandoffError):
        compose_current_productive_29p_common_epoch_handoff_v1(
            decision_epoch=_EPOCH,
            bound_instrument=BoundInstrumentV1(**bad_dict),
            fresh_get_transport=_transport(),
        )


def test_observed_instrument_mismatch_fail_closed_scope() -> None:
    transport = MismatchInstrumentTransportV1(
        payloads=_identity_payloads(),
        wrong_inst="ETH-USDT-SWAP",
    )
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=_EPOCH,
        bound_instrument=_bound(),
        fresh_get_transport=transport,
    )
    assert handoff.instrument_bound is False
    assert handoff.observed_instrument_id == ""


def test_live_account_bound_not_trusted_when_get_stale() -> None:
    transport = InjectedFreshGetTransportV1(
        payloads=_identity_payloads(),
        historical_reuse=True,
    )
    transport.payloads_by_path = dict(transport.payloads)
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=_EPOCH,
        bound_instrument=_bound(),
        fresh_get_transport=transport,
    )
    assert handoff.get_status == FreshPretradeGetStatusV1.STALE.value
    assert handoff.lab_trusted is False


def test_decision_epoch_malformed_fail_closed() -> None:
    with pytest.raises(
        CurrentProductive29PCommonEpochHandoffError, match="DECISION_EPOCH_MALFORMED"
    ):
        compose_current_productive_29p_common_epoch_handoff_v1(
            decision_epoch="  ",
            bound_instrument=_bound(),
            fresh_get_transport=_transport(),
        )


def test_get_budget_invariant_rejects_more_than_seven() -> None:
    with pytest.raises(CurrentProductive29PCommonEpochHandoffError, match="EXCEEDS_MAXIMUM"):
        enforce_deduplicated_get_budget_v1(
            deduplicated_get_count=8,
            config_get_count=1,
            balance_get_count=1,
        )


def test_execute_offline_missing_bound_first_blocker(tmp_path: Path) -> None:
    result = execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        bound_instrument=None,
        fresh_get_transport=_transport(),
        evidence_root=tmp_path / "pack",
    )
    assert result.first_real_blocker == "CURRENT_PRODUCTIVE_CAP24_BOUND_INSTRUMENT_INSTANCE_MISSING"
    assert result.deduplicated_get_count == 0
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["HISTORICAL_EVIDENCE_INPUT"] == "false"
    assert claims["HISTORICAL_PROVENANCE_REF_ONLY"] == HISTORICAL_PROVENANCE_REF_ONLY
    assert claims["VENUE_GET_PERFORMED"] == "false"
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0


def test_execute_happy_injected_not_productive_29p(tmp_path: Path) -> None:
    result = execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1(
        owner_go=PIN_OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        bound_instrument=_bound(),
        fresh_get_transport=_transport(),
        evidence_root=tmp_path / "pack",
    )
    assert result.deduplicated_get_count == 7
    assert result.step_29p_risk_admissible == "false"
    assert result.first_real_blocker == (
        "CURRENT_PRODUCTIVE_29P_REQUIRES_PRODUCTIVE_TRUSTED_GET_AND_CAP24_BOUND_INSTRUMENT"
    )
    assert result.p01_status == "DOES_NOT_APPLY"
    assert result.u01_status == "ELIGIBLE"


def test_producer_and_step29p_evaluator_invoked() -> None:
    with (
        patch(
            "src.ops.governed_productive_account_equity_authority_producer_v1."
            "current_productive_29p_common_epoch_handoff_v1.produce_current_productive_29p_risk_capital_v1"
        ) as mock_producer,
        patch(
            "src.ops.governed_productive_account_equity_authority_producer_v1."
            "current_productive_29p_common_epoch_handoff_v1.evaluate_step_29p_capital_risk_admissibility_v1"
        ) as mock_29p,
        patch(
            "src.ops.governed_productive_account_equity_authority_producer_v1."
            "current_productive_29p_common_epoch_handoff_v1.evaluate_live_account_bound_v1"
        ) as mock_lab,
    ):
        mock_producer.side_effect = __import__(
            "src.ops.governed_productive_account_equity_authority_producer_v1."
            "current_productive_29p_risk_capital_model_v1",
            fromlist=["produce_current_productive_29p_risk_capital_v1"],
        ).produce_current_productive_29p_risk_capital_v1
        mock_29p.side_effect = __import__(
            "src.ops.full_core_live_path_composition_root_v1."
            "step_29p_capital_risk_admissibility_v1",
            fromlist=["evaluate_step_29p_capital_risk_admissibility_v1"],
        ).evaluate_step_29p_capital_risk_admissibility_v1
        mock_lab.side_effect = __import__(
            "src.ops.full_core_live_path_composition_root_v1.live_account_bound_v1",
            fromlist=["evaluate_live_account_bound_v1"],
        ).evaluate_live_account_bound_v1
        _compose()
    assert mock_producer.called
    assert mock_29p.called
    assert mock_lab.called


def test_ssot_docs_once_present() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_V1" in spec
    assert "11.2.1.EI" in atlas
    assert "current_productive_29p_common_epoch_handoff_v1.py" in atlas
    assert "COMMON_EPOCH" in spec or "common-epoch" in spec.lower()
