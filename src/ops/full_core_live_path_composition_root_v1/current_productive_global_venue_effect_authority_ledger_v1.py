"""Global one-shot venue-effect authority ledger (store-root independent).

The single-use boundary for a real venue effect is a canonical, persistent,
account- and environment-bound ledger. It never derives from an operator-chosen
``--store-root`` or evidence directory, so switching store roots, sessions,
processes, or checkouts cannot restore a consumed authorization.

Replay identities (create-once markers, never deleted):

- OWNER_AUTHORIZATION_IDENTITY = sha256(owner_go_token, baseline pin, account_scope, environment)
- PERMIT_ID
- ENVELOPE_DIGEST
- VENUE_CLIENT_ORDER_ID

The Owner-GO token is a code constant, so the one-shot authorization unit is the
token together with the code-bound baseline pin (``EXPECTED_BASELINE_ORIGIN_MAIN_SHA``,
enforced against live ``origin/main``). At most one real venue effect exists per
(token, pin, account, environment) regardless of store root; a further effect
needs a new merged pin. A future standing autonomous mandate is not part of this
ledger.

Claim lifecycle (single namespace lock, atomic replace writes):

CLAIMED -> SENT_INITIATED -> COMPLETED_RESPONSE_RECEIVED | UNKNOWN_OUTCOME | ABORTED_BEFORE_TRANSPORT
CLAIMED -> ABORTED_BEFORE_TRANSPORT   (never reached transport; live attempt, or proven unsent)
CLAIMED / SENT_INITIATED / UNKNOWN_OUTCOME -> RECONCILED   (only via G004 adjudication)

UNKNOWN_SUBMISSION_OUTCOME != SAFE_TO_RETRY. CLAIMED alone != PROVEN_NOT_SENT.
Reconciliation clarifies state; it never restores or creates trading authority.

Proven unsent (settled only inside a NEW_RISK ``claim_v1``, under the namespace
lock): a CLAIMED record whose history is exactly [CLAIMED], bound to this host,
written in the current kernel boot session by a process that no longer exists.
SENT_INITIATED is persisted by atomic replace before the pre-send gate reads it
from disk and lets a socket open, and only the claiming process holds the token
needed to write it. Within one boot session the on-disk state is authoritative
even without full-disk durability; once that process is gone no SENT_INITIATED
can ever be written. Any other boot session (possible lost write), an unknown
boot session, or a live/unknown owner process stays unresolved. Replay markers
remain, so the consumed authorization is never reusable.
Unresolved claims block new-risk claims on the same account/environment; they do
not block a separately proven risk reduction under a separate authorization.

Live-attempt binding: ``claim_v1`` issues an in-memory token held only by the
ledger instance that created the claim; its sha256 is persisted. Sending
(``SENT_INITIATED``) and every unresolved-set release other than G004
(``ABORTED_BEFORE_TRANSPORT``, ``COMPLETED_RESPONSE_RECEIVED``) require that
token, so a restarted process or a manual call can only record
``UNKNOWN_OUTCOME`` or go through G004 reconciliation.

Process-level atomicity reuses the CURRENT canary primitives (``flock`` +
``mkstemp`` + ``fsync`` + ``os.replace`` + directory ``fsync``). The ledger root
must be on a filesystem proven local (otherwise fail-closed), and the namespace
is bound to one host identity on first claim (mismatch fail-closed). Separate
hosts with separate ledgers are not detectable here.

Does not POST. Does not GET. RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import ctypes
import ctypes.util
import functools
import hashlib
import json
import os
import secrets
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    FullCoreExchangeReconciliationDecisionV1,
    FullCoreExchangeReconciliationIdentityV1,
    FullCoreExchangeReconciliationSnapshotV1,
    LocalSubmitOutcome,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    AUTHORIZED_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    _atomic_write_state_v1,
    _exclusive_lock_v1,
)

CONTRACT_ID = "CURRENT_PRODUCTIVE_GLOBAL_VENUE_EFFECT_AUTHORITY_LEDGER_V1"
SCHEMA_VERSION = "current_productive_global_venue_effect_authority_ledger.v1"
CANONICAL_LEDGER_DIRNAME = "Peak_Trade_Venue_Effect_Authority_V1"
ENVIRONMENT_LIVE_EEA = f"LIVE@{AUTHORIZED_HOST}"
ACCOUNT_SCOPE_K1 = f"K1:{KEYCHAIN_SERVICE_ID}/{KEYCHAIN_ACCOUNT_ID}"

STATE_CLAIMED = "CLAIMED"
STATE_SENT_INITIATED = "SENT_INITIATED"
STATE_COMPLETED_RESPONSE_RECEIVED = "COMPLETED_RESPONSE_RECEIVED"
STATE_UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
STATE_ABORTED_BEFORE_TRANSPORT = "ABORTED_BEFORE_TRANSPORT"
STATE_RECONCILED = "RECONCILED"
UNRESOLVED_STATES = frozenset({STATE_CLAIMED, STATE_SENT_INITIATED, STATE_UNKNOWN_OUTCOME})
_OUTCOME_STATES = frozenset(
    {STATE_COMPLETED_RESPONSE_RECEIVED, STATE_UNKNOWN_OUTCOME, STATE_ABORTED_BEFORE_TRANSPORT}
)

KIND_OWNER_AUTHORIZATION = "OWNER_AUTHORIZATION_IDENTITY"
KIND_PERMIT = "PERMIT_ID"
KIND_ENVELOPE = "ENVELOPE_DIGEST"
KIND_CLIENT_ORDER_ID = "VENUE_CLIENT_ORDER_ID"
_MARKER_DIRS = {
    KIND_OWNER_AUTHORIZATION: "owner_authorization",
    KIND_PERMIT: "permit",
    KIND_ENVELOPE: "envelope",
    KIND_CLIENT_ORDER_ID: "client_order_id",
}
_MARKER_ORDER = (KIND_OWNER_AUTHORIZATION, KIND_PERMIT, KIND_ENVELOPE, KIND_CLIENT_ORDER_ID)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")
RISK_CLASS_NEW_RISK = "NEW_RISK_ENTER"
RISK_CLASS_RISK_REDUCING = "RISK_REDUCING"
_RELEASING_OUTCOME_STATES = frozenset(
    {STATE_COMPLETED_RESPONSE_RECEIVED, STATE_ABORTED_BEFORE_TRANSPORT}
)
_HOST_BINDING_FILENAME = "host_binding.json"
_DARWIN_MNT_LOCAL = 0x00001000
_DARWIN_LOCAL_FSTYPES = frozenset({"apfs", "hfs"})
# Reboot-persistent local filesystems only: tmpfs loses replay markers on reboot and
# overlayfs upper layers are per container, so both stay denied.
_LINUX_LOCAL_FS_MAGIC = frozenset(
    {
        0xEF53,  # ext2/3/4
        0x58465342,  # xfs
        0x9123683E,  # btrfs
    }
)
CLASS_CLAIMED_ORPHAN = "CLAIMED_ORPHAN_NOT_PROVEN_UNSENT_REQUIRES_G004"
CLASS_CLAIMED_PROVEN_NOT_SENT = "CLAIMED_PROVEN_NOT_SENT_SAME_BOOT_OWNER_GONE"
DETAIL_PROVEN_NOT_SENT = "PROVEN_NOT_SENT:SAME_BOOT_SESSION:OWNER_PROCESS_GONE:NO_SENT_INITIATED"
CLASS_SENT_INITIATED = "SENT_INITIATED_POSSIBLY_SENT_REQUIRES_G004"
CLASS_UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME_POSSIBLY_SENT_REQUIRES_G004"


class GlobalVenueEffectLedgerError(RuntimeError):
    """Fail-closed global ledger violation."""


class GlobalVenueEffectReplayDeniedError(GlobalVenueEffectLedgerError):
    """A replay identity was already consumed (any store root, session, process)."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise GlobalVenueEffectLedgerError(f"SECRET_TOKEN_PRESENT:{token}")


