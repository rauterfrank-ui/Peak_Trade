#!/usr/bin/env python3
"""Inspect the three BREV V2 operating slices without opening runtime ports."""

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sqlite3
import subprocess
import time

from scripts.ops import brev_v2_mac_host_service as mac
from scripts.ops.run_offline_occupied_brev_with_cap24_v1 import (
    _ConfirmationError,
    inspect_brev_cap24_publication_v1,
    inspect_occupied_brev_cap24_v1,
    inspect_occupied_brev_wait_v1,
)
from src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 import (
    resolve_canonical_f1_m9_productive_apply_ledger_paths_v1,
    resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    GovernedF1M9ThresholdConsumerWiringRequestV1,
    run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
    PostOwnerAuthorityStoreV1,
    SharedPostOwnerAuthorityError,
)
from src.ops.gates.risk_gate import canonical_kill_switch_state_path
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    CurrentProductive29PCap24ProvenanceHandoffError,
)


def _check_post_binding(path, account):
    value = json.loads(path.read_bytes())
    if (
        value.keys()
        != {
            "account",
            "store",
            "store_id",
            "issuer_id",
            "verify_key",
            "checkpoint",
            "binding_sha256",
        }
        or value["account"] != account
    ):
        raise ValueError("POST_BINDING_SCOPE_MISMATCH")
    store = PostOwnerAuthorityStoreV1(
        path=mac._absolute_path(value["store"]),
        store_id=value["store_id"],
        issuer_id=value["issuer_id"],
        verify_key=bytes.fromhex(value["verify_key"]),
        checkpoint_path=mac._absolute_path(value["checkpoint"]),
    )
    current = store.binding_digest_v1()
    if current != value["binding_sha256"]:
        raise SharedPostOwnerAuthorityError("POST_GRANT_STORE_BINDING_MISMATCH")
    return current


def _read_manifest(manifest):
    raw = manifest.read_bytes()
    value = json.loads(raw)
    if value["schema"] != mac.SCHEMA:
        raise ValueError("V2_MANIFEST_INVALID")
    sandbox, bounds, env = mac._manifest_inputs(value)
    return value, sandbox, bounds, env, sha256(raw).hexdigest()


def _inspect_f1_m9(operating):
    try:
        paths = GovernedF1M9ThresholdConsumerWiringRequestV1(
            resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=mac.REPO),
            resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1(
                repo_root=mac.REPO
            ),
            mac.REPO,
        )
        f1m9 = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
            paths
        )
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        operating["blockers"].append("F1_M9_CONSUMER_WIRING_UNPROVEN")
    else:
        operating["f1_m9"] = f1m9.to_dict()
        if f1m9.status != "CONTINUATION_COMPLETE":
            operating["blockers"].append("F1_M9_CONSUMER_WIRING_UNPROVEN")


