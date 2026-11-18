"""Confirm a new Cap24 publication before resuming the original BREV V2 WAIT.

The existing WAIT hashes the runtime source tree. This offline operations
entrypoint leaves that tree and the original request binding intact.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import time

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    LOCK_NAME,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    CAP24_PUBLISH_MANIFEST_FILENAME,
    CurrentProductive29PCap24ProvenanceHandoffError,
    inspect_selection_v1,
)
from src.ops.n1_occupied_scope_recovery_v2.checkpoint import verify_occupied_wait_checkpoint_v1
from src.ops.n1_occupied_scope_recovery_v2.runtime import (
    CHECKPOINT_FILENAME,
    _native_wait,
    run_offline_occupied_n1_v2,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.startup_factory_v1 import (
    _prepare_occupied_n1_request,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    budget_owner_root_for_config_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    unattended_request_digest_v1,
)


_OWNER = "n1_occupied_scope_recovery_v2"
_LANE = "LANE_1"
_NATIVE = "BREV-USDT-SWAP"


class _ConfirmationError(ValueError):
    """An expected refusal before opening replay ports."""


def _require(condition, reason):
    if not condition:
        raise _ConfirmationError(reason)


def _epoch(clock):
    return datetime.fromtimestamp(clock(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path):
    _require(path.resolve() == path, "BREV_CAP24_NONCANONICAL_PATH")
    raw = path.read_bytes()
    return json.loads(raw), sha256(raw).hexdigest()


@dataclass(frozen=True)
class BrevCap24WaitV1:
    publication: Path
    lock_path: Path
    attempt: int
    checkpoint: Path
    checkpoint_sha256: str
    binding: str
    deadline: float | None
    valid_until: str
    confirmation: dict


def inspect_occupied_brev_cap24_v1(
    *,
    sandbox_root: Path,
    runtime_config: dict,
    cap24_productivity_root: Path,
    cap24_repository_sha: str,
    cap24_publication_sha256: str,
    replay_clock=time.time,
) -> BrevCap24WaitV1:
    """Verify the original WAIT and current Cap24 publication without opening ports."""
    root = Path(sandbox_root)
    cap24_root = Path(cap24_productivity_root)
    _require(root.resolve() == root and root.is_dir(), "BREV_CAP24_REPLAY_ROOT_REQUIRED")
    _require(
        cap24_root.resolve() == cap24_root
        and re.fullmatch(r"[0-9a-f]{40}", cap24_repository_sha)
        and re.fullmatch(r"[0-9a-f]{64}", cap24_publication_sha256),
        "BREV_CAP24_EXPLICIT_PUBLICATION_REQUIRED",
    )
    state_root = root / "occupied-n1-v2"
    prepared = _prepare_occupied_n1_request(
        attempt_index=1, evidence_root=state_root, runtime_config=runtime_config
    )
    request = prepared.request
    config, bound = request["config"], request["bound"]
    _require(bound.venue_native_id == _NATIVE, "BREV_CAP24_OCCUPIED_INSTRUMENT_REQUIRED")
    _require(
        cap24_root != config.cap24_productivity_root,
        "BREV_CAP24_SEPARATE_PUBLICATION_REQUIRED",
    )
    publication = cap24_root / CAP24_PUBLISH_MANIFEST_FILENAME
    published, publication_digest = _read(publication)
    _require(publication_digest == cap24_publication_sha256, "BREV_CAP24_PUBLICATION_CHANGED")
    binding_epoch = _epoch(replay_clock)
    decision_time = datetime.fromisoformat(published["decision_epoch"].replace("Z", "+00:00"))
    binding_time = datetime.fromisoformat(binding_epoch.replace("Z", "+00:00"))
    _require(
        decision_time.utcoffset() is not None and decision_time <= binding_time,
        "BREV_CAP24_PUBLICATION_FROM_FUTURE",
    )
    fresh = inspect_selection_v1(
        productivity_root=cap24_root,
        repository_sha=cap24_repository_sha,
        binding_epoch=binding_epoch,
    ).selection
    _require(
        (fresh.instrument_id, fresh.venue_native_id) == (bound.instrument_id, _NATIVE),
        "BREV_CAP24_FOREIGN_INSTRUMENT",
    )

    lock_path = config.lock_root / LOCK_NAME
    cursor_root = config.lane_state_root / _LANE
    budget_root = budget_owner_root_for_config_v1(config) / "owner"
    _require(
        all(path.is_relative_to(root) for path in (lock_path, cursor_root, budget_root)),
        "BREV_CAP24_OCCUPIED_ROOT_OUTSIDE_REPLAY",
    )
    binding = unattended_request_digest_v1(prepared)
    prior, lock_digest = _read(lock_path)
    context = prior["recovery_context"]
    attempt = context["attempt"]
    _require(
        prior["owner"] == _OWNER
        and context["binding"] == binding
        and context["state_root"] == str(state_root)
        and type(attempt) is int
        and attempt > 0,
        "BREV_CAP24_OCCUPIED_REQUEST_CHANGED",
    )
    attempt_root = state_root / "attempts" / str(attempt)
    checkpoint_path = attempt_root / CHECKPOINT_FILENAME
    checkpoint, checkpoint_digest = _read(checkpoint_path)
    store = (budget_root / "reservations.sqlite3").stat()
    store_identity = [store.st_dev, store.st_ino]
    scope = checkpoint["scope"]
    position = scope["position"]
    _require(
        checkpoint["schema"] == _OWNER
        and checkpoint["binding"] == binding
        and checkpoint["repository_sha"] == request["origin_main_sha"]
        and checkpoint["outer_lock_sha256"] == lock_digest
        and checkpoint["store_identity"] == store_identity
        and position["bound"] == bound.to_dict(),
        "BREV_CAP24_OCCUPIED_CHECKPOINT_CHANGED",
    )
    try:
        wait = _native_wait(attempt_root, cursor_root=cursor_root, lock=prior, native_id=_NATIVE)
    except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
        raise _ConfirmationError("BREV_CAP24_ORIGINAL_WAIT_UNPROVEN") from exc
    _require(
        wait == checkpoint["native_wait"]
        and verify_occupied_wait_checkpoint_v1(
            scope,
            cursor_root=cursor_root,
            budget_root=budget_root,
            account=config.expected_account_identity,
            native_id=_NATIVE,
        ),
        "BREV_CAP24_ORIGINAL_WAIT_UNPROVEN",
    )

    return BrevCap24WaitV1(
        publication=publication,
        lock_path=lock_path,
        attempt=attempt,
        checkpoint=checkpoint_path,
        checkpoint_sha256=checkpoint_digest,
        binding=binding,
        deadline=context.get("deadline"),
        valid_until=fresh.valid_until,
        confirmation={
            "repository_sha": cap24_repository_sha,
            "publication_sha256": publication_digest,
            "binding_epoch": binding_epoch,
            "selection_id": fresh.selection_id,
            "occupied_selection_id": bound.selection_id,
            "occupied_checkpoint_sha256": checkpoint_digest,
            "occupied_store_identity": store_identity,
            "occupied_budget_revision": scope["budget_revision"],
            "occupied_reservation_id": position["reservation_id"],
            "occupied_cursor_sha256": wait["cursor_sha256"],
        },
    )


def run_offline_occupied_brev_with_cap24_v1(
    *,
    sandbox_root: Path,
    runtime_config: dict,
    expires_at_unix: float,
    cap24_productivity_root: Path,
    cap24_repository_sha: str,
    cap24_publication_sha256: str,
    open_fixture_ports,
    replay_clock=time.time,
    sleep=time.sleep,
):
    """Resume an occupied replay after independently checking the fresh Cap24 selection.

    The caller pins the additional publication by repository SHA and manifest digest.
    The original runtime request and fixture port contract are passed through to V2.
    """
    try:
        _require(callable(open_fixture_ports), "BREV_CAP24_EXPLICIT_PUBLICATION_REQUIRED")
        admitted = inspect_occupied_brev_cap24_v1(
            sandbox_root=sandbox_root,
            runtime_config=runtime_config,
            cap24_productivity_root=cap24_productivity_root,
            cap24_repository_sha=cap24_repository_sha,
            cap24_publication_sha256=cap24_publication_sha256,
            replay_clock=replay_clock,
        )
    except (_ConfirmationError, CurrentProductive29PCap24ProvenanceHandoffError) as exc:
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": str(exc)}
    except (AttributeError, KeyError, OSError, OverflowError, TypeError, ValueError, sqlite3.Error):
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": "BREV_CAP24_INPUT_UNPROVEN"}

    def confirmed_ports(authorization):
        try:
            claim, _ = _read(admitted.lock_path)
            claimed = claim["recovery_context"]
            current_checkpoint_digest = _read(admitted.checkpoint)[1]
            current_publication_digest = _read(admitted.publication)[1]
            current_epoch = _epoch(replay_clock)
            same_claim = (
                claim["owner"] == _OWNER
                and claimed["binding"] == admitted.binding
                and claimed["attempt"] == admitted.attempt + 1
            )
        except (KeyError, OSError, OverflowError, TypeError, ValueError) as exc:
            raise _ConfirmationError("BREV_CAP24_INPUT_UNPROVEN") from exc
        _require(
            same_claim and current_checkpoint_digest == admitted.checkpoint_sha256,
            "BREV_CAP24_OCCUPIED_CHECKPOINT_CHANGED",
        )
        _require(
            current_publication_digest == admitted.confirmation["publication_sha256"],
            "BREV_CAP24_PUBLICATION_CHANGED",
        )
        _require(current_epoch <= admitted.valid_until, "SELECTION_STALE_FOR_BINDING_EPOCH")
        return open_fixture_ports(authorization)

    try:
        result = run_offline_occupied_n1_v2(
            sandbox_root=Path(sandbox_root),
            runtime_config=runtime_config,
            expires_at_unix=expires_at_unix,
            open_fixture_ports=confirmed_ports,
            replay_clock=replay_clock,
            sleep=sleep,
        )
    except _ConfirmationError as exc:
        return {"status": "RECOVERY_CHECKPOINT_REQUIRED", "reason": str(exc)}
    return {**result, "cap24_confirmation": admitted.confirmation}