def resolve_canonical_global_ledger_root_v1() -> Path:
    """Fixed per-user ledger root. No env override, no store-root derivation."""
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in sys.modules or "_pytest" in sys.modules:
        raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_CANONICAL_ROOT_FORBIDDEN_UNDER_TEST")
    try:
        home = Path.home()
    except (RuntimeError, OSError) as exc:
        raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_HOME_UNRESOLVED") from exc
    if not home.is_absolute():
        raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_HOME_NOT_ABSOLUTE")
    return (home / CANONICAL_LEDGER_DIRNAME).resolve()


def _nearest_existing_ancestor_v1(path: Path) -> Path:
    candidate = path
    while not candidate.exists():
        if candidate.parent == candidate:
            break
        candidate = candidate.parent
    return candidate


def _darwin_fs_is_local_v1(path: Path) -> bool:
    class _StatfsV1(ctypes.Structure):
        _fields_ = [
            ("f_bsize", ctypes.c_uint32),
            ("f_iosize", ctypes.c_int32),
            ("f_blocks", ctypes.c_uint64),
            ("f_bfree", ctypes.c_uint64),
            ("f_bavail", ctypes.c_uint64),
            ("f_files", ctypes.c_uint64),
            ("f_ffree", ctypes.c_uint64),
            ("f_fsid", ctypes.c_int32 * 2),
            ("f_owner", ctypes.c_uint32),
            ("f_type", ctypes.c_uint32),
            ("f_flags", ctypes.c_uint32),
            ("f_fssubtype", ctypes.c_uint32),
            ("f_fstypename", ctypes.c_char * 16),
            ("f_mntonname", ctypes.c_char * 1024),
            ("f_mntfromname", ctypes.c_char * 1024),
            ("f_reserved", ctypes.c_uint32 * 8),
        ]

    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    try:
        fn = libc["statfs$INODE64"]
    except AttributeError:
        fn = libc.statfs
    buf = _StatfsV1()
    if fn(os.fsencode(str(path)), ctypes.byref(buf)) != 0:
        return False
    fstype = buf.f_fstypename.decode("ascii", "replace")
    return bool(buf.f_flags & _DARWIN_MNT_LOCAL) and fstype in _DARWIN_LOCAL_FSTYPES


