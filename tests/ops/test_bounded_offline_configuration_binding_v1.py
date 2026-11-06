"""Actual imported operands, immutable session generation and fresh-process control."""

import json
from pathlib import Path
import subprocess

import pytest

from src.ops.bounded_peaktrade_system_composition_v1.configuration_v1 import CONFIG_RECEIPT
from tests.ops.test_bounded_offline_episode_session_v1 import _setup, _session


@pytest.mark.parametrize("change", ["alias", "receipt", "missing"])
def test_config_drift_rejects_recovery_without_rewriting_original_session(
    tmp_path, monkeypatch, change
):
    manifest, _ = _setup(tmp_path)
    root = tmp_path / "session"
    with _session(manifest, root):
        pass
    path = root / CONFIG_RECEIPT
    if change == "alias":
        from src.ops.full_core_live_path_composition_root_v1 import (
            current_productive_master_v2_runtime_cycle_v1 as core,
        )

        monkeypatch.setattr(
            core, "CANONICAL_CONFIRMATION_EPOCHS", core.CANONICAL_CONFIRMATION_EPOCHS + 1
        )
    elif change == "receipt":
        row = json.loads(path.read_text())
        row["time_exit_max_hold_seconds"] += 1
        path.write_text(json.dumps(row))
    else:
        path.unlink()
    before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    with pytest.raises(ValueError, match="CONFIG"):
        with _session(manifest, root, "recover"):
            pytest.fail("accepted changed configuration")
    assert {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()} == before


def test_fresh_process_binds_variant_to_actual_core_then_cacheclear_cannot_upgrade_old_alias(
    tmp_path,
):
    repo = Path(__file__).resolve().parents[2]
    script = r"""
from pathlib import Path
import importlib,json,sys
from src.ops.decision_config_ownership_and_consumer_closure_v1 import config_loader_v1 as loader, canonical_values_v1 as values
original=loader.load_canonical_decision_runtime_config_v1()
actual_loader=loader.load_canonical_decision_runtime_config_v1
config_path=Path(sys.argv[1])/'isolated_decision.toml'
def write_variant(epochs):
    payload=original.values_payload();payload.pop('owner');payload['confirmation_epochs']=epochs
    config_path.write_text('[canonical_decision_runtime_config_v1]\n'+'\n'.join(k+' = '+json.dumps(v) for k,v in payload.items())+'\n')
write_variant(original.confirmation_epochs+1)
# Explicit disposable-process path override; original loader parses a real temp
# TOML. Only this isolated test bypasses frozen effective-value parity.
loader.load_canonical_decision_runtime_config_v1=lambda *a,**k:actual_loader(config_path,enforce_frozen_effective_values=False)
variant=loader.load_canonical_decision_runtime_config_v1()
importlib.reload(values)
from src.ops.bounded_peaktrade_system_composition_v1.configuration_v1 import effective_runtime_configuration_v1,CONFIG_RECEIPT
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle
from tests.ops.test_position_episode_exit_continuity_v1 import _bound
from tests.ops.test_simulated_accounting_entry_source_v1 import _history,_args
from tests.ops.test_bounded_offline_episode_session_v1 import _manifest,_session
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import lane_state_root_for
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import persist_current_productive_sidestate_confirmation_cursor_v1
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import create_position_episode_from_simulated_accounting_v1
root=Path(sys.argv[1]); core=Path(lane_state_root_for(topology_state_root_base=root/'lanes',lane_id='LANE_1'))
cursor=None
for step in range(8):
    cycle=_cycle(core,step=step,incoming=cursor)
    assert cycle.replay_pass=='true',cycle.fail_reasons
    cursor=cycle.outgoing_cursor
    assert cursor.confirmation_epochs==variant.confirmation_epochs
    if cycle.decision_outcome=='enter_long': break
assert cycle.decision_outcome=='enter_long'
persist_current_productive_sidestate_confirmation_cursor_v1(cursor,store_root=core)
identity,accounting,fills=_history(); args=_args(root,identity); args['repository_sha']='a'*40
context=create_position_episode_from_simulated_accounting_v1(**args,session=accounting,fills=fills)
source=next((root/'sources').glob('*.json')); manifest=_manifest(context,source,core,_bound())
session_root=root/'session'
with _session(manifest,session_root): pass
with _session(manifest,session_root,'recover'): pass
assert json.loads((session_root/CONFIG_RECEIPT).read_text())['actual_core_confirmation_epochs']==variant.confirmation_epochs
write_variant(variant.confirmation_epochs+1)
variant=loader.load_canonical_decision_runtime_config_v1()
values.clear_canonical_decision_runtime_config_cache_v1()
assert values.get_canonical_decision_runtime_config_v1().confirmation_epochs==variant.confirmation_epochs
try: effective_runtime_configuration_v1()
except ValueError as exc: assert 'IMPORTED_OPERAND_DRIFT' in str(exc)
else: raise AssertionError('cache clear silently upgraded imported consumer')
print('FRESH_PROCESS_ACTUAL_CORE_AND_SESSION_CONFIG_PASS')
"""
    result = subprocess.run(
        [str(repo / "scripts/pt"), "-c", script, str(tmp_path)],
        cwd=repo,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FRESH_PROCESS_ACTUAL_CORE_AND_SESSION_CONFIG_PASS" in result.stdout
