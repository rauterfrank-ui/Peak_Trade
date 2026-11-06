"""No inferred genesis: expected account, explicit bootstrap and stable recovery."""

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorConfigV1,
    StandingSupervisorError,
    budget_owner_root_for_config_v1,
    run_n1_standing_pre_external_supervisor_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from tests.ops.test_durable_portfolio_budget_recovery_v1 import (
    ACCOUNT,
    BINDINGS,
    EPOCH,
    NOW,
    _produce,
    _reserve,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch


def _open(root, *, mode="recover", account=ACCOUNT, fetch=None, session="session-one"):
    return PortfolioBudgetHostV1(
        root=root,
        private_rest_fetch=fetch or _fetch(),
        repository_sha="treasury-test-revision",
        session_id=session,
        expected_account_identity=account,
        durable_mode=mode,
        clock=lambda: NOW,
    )


@pytest.mark.parametrize("account", [None, "", " ", " account", "account ", False])
def test_expected_account_is_required_before_any_io(tmp_path, account):
    root = tmp_path / "owner-scope"
    with pytest.raises(ValueError, match="EXPECTED_ACCOUNT_REQUIRED"):
        _open(root, mode="create", account=account)
    assert not root.exists()


def test_recover_missing_root_cannot_create_a_new_budget_or_fetch(tmp_path):
    root = tmp_path / "missing"
    with pytest.raises(ValueError, match="STATE_MISSING"):
        _open(root, fetch=lambda *_: pytest.fail("private fetch before missing-state check"))
    assert not root.exists()


def test_recover_empty_existing_root_does_not_treat_it_as_genesis(tmp_path):
    root = tmp_path / "missing-state"
    root.mkdir()
    host = _open(root)
    try:
        with pytest.raises(ValueError, match="STATE_MISSING"):
            host.observe_v1(BINDINGS)
        assert host.owner is None
        assert list(root.iterdir()) == []
    finally:
        host.close()


def test_first_bootstrap_refuses_another_account_before_creating_state(tmp_path):
    root = tmp_path / "new-scope"
    host = _open(root, mode="create", fetch=_fetch(uid="different-account"))
    try:
        with pytest.raises(ValueError, match="PRIVATE_ACCOUNT_CHANGED"):
            host.observe_v1(BINDINGS)
        assert host.owner is None
        assert not root.exists()
    finally:
        host.close()


def test_lost_observation_cache_cannot_reset_the_configured_account_pin(tmp_path):
    root = tmp_path / "scope"
    host = _open(root, mode="create", fetch=_fetch(uid="different-account"))
    host.account = None
    try:
        with pytest.raises(ValueError, match="PRIVATE_ACCOUNT_CHANGED"):
            host.observe_v1(BINDINGS)
        assert not root.exists()
    finally:
        host.close()


def test_explicit_bootstrap_is_not_a_reopen_mode_and_does_not_grant_capital(tmp_path):
    root = tmp_path / "scope"
    host = _open(root, mode="create")
    try:
        host.observe_v1(BINDINGS)
        assert host.owner.budget_state_v1().recovery_required
        assert not host.owner.budget_state_v1().admitted
        assert host.owner.admitted_budget_v1() == 0
    finally:
        host.close()
    with pytest.raises(ValueError, match="BOOTSTRAP_SCOPE_ALREADY_EXISTS"):
        _open(root, mode="create")


def test_warm_restart_with_new_run_identity_preserves_the_same_holds(tmp_path):
    root = tmp_path / "stable-scope"
    first = _open(root, mode="create", session="attempt-evidence-one")
    try:
        first.observe_v1(BINDINGS).recover_v1(first.owner, _produce(epoch=EPOCH))
        hold = _reserve(first.owner).reservation
        first.owner.commit_internal_pre_external_effect_v1(hold.reservation_id)
    finally:
        first.close()
    restarted = _open(root, session="attempt-evidence-two")
    try:
        ctx = restarted.observe_v1(BINDINGS)
        assert restarted.owner.active_sum_v1() == hold.amount
        assert not restarted.owner.budget_state_v1().admitted
        ctx.recover_v1(restarted.owner, _produce(epoch=EPOCH))
        same = _reserve(restarted.owner).reservation
        assert same.reservation_id == hold.reservation_id
        assert same.amount == hold.amount
        assert same.state.value == "COMMITTED"
        assert restarted.owner.active_sum_v1() == hold.amount
    finally:
        restarted.close()


def test_lost_scope_after_a_real_bootstrap_is_not_silently_recreated(tmp_path):
    root = tmp_path / "stable-scope"
    host = _open(root, mode="create")
    host.observe_v1(BINDINGS)
    host.close()
    retained = tmp_path / "retained-original"
    root.rename(retained)
    with pytest.raises(ValueError, match="STATE_MISSING"):
        _open(root, session="new-evidence-directory")
    assert not root.exists()
    assert (retained / "owner/reservations.sqlite3").is_file()


def _config(tmp_path):
    return StandingSupervisorConfigV1(
        private_store_root=tmp_path / "private",
        public_store_root=tmp_path / "public",
        lane_state_root=tmp_path / "lanes",
        evidence_root=tmp_path / "evidence-one",
        expected_account_identity=ACCOUNT,
    )


def test_evidence_rotation_does_not_change_owner_root(tmp_path):
    config = _config(tmp_path)
    expected = tmp_path / "private/portfolio_budget_host_v1"
    assert budget_owner_root_for_config_v1(config) == expected
    assert (
        budget_owner_root_for_config_v1(replace(config, evidence_root=tmp_path / "evidence-two"))
        == expected
    )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("name", ["evidence_root", "lane_state_root", "public_store_root"])
@pytest.mark.parametrize("direction", ["owner-inside", "other-inside", "same"])
def test_owner_root_cannot_overlap_run_lane_or_public_state(tmp_path, name, direction):
    config = _config(tmp_path)
    owner = config.private_store_root / "portfolio_budget_host_v1"
    other = {
        "owner-inside": config.private_store_root,
        "other-inside": owner / "child",
        "same": owner,
    }[direction]
    config = replace(config, **{name: other})
    with pytest.raises(StandingSupervisorError, match="BUDGET_OWNER_ROOT_OVERLAP"):
        run_n1_standing_pre_external_supervisor_v1(config=config)
    # Wrapper validates before both the runtime and its fault-notice writer.
    assert not list(tmp_path.iterdir())


def test_relative_state_paths_are_not_durable_configuration(tmp_path):
    config = replace(_config(tmp_path), private_store_root=Path("relative-private"))
    with pytest.raises(StandingSupervisorError, match="ABSOLUTE_ROOTS_REQUIRED"):
        budget_owner_root_for_config_v1(config)


def test_symlink_alias_cannot_hide_public_owner_overlap(tmp_path):
    public = tmp_path / "public"
    public.mkdir()
    alias = tmp_path / "private-alias"
    alias.symlink_to(public, target_is_directory=True)
    config = replace(_config(tmp_path), private_store_root=alias)
    with pytest.raises(StandingSupervisorError, match="ROOT_OVERLAP"):
        budget_owner_root_for_config_v1(config)
    assert list(public.iterdir()) == []