def _linux_fs_is_local_v1(path: Path) -> bool:
    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    buf = (ctypes.c_long * 32)()
    if libc.statfs(os.fsencode(str(path)), ctypes.byref(buf)) != 0:
        return False
    return (int(buf[0]) & 0xFFFFFFFF) in _LINUX_LOCAL_FS_MAGIC


def ledger_filesystem_is_proven_local_v1(path: Path | str) -> bool:
    """True only when ``flock`` semantics are those of a known local filesystem."""
    target = _nearest_existing_ancestor_v1(Path(path))
    try:
        if sys.platform == "darwin":
            return _darwin_fs_is_local_v1(target)
        if sys.platform.startswith("linux"):
            return _linux_fs_is_local_v1(target)
    except (OSError, AttributeError, TypeError, ValueError):
        return False
    return False


@functools.lru_cache(maxsize=1)
def _stable_host_identity_v1() -> str:
    """Hardware-bound host identity (macOS IOPlatformUUID / Linux machine-id)."""
    raw = ""
    if sys.platform == "darwin":
        try:
            out = subprocess.run(
                ["/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        for line in out.splitlines():
            if "IOPlatformUUID" in line:
                raw = line.split("=", 1)[-1].strip().strip('"')
                break
    else:
        for candidate in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                raw = Path(candidate).read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if raw:
                break
    if not raw:
        raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_HOST_IDENTITY_UNRESOLVED")
    return _sha256(f"peak_trade_venue_effect_host:{raw}")


@functools.lru_cache(maxsize=1)
def _boot_session_identity_v1() -> str:
    """Current kernel boot session (macOS kern.bootsessionuuid / Linux boot_id); "" if unknown."""
    raw = ""
    if sys.platform == "darwin":
        try:
            raw = subprocess.run(
                ["/usr/sbin/sysctl", "-n", "kern.bootsessionuuid"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            raw = ""
    elif sys.platform.startswith("linux"):
        try:
            raw = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
        except OSError:
            raw = ""
    return _sha256(f"peak_trade_venue_effect_boot:{raw}") if raw else ""


def _process_gone_v1(pid: Any) -> bool:
    """True only when ``pid`` provably names no running process (EPERM counts as alive)."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return False


@dataclass(frozen=True)
class GlobalVenueEffectIdentityV1:
    owner_go_token: str
    account_scope: str
    environment: str
    permit_id: str
    envelope_id: str
    envelope_digest: str
    client_order_id: str
    risk_class: str
    baseline_origin_main_sha: str

    def owner_authorization_identity(self) -> str:
        return _sha256(
            _canonical_json(
                {
                    "owner_go_token": self.owner_go_token.strip(),
                    "baseline_origin_main_sha": self.baseline_origin_main_sha.strip().lower(),
                    "account_scope": self.account_scope.strip(),
                    "environment": self.environment.strip().upper(),
                }
            )
        )

    def marker_keys(self) -> dict[str, str]:
        return {
            KIND_OWNER_AUTHORIZATION: self.owner_authorization_identity(),
            KIND_PERMIT: _sha256(self.permit_id.strip()),
            KIND_ENVELOPE: self.envelope_digest.strip().lower(),
            KIND_CLIENT_ORDER_ID: _sha256(self.client_order_id.strip()),
        }

    def claim_id(self) -> str:
        return _sha256(
            _canonical_json(
                {
                    "owner_authorization_identity": self.owner_authorization_identity(),
                    "permit_id": self.permit_id,
                    "envelope_digest": self.envelope_digest,
                    "client_order_id": self.client_order_id,
                }
            )
        )[:32]

    def validate_v1(self) -> None:
        for name in (
            "owner_go_token",
            "account_scope",
            "environment",
            "permit_id",
            "envelope_id",
            "client_order_id",
            "risk_class",
        ):
            if not str(getattr(self, name) or "").strip():
                raise GlobalVenueEffectLedgerError(f"GLOBAL_IDENTITY_FIELD_MISSING:{name}")
        if len(str(self.envelope_digest or "").strip()) != 64:
            raise GlobalVenueEffectLedgerError("GLOBAL_IDENTITY_ENVELOPE_DIGEST_INVALID")
        sha = str(self.baseline_origin_main_sha or "").strip().lower()
        if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            raise GlobalVenueEffectLedgerError("GLOBAL_IDENTITY_BASELINE_SHA_INVALID")
        if self.risk_class not in {RISK_CLASS_NEW_RISK, RISK_CLASS_RISK_REDUCING}:
            raise GlobalVenueEffectLedgerError("GLOBAL_IDENTITY_RISK_CLASS_INVALID")


@dataclass(frozen=True)
class GlobalVenueEffectClaimV1:
    claim_id: str
    identity: GlobalVenueEffectIdentityV1
    state: str
    ledger_namespace: str


class GlobalVenueEffectAuthorityLedgerV1:
    """Account/environment-bound ledger namespace under a fixed root."""

    def __init__(
        self,
        *,
        root: Path | str | None = None,
        account_scope: str = ACCOUNT_SCOPE_K1,
        environment: str = ENVIRONMENT_LIVE_EEA,
    ) -> None:
        base = (
            Path(root).expanduser()
            if root is not None
            else resolve_canonical_global_ledger_root_v1()
        )
        if not base.is_absolute():
            raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_ROOT_MUST_BE_ABSOLUTE")
        scope = str(account_scope or "").strip()
        env = str(environment or "").strip().upper()
        if not scope or not env:
            raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_SCOPE_REQUIRED")
        if not ledger_filesystem_is_proven_local_v1(base):
            raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_FILESYSTEM_NOT_PROVEN_LOCAL")
        self.account_scope = scope
        self.environment = env
        self.namespace = base.resolve() / "v1" / _sha256(env)[:16] / _sha256(scope)[:32]
        self._lock_path = self.namespace / ".ledger.lock"
        self._host_identity = _stable_host_identity_v1()
        self._live_attempt_tokens: dict[str, str] = {}

    def _assert_host_binding_unlocked(self, *, create: bool) -> None:
        path = self.namespace / _HOST_BINDING_FILENAME
        if not path.is_file():
            if not create:
                raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_HOST_BINDING_MISSING")
            self._write(
                path,
                {
                    "schema_version": SCHEMA_VERSION,
                    "contract_id": CONTRACT_ID,
                    "host_identity_sha256": self._host_identity,
                    "bound_at_utc": _utc_now_iso_v1(),
                },
            )
            return
        if str(self._read_json(path).get("host_identity_sha256") or "") != self._host_identity:
            raise GlobalVenueEffectLedgerError("GLOBAL_LEDGER_HOST_BINDING_MISMATCH")

    def _assert_live_attempt_token_unlocked(self, claim_id: str, record: Mapping[str, Any]) -> None:
        token = self._live_attempt_tokens.get(claim_id)
        persisted = str(record.get("live_attempt_token_sha256") or "")
        if not token or not persisted or _sha256(token) != persisted:
            raise GlobalVenueEffectLedgerError("GLOBAL_CLAIM_TRANSITION_REQUIRES_LIVE_ATTEMPT")

    def _marker_path(self, kind: str, key: str) -> Path:
        return self.namespace / _MARKER_DIRS[kind] / f"{key}.json"

    def _claim_path(self, claim_id: str) -> Path:
        return self.namespace / "claims" / f"{claim_id}.json"

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GlobalVenueEffectLedgerError(
                f"GLOBAL_LEDGER_RECORD_UNREADABLE:{path.name}"
            ) from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
            raise GlobalVenueEffectLedgerError(f"GLOBAL_LEDGER_RECORD_MALFORMED:{path.name}")
        return payload

    def _write(self, path: Path, payload: Mapping[str, Any]) -> None:
        _assert_no_secrets(payload)
        _atomic_write_state_v1(path, payload)

    def _assert_scope(self, identity: GlobalVenueEffectIdentityV1) -> None:
        identity.validate_v1()
        if identity.account_scope.strip() != self.account_scope:
            raise GlobalVenueEffectLedgerError("GLOBAL_IDENTITY_ACCOUNT_SCOPE_MISMATCH")
        if identity.environment.strip().upper() != self.environment:
            raise GlobalVenueEffectLedgerError("GLOBAL_IDENTITY_ENVIRONMENT_MISMATCH")

    def _unresolved_unlocked(self) -> list[dict[str, Any]]:
        claims_dir = self.namespace / "claims"
        if not claims_dir.is_dir():
            return []
        out: list[dict[str, Any]] = []
        for path in sorted(claims_dir.glob("*.json")):
            record = self._read_json(path)
            if str(record.get("state") or "") in UNRESOLVED_STATES:
                out.append(record)
        return out

    def unresolved_claims_v1(self) -> list[dict[str, Any]]:
        if not self.namespace.is_dir():
            return []
        with _exclusive_lock_v1(self._lock_path):
            return self._unresolved_unlocked()

    def consumed_kinds_v1(self, identity: GlobalVenueEffectIdentityV1) -> list[str]:
        self._assert_scope(identity)
        keys = identity.marker_keys()
        return [k for k in _MARKER_ORDER if self._marker_path(k, keys[k]).exists()]

    def claim_v1(self, identity: GlobalVenueEffectIdentityV1) -> GlobalVenueEffectClaimV1:
        """Atomically consume every replay identity of this authorization unit."""
        self._assert_scope(identity)
        keys = identity.marker_keys()
        claim_id = identity.claim_id()
        self.namespace.mkdir(parents=True, exist_ok=True, mode=0o700)
        with _exclusive_lock_v1(self._lock_path):
            self._assert_host_binding_unlocked(create=True)
            for kind in _MARKER_ORDER:
                if self._marker_path(kind, keys[kind]).exists():
                    raise GlobalVenueEffectReplayDeniedError(f"GLOBAL_REPLAY_DENIED:{kind}")
            if self._claim_path(claim_id).exists():
                raise GlobalVenueEffectReplayDeniedError("GLOBAL_REPLAY_DENIED:CLAIM_RECORD")
            if identity.risk_class == RISK_CLASS_NEW_RISK:
                self._settle_proven_unsent_claims_unlocked()
                if self._unresolved_unlocked():
                    raise GlobalVenueEffectLedgerError(
                        "GLOBAL_UNRESOLVED_VENUE_EFFECT_BLOCKS_NEW_RISK"
                    )
            token = secrets.token_hex(32)
            now = _utc_now_iso_v1()
            for kind in _MARKER_ORDER:
                self._write(
                    self._marker_path(kind, keys[kind]),
                    {
                        "schema_version": SCHEMA_VERSION,
                        "contract_id": CONTRACT_ID,
                        "kind": kind,
                        "key": keys[kind],
                        "claim_id": claim_id,
                        "consumed_at_utc": now,
                        "reusable": False,
                    },
                )
            self._write(
                self._claim_path(claim_id),
                {
                    "schema_version": SCHEMA_VERSION,
                    "contract_id": CONTRACT_ID,
                    "claim_id": claim_id,
                    "state": STATE_CLAIMED,
                    "identity": asdict(identity),
                    "owner_authorization_identity": keys[KIND_OWNER_AUTHORIZATION],
                    "claimed_at_utc": now,
                    "history": [{"state": STATE_CLAIMED, "at_utc": now}],
                    "live_attempt_token_sha256": _sha256(token),
                    "host_identity_sha256": self._host_identity,
                    "boot_session_sha256": _boot_session_identity_v1(),
                    "process_id": os.getpid(),
                    "retry_allowed": False,
                    "authorization_reusable": False,
                },
            )
            self._live_attempt_tokens[claim_id] = token
        return GlobalVenueEffectClaimV1(
            claim_id=claim_id,
            identity=identity,
            state=STATE_CLAIMED,
            ledger_namespace=str(self.namespace),
        )

    def load_claim_v1(self, claim_id: str) -> dict[str, Any]:
        path = self._claim_path(str(claim_id or ""))
        if not path.is_file():
            raise GlobalVenueEffectLedgerError("GLOBAL_CLAIM_MISSING")
        return self._read_json(path)

    def _assert_claim_binds_v1(
        self,
        record: Mapping[str, Any],
        *,
        permit_id: str,
        envelope_digest: str,
    ) -> None:
        identity = record.get("identity") or {}
        if str(identity.get("permit_id") or "") != str(permit_id):
            raise GlobalVenueEffectLedgerError("GLOBAL_CLAIM_PERMIT_MISMATCH")
        if str(identity.get("envelope_digest") or "") != str(envelope_digest):
            raise GlobalVenueEffectLedgerError("GLOBAL_CLAIM_ENVELOPE_DIGEST_MISMATCH")

    def _transition_unlocked(
        self,
        claim_id: str,
        *,
        new_state: str,
        allowed_current: frozenset[str],
        permit_id: Optional[str] = None,
        envelope_digest: Optional[str] = None,
        extra: Optional[Mapping[str, Any]] = None,
        require_live_attempt: bool = False,
    ) -> dict[str, Any]:
        self._assert_host_binding_unlocked(create=False)
        path = self._claim_path(claim_id)
        if not path.is_file():
            raise GlobalVenueEffectLedgerError("GLOBAL_CLAIM_MISSING")
        record = self._read_json(path)
        current = str(record.get("state") or "")
        if current not in allowed_current:
            raise GlobalVenueEffectLedgerError(
                f"GLOBAL_CLAIM_INVALID_TRANSITION:{current}->{new_state}"
            )
        if require_live_attempt:
            self._assert_live_attempt_token_unlocked(claim_id, record)
        if permit_id is not None or envelope_digest is not None:
            self._assert_claim_binds_v1(
                record, permit_id=str(permit_id or ""), envelope_digest=str(envelope_digest or "")
            )
        now = _utc_now_iso_v1()
        record["state"] = new_state
        record["history"] = list(record.get("history") or []) + [
            {"state": new_state, "at_utc": now, **dict(extra or {})}
        ]
        record["retry_allowed"] = False
        record["authorization_reusable"] = False
        self._write(path, record)
        return record

    def mark_sent_initiated_v1(
        self, claim_id: str, *, permit_id: str, envelope_digest: str
    ) -> dict[str, Any]:
        """Consume-before-transport: CLAIMED -> SENT_INITIATED exactly once."""
        with _exclusive_lock_v1(self._lock_path):
            return self._transition_unlocked(
                claim_id,
                new_state=STATE_SENT_INITIATED,
                allowed_current=frozenset({STATE_CLAIMED}),
                permit_id=permit_id,
                envelope_digest=envelope_digest,
                require_live_attempt=True,
            )

    def assert_sent_initiated_for_transport_v1(
        self, claim_id: str, *, permit_id: str, envelope_digest: str
    ) -> None:
        with _exclusive_lock_v1(self._lock_path):
            record = self.load_claim_v1(claim_id)
            if str(record.get("state") or "") != STATE_SENT_INITIATED:
                raise GlobalVenueEffectLedgerError("GLOBAL_CLAIM_NOT_SENT_INITIATED")
            self._assert_claim_binds_v1(
                record, permit_id=permit_id, envelope_digest=envelope_digest
            )

    def mark_outcome_v1(
        self, claim_id: str, *, outcome_state: str, detail: str = ""
    ) -> dict[str, Any]:
        if outcome_state not in _OUTCOME_STATES:
            raise GlobalVenueEffectLedgerError(f"GLOBAL_OUTCOME_STATE_FORBIDDEN:{outcome_state}")
        with _exclusive_lock_v1(self._lock_path):
            record = self._transition_unlocked(
                claim_id,
                new_state=outcome_state,
                allowed_current=frozenset({STATE_SENT_INITIATED}),
                extra={"detail": str(detail or "")},
                require_live_attempt=outcome_state in _RELEASING_OUTCOME_STATES,
            )
            self._live_attempt_tokens.pop(claim_id, None)
            return record

    def abandon_unsent_claim_v1(self, claim_id: str, *, reason: str) -> dict[str, Any]:
        """CLAIMED never reached transport (live attempt only); authorization stays consumed."""
        with _exclusive_lock_v1(self._lock_path):
            path = self._claim_path(str(claim_id or ""))
            if path.is_file() and any(
                str(entry.get("state") or "") == STATE_SENT_INITIATED
                for entry in (self._read_json(path).get("history") or [])
                if isinstance(entry, Mapping)
            ):
                raise GlobalVenueEffectLedgerError("GLOBAL_CLAIM_ABANDON_AFTER_SEND_FORBIDDEN")
            record = self._transition_unlocked(
                claim_id,
                new_state=STATE_ABORTED_BEFORE_TRANSPORT,
                allowed_current=frozenset({STATE_CLAIMED}),
                extra={"detail": str(reason or "")},
                require_live_attempt=True,
            )
            self._live_attempt_tokens.pop(claim_id, None)
            return record

    def _claim_proven_not_sent_v1(self, record: Mapping[str, Any]) -> bool:
        """See module docstring "Proven unsent"; every unmet condition means NOT_PROVEN."""
        history = record.get("history")
        if (
            str(record.get("state") or "") != STATE_CLAIMED
            or not isinstance(history, list)
            or len(history) != 1
            or not isinstance(history[0], Mapping)
            or str(history[0].get("state") or "") != STATE_CLAIMED
        ):
            return False
        if str(record.get("host_identity_sha256") or "") != self._host_identity:
            return False
        boot = _boot_session_identity_v1()
        if not boot or str(record.get("boot_session_sha256") or "") != boot:
            return False
        pid = record.get("process_id")
        if pid == os.getpid() or str(record.get("claim_id") or "") in self._live_attempt_tokens:
            return False
        return _process_gone_v1(pid)

    def _settle_proven_unsent_claims_unlocked(self) -> None:
        for record in self._unresolved_unlocked():
            if not self._claim_proven_not_sent_v1(record):
                continue
            self._transition_unlocked(
                str(record.get("claim_id") or ""),
                new_state=STATE_ABORTED_BEFORE_TRANSPORT,
                allowed_current=frozenset({STATE_CLAIMED}),
                extra={"detail": DETAIL_PROVEN_NOT_SENT, "settled_by_process_id": os.getpid()},
            )

    def classify_unresolved_claims_v1(self) -> list[dict[str, Any]]:
        """Read-only recovery view. Never transitions, never authorizes."""
        classes = {
            STATE_CLAIMED: CLASS_CLAIMED_ORPHAN,
            STATE_SENT_INITIATED: CLASS_SENT_INITIATED,
            STATE_UNKNOWN_OUTCOME: CLASS_UNKNOWN_OUTCOME,
        }
        out: list[dict[str, Any]] = []
        for record in self.unresolved_claims_v1():
            state = str(record.get("state") or "")
            claim_id = str(record.get("claim_id") or "")
            live = self._live_attempt_tokens.get(claim_id)
            proven_not_sent = self._claim_proven_not_sent_v1(record)
            out.append(
                {
                    "claim_id": claim_id,
                    "state": state,
                    "classification": (
                        CLASS_CLAIMED_PROVEN_NOT_SENT
                        if proven_not_sent
                        else classes.get(state, "UNRESOLVED_UNCLASSIFIED")
                    ),
                    "proven_not_sent": proven_not_sent,
                    "held_by_this_live_attempt": bool(
                        live and _sha256(live) == record.get("live_attempt_token_sha256")
                    ),
                    "client_order_id": str(
                        (record.get("identity") or {}).get("client_order_id") or ""
                    ),
                    "blocks_new_risk": True,
                    "safe_to_retry": False,
                    "authorization_reusable": False,
                    "resolution_path": "G004_RECONCILE_UNRESOLVED_CLAIM_V1",
                }
            )
        return out

    def reconcile_unresolved_claim_v1(
        self,
        claim_id: str,
        *,
        reconciliation_identity: FullCoreExchangeReconciliationIdentityV1,
        snapshot: FullCoreExchangeReconciliationSnapshotV1,
    ) -> FullCoreExchangeReconciliationDecisionV1:
        """Resolve an unresolved claim from read-only venue evidence via G004.

        Never restores authority: replay markers remain; the claim only leaves the
        unresolved set when the adjudication is complete and authority-neutral.
        Order-not-found is never proof of no submit (G004 halts).
        """
        with _exclusive_lock_v1(self._lock_path):
            record = self.load_claim_v1(claim_id)
            state = str(record.get("state") or "")
            if state not in UNRESOLVED_STATES:
                raise GlobalVenueEffectLedgerError(f"GLOBAL_CLAIM_NOT_RECONCILABLE:{state}")
            identity = record.get("identity") or {}
            if str(reconciliation_identity.clordid) != str(identity.get("client_order_id") or ""):
                raise GlobalVenueEffectLedgerError("GLOBAL_RECON_CLORDID_MISMATCH")
            if str(reconciliation_identity.envelope_digest) != str(
                identity.get("envelope_digest") or ""
            ):
                raise GlobalVenueEffectLedgerError("GLOBAL_RECON_ENVELOPE_DIGEST_MISMATCH")
            decision = adjudicate_full_core_exchange_reconciliation_v1(
                identity=reconciliation_identity,
                snapshot=snapshot,
                local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
            )
            if decision.reconciliation_complete is True and (
                decision.execution_authority_effect == "NONE"
            ):
                self._transition_unlocked(
                    claim_id,
                    new_state=STATE_RECONCILED,
                    allowed_current=UNRESOLVED_STATES,
                    extra={
                        "reconciliation_outcome": decision.outcome,
                        "exposure_retained": bool(decision.exposure_retained),
                        "venue_ord_id": decision.venue_ord_id or "",
                    },
                )
                self._live_attempt_tokens.pop(claim_id, None)
            return decision


__all__ = [
    "ACCOUNT_SCOPE_K1",
    "CANONICAL_LEDGER_DIRNAME",
    "CLASS_CLAIMED_ORPHAN",
    "CLASS_CLAIMED_PROVEN_NOT_SENT",
    "CLASS_SENT_INITIATED",
    "CLASS_UNKNOWN_OUTCOME",
    "CONTRACT_ID",
    "DETAIL_PROVEN_NOT_SENT",
    "ENVIRONMENT_LIVE_EEA",
    "GlobalVenueEffectAuthorityLedgerV1",
    "GlobalVenueEffectClaimV1",
    "GlobalVenueEffectIdentityV1",
    "GlobalVenueEffectLedgerError",
    "GlobalVenueEffectReplayDeniedError",
    "KIND_CLIENT_ORDER_ID",
    "KIND_ENVELOPE",
    "KIND_OWNER_AUTHORIZATION",
    "KIND_PERMIT",
    "RISK_CLASS_NEW_RISK",
    "RISK_CLASS_RISK_REDUCING",
    "STATE_ABORTED_BEFORE_TRANSPORT",
    "STATE_CLAIMED",
    "STATE_COMPLETED_RESPONSE_RECEIVED",
    "STATE_RECONCILED",
    "STATE_SENT_INITIATED",
    "STATE_UNKNOWN_OUTCOME",
    "UNRESOLVED_STATES",
    "ledger_filesystem_is_proven_local_v1",
    "resolve_canonical_global_ledger_root_v1",
]
