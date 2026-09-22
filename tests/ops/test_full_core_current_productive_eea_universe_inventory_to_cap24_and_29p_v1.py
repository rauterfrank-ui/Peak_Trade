"""CURRENT_PRODUCTIVE EEA universe inventory → Cap-2.1–2.4 → 29P tests.

Injected acquisition and GET only. No productive network. No POST.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    acquire_eea_universe_inventory_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CAP21_NETWORK_OWNER,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    EeaPublicGetResultV1,
    EeaUniverseAcquisitionError,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import ECONOMIC_RANK_ACTIVATED
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_PUBLIC_INSTRUMENTS as PRETRADE_INSTRUMENTS,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED,
    CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_ADAPTER_CREATED,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    ALLOWED_OWNER_GOS,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    CurrentProductiveEeaUniverseTo29PError,
    execute_current_productive_eea_universe_inventory_to_cap24_and_29p_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_fresh_pretrade_runtime_get_seam_v1 import (
    InjectedFreshGetTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_PATH = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
CZ_HEADING = "### 11.2.1.CZ FULL_CORE_CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P"
_TEST_TD = "cross"
_EXPECTED_SELECTED = "ADA-USDT-SWAP"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


def _perp(inst_id: str, *, base: str) -> dict[str, str]:
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "baseCcy": base,
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": base,
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": f"{base}-USDT",
        "expTime": "",
    }


def _okx_envelope(*, rows: list[dict[str, str]], code: str = "0", ts: str = "1700000000000"):
    return {"code": code, "msg": "", "data": rows, "ts": ts}


def _eligible_rows() -> list[dict[str, str]]:
    return [
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ETH-USDT-SWAP", base="ETH"),
        _perp("ADA-USDT-SWAP", base="ADA"),
    ]


def _marks(rows: list[dict[str, str]]) -> dict[str, object]:
    return _okx_envelope(rows=[{"instId": str(row["instId"]), "markPx": "100.5"} for row in rows])


class FakeEeaPublicUniverseGetTransportV1:
    def __init__(self, payloads: dict[tuple[str, str], dict[str, object]]) -> None:
        self._payloads = payloads
        self.request_count = 0
        self.methods_used: list[str] = []
        self.venue_live_contact = False

    def get(self, *, path: str, query: dict[str, str]) -> EeaPublicGetResultV1:
        inst_type = str(query.get("instType") or "")
        payload = self._payloads.get((path, inst_type), {"code": "0", "data": [], "msg": ""})
        self.request_count += 1
        self.methods_used.append("GET")
        return EeaPublicGetResultV1(
            url=f"https://{AUTHORIZED_HOST}{path}?instType={inst_type}",
            path=path,
            query=f"instType={inst_type}",
            host=AUTHORIZED_HOST,
            method="GET",
            http_status=200,
            payload=payload,
            body_sha256="abc",
            ts=str(payload.get("ts") or ""),
            error_class="",
            venue_live_contact=False,
        )


class InjectedPayloadsFreshGetTransportV1(InjectedFreshGetTransportV1):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.payloads_by_path = dict(self.payloads)


def _identity_payloads(*, instrument_id: str = _EXPECTED_SELECTED, uid: str | None = None):
    uid_value = uid or REUSED_BINDING_ACCOUNT_SCOPE
    inst_row = {"instId": instrument_id, "tdMode": _TEST_TD, "mgnMode": _TEST_TD}
    return {
        PRETRADE_INSTRUMENTS: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_PUBLIC_PRICE_LIMIT: {"code": "0", "data": [{"instId": instrument_id}]},
        ENDPOINT_ACCOUNT_MAX_SIZE: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_ACCOUNT_LEVERAGE_INFO: {"code": "0", "data": [dict(inst_row)]},
        ENDPOINT_ACCOUNT_CONFIG: {
            "code": "0",
            "data": [{"uid": uid_value, "acctLv": "2", "posMode": "net_mode"}],
        },
        ENDPOINT_ACCOUNT_POSITIONS: {"code": "0", "data": []},
        ENDPOINT_ACCOUNT_BALANCE: {
            "code": "0",
            "msg": "",
            "data": [
                {
                    "uTime": "1726400000000",
                    "availEq": "999.00",
                    "totalEq": "1000.00",
                    "adjEq": "800.00",
                    "uid": uid_value,
                    "details": [
                        {
                            "ccy": "USDC",
                            "availEq": "123.45",
                            "availBal": "10.00",
                            "cashBal": "11.00",
                            "eq": "200.00",
                            "uTime": "1726400000000",
                        }
                    ],
                }
            ],
        },
    }


def _eligible_transport() -> FakeEeaPublicUniverseGetTransportV1:
    rows = _eligible_rows()
    return FakeEeaPublicUniverseGetTransportV1(
        {
            (ENDPOINT_PUBLIC_INSTRUMENTS, "FUTURES"): _okx_envelope(rows=[]),
            (ENDPOINT_PUBLIC_MARK_PRICE, "FUTURES"): _okx_envelope(rows=[]),
            (ENDPOINT_PUBLIC_INSTRUMENTS, "SWAP"): _okx_envelope(rows=rows),
            (ENDPOINT_PUBLIC_MARK_PRICE, "SWAP"): _marks(rows),
        }
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
    }
    payload.update(overrides)
    return execute_current_productive_eea_universe_inventory_to_cap24_and_29p_v1(**payload)


def test_flags_and_authority_bounds() -> None:
    assert CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_ADAPTER_CREATED is True
    assert CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED is False
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert P01_RUNTIME_INSTANCE_PRESENT is False
    assert CAP21_NETWORK_OWNER is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert DEFAULT_INSTRUMENT_ID == CANARY_DEFAULT_INSTRUMENT_ID
    assert OWNER_GO in ALLOWED_OWNER_GOS
    assert EXPECTED_ORIGIN_MAIN_SHA == "ee3850128e01378f4b480f4ab1b5e57dd8ee24a3"


def test_acquisition_rejects_www_okx_and_non_get() -> None:
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
        _assert_get_url_v1,
    )

    with pytest.raises(EeaUniverseAcquisitionError, match="HOST_NOT_EEA_OKX"):
        _assert_get_url_v1(
            url="https://www.okx.com/api/v5/public/instruments?instType=SWAP",
            path=ENDPOINT_PUBLIC_INSTRUMENTS,
        )
    with pytest.raises(EeaUniverseAcquisitionError, match="NON_HTTPS_FORBIDDEN"):
        _assert_get_url_v1(
            url="http://eea.okx.com/api/v5/public/instruments?instType=SWAP",
            path=ENDPOINT_PUBLIC_INSTRUMENTS,
        )


def test_acquisition_soft_fails_empty_or_errored_swap_when_futures_present() -> None:
    rows = [
        {
            "instId": "ETH-USDT-250328",
            "instType": "FUTURES",
            "state": "live",
            "baseCcy": "ETH",
            "quoteCcy": "USDT",
            "settleCcy": "USDT",
            "ctType": "linear",
            "ctVal": "0.01",
            "ctValCcy": "ETH",
            "tickSz": "0.01",
            "lotSz": "1",
            "minSz": "1",
            "uly": "ETH-USDT",
            "expTime": "1743120000000",
        }
    ]
    result = acquire_eea_universe_inventory_v1(
        transport=FakeEeaPublicUniverseGetTransportV1(
            {
                (ENDPOINT_PUBLIC_INSTRUMENTS, "FUTURES"): _okx_envelope(rows=rows),
                (ENDPOINT_PUBLIC_MARK_PRICE, "FUTURES"): _marks(rows),
                (ENDPOINT_PUBLIC_INSTRUMENTS, "SWAP"): _okx_envelope(rows=[], code="51000"),
                (ENDPOINT_PUBLIC_MARK_PRICE, "SWAP"): _okx_envelope(rows=[], code="51000"),
            }
        ),
        observed_at="2026-09-15T14:00:00Z",
    )
    assert result.ok is True
    assert result.host == AUTHORIZED_HOST
    assert result.post_count == "0"
    assert "GET" in result.methods_used
    assert result.provenance["CAP21_NETWORK_OWNER"] is False
    assert result.provenance["INSTID_FORCED"] is False
    assert "VENUE_CODE_51000" in result.provenance["SOFT_FAILURE_CODES"]


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveEeaUniverseTo29PError, match="OWNER_GO_MISMATCH"):
        _run(tmp_path / "a", owner_go="WRONG")
    with pytest.raises(CurrentProductiveEeaUniverseTo29PError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        _run(tmp_path / "b", origin_main_sha="0" * 40)


def test_injected_path_mints_current_cap21_to_cap24_without_canary_or_manual_choice(
    tmp_path: Path,
) -> None:
    result = _run(tmp_path)
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.eea_universe_acquisition_status == "PASS"
    assert result.cap21_snapshot_id
    assert int(result.cap21_universe_size) >= 1
    assert result.cap22_ranking_id
    assert result.cap23_selection_decision_id
    assert result.cap23_selected_instrument_id == _EXPECTED_SELECTED
    assert result.cap23_selected_instrument_id != CANARY_DEFAULT_INSTRUMENT_ID
    assert result.cap23_selected_instrument_id != DEFAULT_INSTRUMENT_ID
    assert result.cap24_bound_instrument_id
    assert result.p01_status == "DOES_NOT_APPLY"
    assert result.post_count == "0"
    assert claims["RESELECTION_AUTHORIZED_BY_THIS_GO"] == "true"
    assert claims["MANUAL_INSTRUMENT_SELECTION_PERFORMED"] == "false"
    assert claims["SELECTION_ALGORITHM_CHANGED"] == "false"
    assert claims["RANKING_ALGORITHM_CHANGED"] == "false"
    assert claims["UNIVERSE_SEMANTICS_CHANGED"] == "false"
    assert claims["CANARY_INSTRUMENT_AUTHORITY_IMPORTED"] == "false"
    assert claims["CAP21_NETWORK_OWNER_CHANGED"] == "false"
    assert claims["ECONOMIC_RANK_ACTIVATED"] == "false"
    assert claims["MAX_POSITIONS_EFFECTIVE"] == "1"
    assert claims["LIVE_ENABLED"] == "true"
    assert claims["LIVE_ARMED"] == "true"
    assert claims["WIRE_SEND_PERMITTED"] == "true"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "false"
    assert result.first_real_blocker == (
        "CURRENT_PRODUCTIVE_29P_REQUIRES_PRODUCTIVE_TRUSTED_GET_AND_CAP24_BOUND_INSTRUMENT"
    )
    assert result.blocker_class == "C"
    assert verify_manifest_sha256_v1(store_root=Path(result.store_root)) == 0


def test_protected_algorithm_files_unchanged_vs_origin_main() -> None:
    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", *PROTECTED_ALGORITHM_FILES],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert diff.stdout.strip() == ""


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert (
        CZ_HEADING in runbook or "EEA_UNIVERSE_INVENTORY_TO_CAP24" in runbook or SPEC_PATH.is_file()
    )
    assert SPEC_PATH.name in mot or "NAVIGATION_ONLY" in mot or "MAP_OF_TRUTH" in mot
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_TO_CAP24_AND_29P_V1" in spec
    )
    assert "11.2.1.CZ" in atlas
    assert "current_productive_eea_universe_inventory_to_cap24_and_29p_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["CANARY_INSTRUMENT_AUTHORITY_IMPORTED"] == "false"
    assert claims["POST_COUNT"] == "0"
    assert claims["P01_POLICY_DECISION"] == "DOES_NOT_APPLY"
    assert claims["MANUAL_INSTRUMENT_SELECTION_PERFORMED"] == "false"
    assert claims["LIVE_ENABLED"] == "false"
    assert claims["LIVE_ARMED"] == "false"
    assert claims["WIRE_SEND_PERMITTED"] == "false"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "true"
    assert claims["FIRST_REAL_BLOCKER"] == "LIVE_ENABLED_STANDING_GATE_REMAINS_FALSE"
    assert claims["BLOCKER_CLASS"] == "E"
    assert claims["CAP23_SELECTED_INSTRUMENT_ID"] != CANARY_DEFAULT_INSTRUMENT_ID
    assert claims["CAP23_SELECTED_INSTRUMENT_ID"] != DEFAULT_INSTRUMENT_ID
    assert verify_manifest_sha256_v1(store_root=pack) == 0
