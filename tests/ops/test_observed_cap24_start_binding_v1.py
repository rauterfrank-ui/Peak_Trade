"""Offline integration tests against persisted original universe/ranking contracts."""

from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from tests.ops.test_full_core_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    REPO_SHA,
    _build_fresh_chain,
    _materialize_productivity_root,
)

from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 as component,
)

Error = component.CurrentProductive29PCap24ProvenanceHandoffError


def tree_bytes(root):
    return {
        str(p.relative_to(root)): (
            p.is_dir(),
            None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest(),
        )
        for p in root.rglob("*")
    }


@pytest.fixture
def state(tmp_path):
    chain = _build_fresh_chain(tmp_path / "source", repository_sha=REPO_SHA)
    prod = _materialize_productivity_root(tmp_path, chain)
    return chain, prod


def kwargs(state):
    chain, prod = state
    return dict(
        productivity_root=prod, repository_sha=REPO_SHA, binding_epoch=chain["binding_epoch"]
    )


def observed(state, **changes):
    chain, _ = state
    ts = component._binding_epoch_unix_v1(chain["binding_epoch"])
    return replace(
        PortfolioTruthSnapshotV1(
            source_id="injected_private_observation", event_time_unix=ts, wall_time_unix=ts
        ),
        **changes,
    )


def test_inspection_has_no_writes_or_admission(state):
    _, prod = state
    before = tree_bytes(prod)
    with patch.object(
        component,
        "run_single_selected_future_runtime_binding_gate_v1",
        side_effect=AssertionError("stateful gate called"),
    ):
        result = component.inspect_selection_v1(**kwargs(state))
    assert tree_bytes(prod) == before
    assert result.selection.selection_id == state[0]["selection"].selection_id
    assert not hasattr(result, "bound_instrument")
    assert not hasattr(result, "alpha_enabled")
    with pytest.raises(TypeError):
        result.mark_prices["other"] = "1"


@pytest.mark.parametrize(
    "mode",
    [
        "missing_manifest",
        "wrong_manifest_sha",
        "wrong_manifest_selection",
        "wrong_repo",
        "expired_epoch",
        "missing_marks",
    ],
)
def test_inspection_rejects_invalid_provenance_without_writes(state, mode):
    _, prod = state
    values = kwargs(state)
    manifest = prod / component.CAP24_PUBLISH_MANIFEST_FILENAME
    if mode == "missing_manifest":
        manifest.unlink()
    elif mode.startswith("wrong_manifest"):
        payload = json.loads(manifest.read_text())
        key = "repository_sha" if mode.endswith("sha") else "cap23_selection_decision_id"
        payload[key] = "invalid"
        manifest.write_text(json.dumps(payload))
    elif mode == "wrong_repo":
        values["repository_sha"] = "f" * 40
    elif mode == "expired_epoch":
        values["binding_epoch"] = "2099-01-01T00:00:00Z"
    else:
        (prod / "mark_prices_by_native_id_v1.json").unlink()
    before = tree_bytes(prod)
    with pytest.raises(Error):
        component.inspect_selection_v1(**values)
    assert tree_bytes(prod) == before


@pytest.mark.parametrize("side,quantity", [("LONG", "2"), ("SHORT", "-2"), ("FLAT", "0")])
def test_exact_observation_forwarded_not_replaced(state, side, quantity):
    position = PositionTruthV1.from_signed(
        instrument_id=state[0]["instrument_id"],
        signed_quantity=Decimal(quantity),
        source_id="injected",
    )
    snapshot = observed(state, positions=(position,))
    sentinel = object()
    with patch.object(
        component, "run_single_selected_future_runtime_binding_gate_v1", return_value=sentinel
    ) as gate:
        result = component.bind_observed_selection_v1(
            **kwargs(state), session_id="restart-1", observed_portfolio=snapshot
        )
    assert result is sentinel
    assert gate.call_args.kwargs["observed_portfolio"] is snapshot
    assert snapshot.positions[0].side == side
    assert gate.call_args.kwargs["skip_reconciliation"] is False
    assert gate.call_args.kwargs["require_position_truth_if_open_claimed"] is True


