"""Explicit bounded Demo POST-owner source over the original shared authority."""

from dataclasses import replace, asdict
import os
from pathlib import Path
import time

from nacl.signing import SigningKey

from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
    PostOwnerAuthorityStoreV1,
    PostOwnerGrantV1,
    SharedPostOwnerAuthorizationV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    assert_envelope_unmodified_v1,
)


class BtcDemoBoundedPostOwnerV1:
    """No implicit start: the runtime supplies its original start registration.

    This source can issue only exact ENTER, native net reversal and bounded
    reduce-only close grants for the explicitly started TESTNET account.
    The original stores still enforce consumption, revocation and dispatch.
    """

    def __init__(self, *, root, registration, recover):
        self.registration = registration
        registration.validate_v1()
        root = Path(root)
        if not root.is_absolute() or root.resolve() != root:
            raise ValueError("BTC_DEMO_POST_OWNER_ROOT_REQUIRED")
        store, checkpoint, key_root = (root / name for name in ("store", "checkpoint", "issuer"))
        for path in (store, checkpoint, key_root):
            path.mkdir(mode=0o700, parents=True, exist_ok=recover)
        self._key_path = key_root / "demo-session-issuer"
        if not recover:
            key = SigningKey.generate()
            fd = os.open(self._key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(fd, bytes(key))
                os.fsync(fd)
            finally:
                os.close(fd)
        else:
            if self._key_path.is_symlink() or self._key_path.stat().st_mode & 0o077:
                raise ValueError("BTC_DEMO_POST_OWNER_PRIVATE_KEY_SCOPE_INVALID")
            key = SigningKey(self._key_path.read_bytes())
        self._key = key
        self.authority = PostOwnerAuthorityStoreV1(
            store / "post-owner.sqlite3",
            registration.digest_v1(),
            "bounded-slot3-demo-post-owner",
            bytes(key.verify_key),
            checkpoint_path=checkpoint / "post-owner-checkpoint.sqlite3",
        )
        if not recover:
            self.authority.provision_v1()
        self._binding = self.authority.binding_digest_v1()

    def authorization_v1(self, envelope, *, action, owner):
        from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3
        from src.ops.btc_demo_session_control_v1 import validate_session_control_v1

        assert_envelope_unmodified_v1(envelope)
        registration = validate_session_control_v1(owner, owner._bounded_demo_session_control)
        if (
            type(owner) is not BtcDemoBudgetOwnerV3
            or registration != self.registration
            or envelope.instrument_id != registration.native_id
            or action not in {"ENTER", "DIRECT_DOUBLE_PLAY_REVERSAL", "BOUNDED_SESSION_CLOSE"}
        ):
            raise ValueError("BTC_DEMO_POST_OWNER_ORIGINAL_SESSION_SCOPE_REQUIRED")
        if action == "BOUNDED_SESSION_CLOSE":
            if (
                envelope.path_kind != action
                or envelope.reduce_only is not True
                or envelope.admission_ref != registration.digest_v1()
            ):
                raise ValueError("BTC_DEMO_POST_OWNER_REDUCE_ONLY_CLOSE_REQUIRED")
            import json
            from src.ops.btc_demo_session_close_v1 import close_root_v1, validate_close_plan_v1

            plan = json.loads((close_root_v1(owner, registration) / "close-plan.json").read_bytes())
            if validate_close_plan_v1(owner, registration, plan) != envelope:
                raise ValueError("BTC_DEMO_POST_OWNER_ORIGINAL_CLOSE_PLAN_REQUIRED")
        else:
            owner.require_bounded_demo_risk_window_v1()
            if envelope.reduce_only is not False or (
                action == "DIRECT_DOUBLE_PLAY_REVERSAL" and envelope.path_kind != action
            ):
                raise ValueError("BTC_DEMO_POST_OWNER_ACTION_MISMATCH")
            if action == "ENTER":
                links = owner.execution_links_v1(active_only=True)
                matches = [
                    rid
                    for rid, link in links.items()
                    if link["phase"] == "PLAN_BOUND" and link["envelope"] == asdict(envelope)
                ]
                if len(matches) != 1:
                    raise ValueError("BTC_DEMO_POST_OWNER_ORIGINAL_ENTER_PLAN_REQUIRED")
                owner.inspect_current_entry_budget_policy_v1(matches[0], envelope)
        now = int(time.time())
        grant = PostOwnerGrantV1(
            store_id=self.authority.store_id,
            store_binding_digest=self._binding,
            issuer_id=self.authority.issuer_id,
            grant_id=action + ":" + envelope.envelope_digest,
            account=registration.account_identity,
            action=action,
            envelope_digest=envelope.envelope_digest,
            issued_at_unix=now,
            expires_at_unix=now + 30,
            signature=b"",
            environment="TESTNET",
        )
        grant = replace(grant, signature=self._key.sign(grant.signing_bytes_v1()).signature)
        return SharedPostOwnerAuthorizationV1(self.authority, grant)