def inspect_operating_point(manifest: Path, post_binding: Path | None = None) -> dict:
    operating = {"blockers": []}
    restart = {"blockers": ["MAC_SERVICE_START_AND_RESTART_UNPROVEN"]}
    post = {"blockers": ["V2_POST_PORT_NOT_CONNECTED", "ORDER_RECOVERY_AT_MAC_UNPROVEN"]}
    report = {
        "schema": "peaktrade.brev_v2_operating_point_inspection.v1",
        "instrument": "BREV-USDT-SWAP",
        "lane": "LANE_1",
        "runtime_authorization_effect": "NONE",
        "slices": {"operating_point": operating, "restart": restart, "post": post},
    }
    try:
        value, sandbox, bounds, env, manifest_digest = _read_manifest(manifest)
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        operating["blockers"].append("V2_MANIFEST_INVALID")
        return report
    report["manifest_sha256"] = manifest_digest
    report["checkout_sha"] = value["checkout_sha"]
    report["manifest_mode"] = value["mode"]
    if value["mode"] == "offline_replay":
        operating["blockers"].append("OFFLINE_REPLAY_TEST_ONLY")
    else:
        try:
            mac._require_governed_start(value)
        except mac._HostRefusal as exc:
            operating["blockers"].append(str(exc))
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            operating["blockers"].append("OWNER_GO_INPUT_UNPROVEN")
    filegate = Path(env[mac.FILEGATE_ENV])
    if (
        any(os.environ.get(key) != env.get(key) for key in (mac.FILEGATE_ENV, mac.ROOT_ENV))
        or not filegate.is_file()
        or not mac._filegate_revision(filegate)
    ):
        operating["blockers"].append("CANONICAL_FILEGATE_UNPROVEN")
    _inspect_f1_m9(operating)

    if time.time() >= bounds.expires_at_unix:
        restart["blockers"].append("MANIFEST_WINDOW_EXPIRED")
    if (sandbox / "occupied-n1-v2" / "STOP").exists():
        restart["blockers"].append("HOST_STOP_REQUESTED")
    try:
        cap24 = value["cap24"]
        wait = inspect_occupied_brev_cap24_v1(
            sandbox_root=sandbox,
            runtime_config=value["runtime_request_config"],
            cap24_productivity_root=Path(cap24["productivity_root"]),
            cap24_repository_sha=cap24["repository_sha"],
            cap24_publication_sha256=cap24["publication_sha256"],
        )
    except (_ConfirmationError, CurrentProductive29PCap24ProvenanceHandoffError) as exc:
        restart["blockers"].append(str(exc))
    except (AttributeError, KeyError, OSError, OverflowError, TypeError, ValueError, sqlite3.Error):
        restart["blockers"].append("CAP24_OR_ORIGINAL_WAIT_UNPROVEN")
    else:
        if wait.binding != bounds.runtime_config_digest:
            restart["blockers"].append("HOST_BREV_V2_RUNTIME_DIGEST_MISMATCH")
        if type(wait.deadline) not in {int, float} or not math.isfinite(wait.deadline):
            restart["blockers"].append("ORIGINAL_WAIT_DEADLINE_UNPROVEN")
        elif time.time() >= wait.deadline:
            restart["blockers"].append("ORIGINAL_WAIT_WINDOW_EXPIRED")
        restart["wait_check"] = {
            "publication_sha256": wait.confirmation["publication_sha256"],
            "checkpoint_sha256": wait.checkpoint_sha256,
            "cursor_sha256": wait.confirmation["occupied_cursor_sha256"],
        }

    if post_binding is None:
        post["blockers"].append("POST_ISSUER_AND_STORE_UNBOUND")
    else:
        try:
            post["shared_store_binding_sha256"] = _check_post_binding(
                post_binding, value["runtime_request_config"]["expected_account_identity"]
            )
        except SharedPostOwnerAuthorityError as exc:
            post["blockers"].append(str(exc))
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            post["blockers"].append("POST_BINDING_INPUT_UNPROVEN")
    return report


