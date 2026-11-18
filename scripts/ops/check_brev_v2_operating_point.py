#!/usr/bin/env python3
"""Inspect the three BREV V2 operating slices without opening runtime ports."""

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sqlite3
import time

from scripts.ops import brev_v2_mac_host_service as mac
from scripts.ops.run_offline_occupied_brev_with_cap24_v1 import (
    _ConfirmationError,
    inspect_occupied_brev_cap24_v1,
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
        raw = manifest.read_bytes()
        value = json.loads(raw)
        if value["schema"] != mac.SCHEMA:
            raise ValueError()
        sandbox, bounds, env = mac._manifest_inputs(value)
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        operating["blockers"].append("V2_MANIFEST_INVALID")
        return report
    report["manifest_sha256"] = sha256(raw).hexdigest()
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--post-binding", type=Path)
    args = parser.parse_args(argv)
    result = inspect_operating_point(args.manifest, args.post_binding)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 75 if any(item["blockers"] for item in result["slices"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