@pytest.mark.parametrize("value", [None, {}, "FLAT"])
def test_missing_observation_cannot_mutate(state, value):
    before = tree_bytes(state[1])
    with pytest.raises(TypeError, match="OBSERVED_PORTFOLIO_REQUIRED"):
        component.bind_observed_selection_v1(
            **kwargs(state), session_id="restart", observed_portfolio=value
        )
    assert tree_bytes(state[1]) == before


def test_omitting_observation_is_an_error(state):
    with pytest.raises(TypeError):
        component.bind_observed_selection_v1(**kwargs(state), session_id="restart")


@pytest.mark.parametrize("flag", ["missing", "stale", "duplicate", "writer_conflict"])
def test_real_gate_keeps_bad_observation_blocked(state, flag):
    result = component.bind_observed_selection_v1(
        **kwargs(state), session_id="restart", observed_portfolio=observed(state, **{flag: True})
    )
    assert result.ok is False
    assert result.alpha_enabled is False


def test_real_gate_flat_observation_and_repeat_keep_selection(state):
    chain, prod = state
    before_selection = tree_bytes(prod / "runtime_state" / "selection")
    snapshot = observed(state)
    for session in ("restart-a", "restart-b"):
        result = component.bind_observed_selection_v1(
            **kwargs(state), session_id=session, observed_portfolio=snapshot
        )
        assert result.ok is True, result.blockers
        assert result.bound.instrument_id == chain["instrument_id"]
    assert tree_bytes(prod / "runtime_state" / "selection") == before_selection


def test_gate_reloads_state_instead_of_using_old_inspection(state):
    component.inspect_selection_v1(**kwargs(state))
    manifest = state[1] / component.CAP24_PUBLISH_MANIFEST_FILENAME
    manifest.unlink()
    before = tree_bytes(state[1])
    with pytest.raises(Error, match="CAP24_PUBLISH_MANIFEST_REQUIRED"):
        component.bind_observed_selection_v1(
            **kwargs(state), session_id="restart", observed_portfolio=observed(state)
        )
    assert tree_bytes(state[1]) == before


@pytest.mark.parametrize("quantity", ["2", "-2"])
def test_real_gate_preserves_matching_open_position(state, quantity):
    from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
        PORTFOLIO_STATE_FILENAME,
    )
    from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
        load_persisted_portfolio_state,
    )

    chain, prod = state
    position = PositionTruthV1.from_signed(
        instrument_id=chain["instrument_id"],
        signed_quantity=quantity,
        source_id="injected_private_observation",
    )
    snapshot = observed(state, positions=(position,))
    recon = prod / "runtime_state" / "recon"
    (recon / PORTFOLIO_STATE_FILENAME).write_text(json.dumps(snapshot.to_dict()))
    before = tree_bytes(prod / "runtime_state" / "selection")
    result = component.bind_observed_selection_v1(
        **kwargs(state), session_id="restart-open", observed_portfolio=snapshot
    )
    assert result.reconciliation_result["classification"] == "MATCH"
    restored = load_persisted_portfolio_state(recon, require_present=True)
    assert len(restored.positions) == 1
    assert restored.positions[0].signed_quantity == Decimal(quantity)
    assert restored.positions[0].instrument_id == chain["instrument_id"]
    assert tree_bytes(prod / "runtime_state" / "selection") == before


@pytest.mark.parametrize("quantity", ["2", "-2"])
def test_real_gate_unknown_open_obligation_cannot_become_flat(state, quantity):
    chain, _ = state
    position = PositionTruthV1.from_signed(
        instrument_id=chain["instrument_id"],
        signed_quantity=quantity,
        source_id="injected_private_observation",
    )
    result = component.bind_observed_selection_v1(
        **kwargs(state),
        session_id="restart-unknown",
        observed_portfolio=observed(state, positions=(position,)),
    )
    assert result.ok is False
    assert result.alpha_enabled is False