def _inspect_start_governance(governance, env):
    blockers = governance["blockers"]
    try:
        target = subprocess.check_output(
            ["git", "-C", str(mac.REPO), "rev-parse", "--verify", "origin/main^{commit}"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        target = None
        blockers.append("ORIGIN_MAIN_REVISION_UNPROVEN")
    if target is not None:
        governance["target_revision"] = target
        try:
            mac._require_checkout(target)
        except mac._HostRefusal as exc:
            blockers.append(str(exc))
        try:
            owner_go, reasons = mac.validate_bounded_continuous_run_owner_go_decision_v1(
                repo_root=mac.REPO, baseline_origin_main_sha=target
            )
            if not owner_go:
                blockers.extend(reasons)
            if not mac.standing_continuous_run_authorized_v1(repo_root=mac.REPO):
                blockers.append("HOST_BREV_V2_STANDING_POLICY_DENIED")
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            blockers.append("OWNER_GO_INPUT_UNPROVEN")

    if env is None:
        filegate = Path(canonical_kill_switch_state_path()).resolve()
    else:
        filegate = Path(env[mac.FILEGATE_ENV])
    filegate_revision = mac._filegate_revision(filegate)
    if (
        not filegate_revision
        or filegate_revision == "UNCONFIGURED"
        or (
            env is not None
            and any(os.environ.get(key) != env.get(key) for key in (mac.FILEGATE_ENV, mac.ROOT_ENV))
        )
    ):
        blockers.append("CANONICAL_FILEGATE_UNPROVEN")
    else:
        governance["filegate_sha256"] = filegate_revision
    _inspect_f1_m9(governance)
    return target


def _inspect_start_episode(episode, sandbox, config, bounds, now):
    blockers = episode["blockers"]
    try:
        wait = inspect_occupied_brev_wait_v1(sandbox_root=sandbox, runtime_config=config)
    except _ConfirmationError as exc:
        blockers.append(str(exc))
    except (AttributeError, KeyError, OSError, OverflowError, TypeError, ValueError, sqlite3.Error):
        blockers.append("ORIGINAL_BREV_WAIT_UNPROVEN")
    else:
        if wait.binding != bounds.runtime_config_digest:
            blockers.append("HOST_BREV_V2_RUNTIME_DIGEST_MISMATCH")
        if type(wait.deadline) not in {int, float} or not math.isfinite(wait.deadline):
            blockers.append("ORIGINAL_WAIT_DEADLINE_UNPROVEN")
        elif now >= wait.deadline:
            blockers.append("ORIGINAL_WAIT_WINDOW_EXPIRED")
        episode["checkpoint_sha256"] = wait.checkpoint_sha256
        episode["cursor_sha256"] = wait.confirmation["occupied_cursor_sha256"]


def _inspect_start_cap24(start, cap24, config, now):
    try:
        publication = inspect_brev_cap24_publication_v1(
            original_productivity_root=mac._absolute_path(
                config["roots"]["cap24_productivity_root"]
            ),
            instrument_id=config["bound"]["instrument_id"],
            cap24_productivity_root=Path(cap24["productivity_root"]),
            cap24_repository_sha=cap24["repository_sha"],
            cap24_publication_sha256=cap24["publication_sha256"],
            replay_clock=lambda: now,
        )
    except (_ConfirmationError, CurrentProductive29PCap24ProvenanceHandoffError) as exc:
        start["blockers"].append(str(exc))
    except (AttributeError, KeyError, OSError, OverflowError, TypeError, ValueError, sqlite3.Error):
        start["blockers"].append("CAP24_PUBLICATION_UNPROVEN")
    else:
        start["publication_sha256"] = publication.confirmation["publication_sha256"]
        start["selection_valid_until"] = publication.valid_until


def inspect_start_inputs(manifest: Path | None) -> dict:
    """Inspect the three V2 start prerequisites without starting the host."""
    episode, governance, start = ({"blockers": []} for _ in range(3))
    report = {
        "schema": "peaktrade.brev_v2_start_input_inspection.v1",
        "instrument": "BREV-USDT-SWAP",
        "lane": "LANE_1",
        "runtime_authorization_effect": "NONE",
        "slices": {
            "original_episode": episode,
            "owner_go_and_filegate": governance,
            "cap24_and_manifest": start,
        },
    }
    inputs = None
    if manifest is not None:
        try:
            inputs = _read_manifest(manifest)
        except FileNotFoundError:
            pass
        except (AttributeError, KeyError, OSError, OverflowError, TypeError, ValueError):
            start["blockers"].append("V2_MANIFEST_INVALID")

    target = _inspect_start_governance(governance, inputs[3] if inputs else None)
    if inputs is None:
        episode["blockers"].append("ORIGINAL_BREV_WAIT_INPUT_REQUIRED")
        if not start["blockers"]:
            start["blockers"].append("V2_MANIFEST_REQUIRED")
        start["blockers"].append("CAP24_PUBLICATION_INPUT_REQUIRED")
        return report

    value, sandbox, bounds, _, manifest_digest = inputs
    now = time.time()
    start.update(manifest_sha256=manifest_digest, manifest_mode=value["mode"])
    if value["mode"] == "offline_replay":
        start["blockers"].append("OFFLINE_REPLAY_TEST_ONLY")
    if target != value["checkout_sha"] or target != bounds.repository_sha:
        start["blockers"].append("HOST_BREV_V2_START_REVISION_MISMATCH")
    if target != value["cap24"]["repository_sha"]:
        start["blockers"].append("CAP24_START_REVISION_MISMATCH")
    if now >= bounds.expires_at_unix:
        start["blockers"].append("MANIFEST_WINDOW_EXPIRED")
    if (sandbox / "occupied-n1-v2" / "STOP").exists():
        start["blockers"].append("HOST_STOP_REQUESTED")

    config = value["runtime_request_config"]
    _inspect_start_episode(episode, sandbox, config, bounds, now)
    _inspect_start_cap24(start, value["cap24"], config, now)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--post-binding", type=Path)
    parser.add_argument("--start-readiness", action="store_true")
    args = parser.parse_args(argv)
    if args.start_readiness:
        if args.post_binding is not None:
            parser.error("--post-binding is for the operating-point report")
        result = inspect_start_inputs(args.manifest)
    else:
        if args.manifest is None:
            parser.error("--manifest is required unless --start-readiness is selected")
        result = inspect_operating_point(args.manifest, args.post_binding)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 75 if any(item["blockers"] for item in result["slices"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
