"""FAM-A productive lineage enforcement: shared chain binding + reserved Cap24 CLI guard."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
    CurrentProductiveCap21ToCap23PersistenceError,
    run_cap21_to_cap23_persist_productive_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap24_reserved_productivity_root_guard_v1 import (
    FAILURE_RESERVED_CAP24_PRODUCTIVITY_ROOT,
    ReservedCap24ProductivityRootError,
    assert_standalone_capability_state_root_not_reserved_cap24_v1,
    reserved_cap24_productivity_root_v1,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    _eligible_rows,
    _okx_envelope,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "e82e65ee6bf36ad9c3983919e388413234f8f4a9"


def _acquisition() -> EeaUniverseAcquisitionResultV1:
    rows = _eligible_rows()
    ids = [r["instId"] for r in rows]
    return EeaUniverseAcquisitionResultV1(
        ok=True,
        host="eea.okx.com",
        venue="okx_eea",
        source_kind="okx_eea_public_instruments",
        source_event_time="1700000000000",
        instruments_payload=_okx_envelope(rows=rows),
        mark_price_payload=_okx_envelope(
            rows=[{"instId": i, "markPx": "100.5"} for i in ids],
            ts="1700000000000",
        ),
        endpoints_used=("/api/v5/public/instruments",),
        methods_used=("GET",),
        post_count="0",
        request_count=2,
        venue_live_contact=False,
        failure_codes=(),
        provenance={"test": True},
    )


def test_shared_chain_proceeds_with_valid_cap22_binding(tmp_path: Path) -> None:
    result = run_cap21_to_cap23_persist_productive_v1(
        acquisition=_acquisition(),
        store=tmp_path / "store",
        repository_sha=BASE_SHA,
        observed_unix=1_700_000_100.0,
        session_id_prefix="fam-a-test",
    )
    assert result.ok is True
    assert result.selection is not None


def test_shared_chain_fails_closed_on_cap22_binding_drift(tmp_path: Path) -> None:
    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_cap21_to_cap23_productive_persistence_v1.RANKING_POLICY_ID",
        "POLICY_DRIFT_FOR_TEST",
    ):
        with pytest.raises(
            CurrentProductiveCap21ToCap23PersistenceError, match="RANKING_POLICY_DRIFT"
        ):
            run_cap21_to_cap23_persist_productive_v1(
                acquisition=_acquisition(),
                store=tmp_path / "store",
                repository_sha=BASE_SHA,
                observed_unix=1_700_000_100.0,
                session_id_prefix="fam-a-test",
            )


def test_direct_chain_invocation_cannot_bypass_binding_assert(tmp_path: Path) -> None:
    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_cap21_to_cap23_productive_persistence_v1."
        "assert_current_productive_cap22_ranking_policy_binding_v1",
        side_effect=CurrentProductiveCap21ToCap23PersistenceError("RANKING_POLICY_DRIFT"),
    ) as mocked:
        with pytest.raises(CurrentProductiveCap21ToCap23PersistenceError):
            run_cap21_to_cap23_persist_productive_v1(
                acquisition=_acquisition(),
                store=tmp_path / "store",
                repository_sha=BASE_SHA,
                observed_unix=1_700_000_100.0,
                session_id_prefix="fam-a-test",
            )
        mocked.assert_called_once()


def test_guard_allows_non_reserved_root(tmp_path: Path) -> None:
    allowed = tmp_path / "capability_evidence_root"
    assert_standalone_capability_state_root_not_reserved_cap24_v1(allowed)


def test_guard_rejects_exact_reserved_root() -> None:
    reserved = reserved_cap24_productivity_root_v1()
    with pytest.raises(ReservedCap24ProductivityRootError) as exc:
        assert_standalone_capability_state_root_not_reserved_cap24_v1(reserved)
    assert exc.value.failure_code == FAILURE_RESERVED_CAP24_PRODUCTIVITY_ROOT


def test_guard_rejects_descendant_of_reserved_root() -> None:
    reserved = reserved_cap24_productivity_root_v1()
    descendant = reserved / "runtime_state" / "selection"
    with pytest.raises(ReservedCap24ProductivityRootError):
        assert_standalone_capability_state_root_not_reserved_cap24_v1(descendant)


def test_guard_rejects_resolved_path_alias(tmp_path: Path) -> None:
    reserved = reserved_cap24_productivity_root_v1()
    alias = tmp_path / "alias_to_reserved"
    try:
        os.symlink(reserved, alias, target_is_directory=True)
    except OSError:
        pytest.skip("symlink not supported in this environment")
    with pytest.raises(ReservedCap24ProductivityRootError):
        assert_standalone_capability_state_root_not_reserved_cap24_v1(alias / "runtime_state")


def test_guard_allows_sibling_outside_reserved_root() -> None:
    reserved = reserved_cap24_productivity_root_v1()
    sibling = reserved.parent / "cap24_selection_state_isolated_test_sibling"
    assert_standalone_capability_state_root_not_reserved_cap24_v1(sibling)


def _instruments_json(tmp_path: Path) -> Path:
    rows = _eligible_rows()
    path = tmp_path / "instruments.json"
    path.write_text(json.dumps(_okx_envelope(rows=rows)), encoding="utf-8")
    return path


def _ranking_snapshot_json(tmp_path: Path) -> Path:
    path = tmp_path / "ranking.json"
    path.write_text(
        json.dumps(
            {
                "ranking_snapshot_id": "rank_test",
                "event_time": "2020-01-01T00:00:00Z",
                "integrity_digest": "0" * 64,
                "ranked_instruments": [],
            }
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    "script",
    [
        "scripts/ops/run_governed_futures_universe_producer_v1.py",
        "scripts/ops/run_productive_futures_ranking_producer_v1.py",
        "scripts/ops/run_single_selected_future_policy_v1.py",
    ],
)
def test_capability_cli_rejects_reserved_root(tmp_path: Path, script: str) -> None:
    reserved = reserved_cap24_productivity_root_v1()
    instruments = _instruments_json(tmp_path)
    ranking = _ranking_snapshot_json(tmp_path)
    if script.endswith("run_governed_futures_universe_producer_v1.py"):
        cmd = [
            str(REPO_ROOT / "scripts/pt"),
            script,
            "--state-root",
            str(reserved / "runtime_state" / "universe"),
            "--instruments-json",
            str(instruments),
        ]
    elif script.endswith("run_productive_futures_ranking_producer_v1.py"):
        cmd = [
            str(REPO_ROOT / "scripts/pt"),
            script,
            "--state-root",
            str(reserved / "runtime_state" / "ranking"),
            "--universe-snapshot-json",
            str(instruments),
        ]
    else:
        cmd = [
            str(REPO_ROOT / "scripts/pt"),
            script,
            "--state-root",
            str(reserved / "runtime_state" / "selection"),
            "--ranking-snapshot-json",
            str(ranking),
        ]
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert FAILURE_RESERVED_CAP24_PRODUCTIVITY_ROOT in proc.stdout + proc.stderr


@pytest.mark.parametrize(
    "script",
    [
        "scripts/ops/run_governed_futures_universe_producer_v1.py",
        "scripts/ops/run_productive_futures_ranking_producer_v1.py",
        "scripts/ops/run_single_selected_future_policy_v1.py",
    ],
)
def test_capability_cli_allows_non_reserved_root(tmp_path: Path, script: str) -> None:
    state_root = tmp_path / "standalone_capability_root"
    state_root.mkdir()
    instruments = _instruments_json(tmp_path)
    ranking = _ranking_snapshot_json(tmp_path)
    if script.endswith("run_governed_futures_universe_producer_v1.py"):
        cmd = [
            str(REPO_ROOT / "scripts/pt"),
            script,
            "--state-root",
            str(state_root),
            "--instruments-json",
            str(instruments),
        ]
    elif script.endswith("run_productive_futures_ranking_producer_v1.py"):
        uni_root = tmp_path / "uni"
        uni_root.mkdir()
        from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
            run_governed_futures_universe_producer_v1,
        )

        run_governed_futures_universe_producer_v1(
            state_root=uni_root,
            source_payload=json.loads(instruments.read_text(encoding="utf-8")),
            repository_sha=BASE_SHA,
            producer_observed_at_unix=1_700_000_100.0,
        )
        cmd = [
            str(REPO_ROOT / "scripts/pt"),
            script,
            "--state-root",
            str(state_root),
            "--universe-state-root",
            str(uni_root),
        ]
    else:
        rank_root = tmp_path / "rank"
        rank_root.mkdir()
        from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
            run_productive_futures_ranking_producer_v1,
        )

        uni_root = tmp_path / "uni_for_sel"
        uni_root.mkdir()
        from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
            run_governed_futures_universe_producer_v1,
        )

        run_governed_futures_universe_producer_v1(
            state_root=uni_root,
            source_payload=json.loads(instruments.read_text(encoding="utf-8")),
            repository_sha=BASE_SHA,
            producer_observed_at_unix=1_700_000_100.0,
        )
        run_productive_futures_ranking_producer_v1(
            state_root=rank_root,
            universe_state_root=uni_root,
            repository_sha=BASE_SHA,
            producer_observed_at_unix=1_700_000_100.0,
        )
        cmd = [
            str(REPO_ROOT / "scripts/pt"),
            script,
            "--state-root",
            str(state_root),
            "--ranking-state-root",
            str(rank_root),
        ]
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode in {0, 2}
    assert FAILURE_RESERVED_CAP24_PRODUCTIVITY_ROOT not in proc.stdout + proc.stderr
