"""Cap-24 writer persisted baseline joins common-epoch handoff (runtime integrity)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    RUNTIME_INTEGRITY_CONTRACT_VERSION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    PIN_OWNER_GO,
    execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
    TRUSTED_TEST_ORIGIN_MAIN_SHA,
)
from tests.ops.test_full_core_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    _build_fresh_chain,
    _materialize_productivity_root,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    CountingInjectedFreshGetTransportV1,
    _identity_payloads,
)

LEGACY_CAP24_REPOSITORY_SHA = "e5396206530415b469fa345ec04322613c953c44"
_INTEGRITY = MockCurrentProductive29PIntegrityBackendV1()


def test_common_epoch_resolves_legacy_cap24_repository_sha(tmp_path: Path) -> None:
    chain = _build_fresh_chain(
        tmp_path / "build",
        repository_sha=LEGACY_CAP24_REPOSITORY_SHA,
    )
    prod = _materialize_productivity_root(tmp_path, chain)
    inst = str(chain["venue_native_id"])
    transport = CountingInjectedFreshGetTransportV1(payloads=_identity_payloads(instrument_id=inst))
    fixed_epoch = chain["binding_epoch"]
    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_29p_common_epoch_handoff_v1._utc_now_iso_v1",
        return_value=fixed_epoch,
    ):
        result = execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1(
            owner_go=PIN_OWNER_GO,
            origin_main_sha=TRUSTED_TEST_ORIGIN_MAIN_SHA,
            bound_instrument=None,
            fresh_get_transport=transport,
            evidence_root=tmp_path / "pack",
            cap24_productivity_root=prod,
            execution_integrity_backend=_INTEGRITY,
        )
    assert result.bound_instrument_id == chain["instrument_id"]
    assert result.deduplicated_get_count == 7
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert claims["CAP24_PROVENANCE_HANDOFF_STATUS"] == "ACQUIRED"
    assert claims["EXPECTED_ORIGIN_MAIN"] == TRUSTED_TEST_ORIGIN_MAIN_SHA


def test_writer_and_common_epoch_share_runtime_integrity_contract() -> None:
    assert RUNTIME_INTEGRITY_CONTRACT_VERSION == "current_productive_29p_chain_runtime_integrity.v1"
