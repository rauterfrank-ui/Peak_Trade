"""Offline POST authority and its wiring to the real ENTER producer."""

from dataclasses import replace
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time

from nacl.signing import SigningKey
import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    load_durable_post_owner_go_consume_v1,
    persist_durable_post_owner_go_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
    PostOwnerAuthorityStoreV1,
    PostOwnerGrantV1,
    SharedPostOwnerAuthorizationV1,
    SharedPostOwnerAuthorityError,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    load_external_effect_durable_consume_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 as actual,
)
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
    synthetic_current_post_pending_context_v1,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
    _TrustedReadTransport,
    _clean_post_integrity,
    _envelope,
    _forbid_real_sockets as _forbid_real_sockets,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    CurrentProductiveOneShotFreshEnvelopeJoinError,
    _attempt,
)

_ACCOUNT = "injected-observer-account"


def signed_post_authorization(tmp_path, envelope, *, account, action):
    key = SigningKey.generate()
    authority = PostOwnerAuthorityStoreV1(
        tmp_path / "shared-post.sqlite3",
        "offline-post-store",
        "offline-post-owner",
        bytes(key.verify_key),
    )
    authority.provision_v1()
    now = int(time.time())
    replacement = PostOwnerGrantV1(
        store_id=authority.store_id,
        store_binding_digest=authority.binding_digest_v1(),
        issuer_id=authority.issuer_id,
        grant_id="one-grant",
        account=account,
        action=action,
        envelope_digest=envelope.envelope_digest,
        issued_at_unix=now - 30,
        expires_at_unix=now + 120,
        signature=b"",
    )
    grant = replace(replacement, signature=key.sign(replacement.signing_bytes_v1()).signature)
    return SharedPostOwnerAuthorizationV1(authority, grant), key


def revoke(authorization, key):
    authority, grant_id = authorization.authority, authorization.grant.grant_id
    signature = key.sign(authority.revocation_signing_bytes_v1(grant_id)).signature
    authority.revoke_v1(grant_id, signature)


def _reopened(authorization):
    return replace(authorization, authority=replace(authorization.authority))


def _claim_rows(authorization):
    from contextlib import closing

    with closing(sqlite3.connect(authorization.authority.path)) as db:
        return db.execute(
            "SELECT grant_id, dispatch_started_at IS NOT NULL FROM claims ORDER BY grant_id"
        ).fetchall()


def _run_enter(authorization, envelope, root, opener, loads):
    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kwargs):
            loads.append(True)
            return super().copy_matching_generic_password_value_data_v1(**kwargs)

    return actual.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
        owner_go=actual.OWNER_GO,
        baseline_origin_main_sha=actual.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=root,
        evidence_root=root / "evidence",
        perform_real_venue_post=True,
        k1_backend=Backend(),
        opener_factory=opener,
        read_only_get_transport=_TrustedReadTransport(),
        execution_integrity_backend=_clean_post_integrity(),
        post_pending_context=synthetic_current_post_pending_context_v1(envelope),
        shared_post_owner_authorization=authorization,
    )


def test_enter_consumes_grant_once_across_attempt_roots(tmp_path):
    envelope = _envelope()
    auth, _ = signed_post_authorization(tmp_path, envelope, account=_ACCOUNT, action="ENTER")
    first, second = tmp_path / "a", tmp_path / "b"
    requests, loads = [], []

    class Timeout:
        def open(self, request, timeout):
            assert _claim_rows(auth) == [(auth.grant.grant_id, 1)]
            requests.append(request.data)
            raise TimeoutError("simulated only")

    result = _run_enter(auth, envelope, first, Timeout, loads)
    assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
    assert result.envelope_digest == auth.grant.envelope_digest
    assert len(requests) == len(loads) == 1
    with pytest.raises(
        actual.CurrentProductiveActualVenuePostError, match="POST_GRANT_ALREADY_CONSUMED"
    ):
        _run_enter(_reopened(auth), envelope, second, Timeout, loads)
    assert len(requests) == len(loads) == 1
    assert not load_durable_post_owner_go_consume_v1(store_root=second)["present"]
    assert not load_external_effect_durable_consume_v1(store_root=second)["present"]


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("issuer", "POST_GRANT_ISSUER_OR_STORE_MISMATCH"),
        ("signature", "POST_GRANT_SIGNATURE_UNPROVEN"),
        ("revoked", "POST_GRANT_REVOKED"),
        ("scope", "POST_GRANT_SCOPE_MISMATCH"),
        ("action", "POST_GRANT_SCOPE_MISMATCH"),
        ("expired", "POST_GRANT_OUTSIDE_VALIDITY"),
        ("missing-store", "POST_AUTHORITY_STORE_UNPROVEN"),
        ("copy-store", "POST_AUTHORITY_STORE_IDENTITY_MISMATCH"),
        ("fresh-store", "POST_GRANT_STORE_BINDING_MISMATCH"),
    ],
)
def test_enter_invalid_authority_stops_before_local_consumption(tmp_path, case, reason):
    envelope = _envelope()
    auth, key = signed_post_authorization(tmp_path, envelope, account=_ACCOUNT, action="ENTER")
    if case == "issuer":
        auth = replace(auth, grant=replace(auth.grant, issuer_id="foreign"))
    if case == "signature":
        key = SigningKey.generate()
    if case == "revoked":
        revoke(auth, key)
    if case == "scope":
        auth = replace(auth, grant=replace(auth.grant, account="foreign"))
    if case == "action":
        auth = replace(auth, grant=replace(auth.grant, action="L10_CLOSE"))
    if case == "expired":
        auth = replace(auth, grant=replace(auth.grant, expires_at_unix=int(time.time())))
    if case in {"missing-store", "copy-store", "fresh-store"}:
        path = tmp_path / "different.sqlite3"
        if case == "copy-store":
            shutil.copyfile(auth.authority.path, path)
        auth = replace(auth, authority=replace(auth.authority, path=path))
        if case == "fresh-store":
            auth.authority.provision_v1()
    auth = replace(
        auth, grant=replace(auth.grant, signature=key.sign(auth.grant.signing_bytes_v1()).signature)
    )
    attempt = tmp_path / "attempt"
    loads = []

    def no_transport():
        pytest.fail("unexpected transport")

    with pytest.raises(actual.CurrentProductiveActualVenuePostError, match=reason):
        _run_enter(auth, envelope, attempt, no_transport, loads)
    assert loads == []
    assert not load_durable_post_owner_go_consume_v1(store_root=attempt)["present"]
    assert not load_external_effect_durable_consume_v1(store_root=attempt)["present"]
    if case == "missing-store":
        assert not auth.authority.path.exists()
    else:
        assert _claim_rows(auth) == []


def test_enter_revocation_at_socket_keeps_consumed_grant_and_aborts_transport(tmp_path):
    envelope = _envelope()
    auth, key = signed_post_authorization(tmp_path, envelope, account=_ACCOUNT, action="ENTER")
    attempt, loads = tmp_path / "attempt", []

    class RevokeBeforeSocket:
        def __init__(self):
            assert _claim_rows(auth) == [(auth.grant.grant_id, 0)]
            revoke(auth, key)

        def open(self, *args, **kwargs):
            pytest.fail("revoked POST reached the simulated socket")

    with pytest.raises(actual.CurrentProductiveActualVenuePostError, match="POST_GRANT_REVOKED"):
        _run_enter(auth, envelope, attempt, RevokeBeforeSocket, loads)
    assert len(loads) == 1
    permit = load_external_effect_durable_consume_v1(store_root=attempt)["record"]
    assert permit["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
    assert _claim_rows(auth) == [(auth.grant.grant_id, 0)]


def test_consume_race_and_fresh_process_readback(tmp_path):
    envelope = _envelope()
    auth, _ = signed_post_authorization(tmp_path, envelope, account=_ACCOUNT, action="ENTER")
    child = """
import json
from pathlib import Path
import sys
import time
from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
    PostOwnerAuthorityStoreV1, PostOwnerGrantV1, SharedPostOwnerAuthorizationV1, SharedPostOwnerAuthorityError,
)
root, attempt = Path(sys.argv[1]), Path(sys.argv[2])
grant_values = json.loads(sys.argv[3])
grant_values['signature'] = bytes.fromhex(grant_values['signature'])
grant = PostOwnerGrantV1(**grant_values)
store = PostOwnerAuthorityStoreV1(root / 'shared-post.sqlite3', grant.store_id, grant.issuer_id, bytes.fromhex(sys.argv[4]))
attempt.mkdir()
(attempt / 'ready').touch()
deadline = time.monotonic() + 10
while not (root / 'go').exists():
    if time.monotonic() >= deadline:
        raise RuntimeError('race barrier expired')
    time.sleep(0.01)
try:
    SharedPostOwnerAuthorizationV1(store, grant).consume_v1(
        account=grant.account, action='ENTER', envelope_digest=grant.envelope_digest, attempt_root=attempt
    )
    print('RESULT:consumed')
except SharedPostOwnerAuthorityError as exc:
    print(f'RESULT:{exc}')
"""
    import json
    import os

    repo = Path(__file__).resolve().parents[2]
    payload = {**vars(auth.grant), "signature": auth.grant.signature.hex()}

    def launch(name):
        return subprocess.Popen(
            [
                "./scripts/pt",
                "-c",
                child,
                str(tmp_path),
                str(tmp_path / name),
                json.dumps(payload),
                auth.authority.verify_key.hex(),
            ],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def outcome(process):
        stdout, stderr = process.communicate(timeout=15)
        assert process.returncode == 0, (stdout, stderr)
        return [
            line.removeprefix("RESULT:")
            for line in stdout.splitlines()
            if line.startswith("RESULT:")
        ]

    a, b = launch("a"), launch("b")
    deadline = time.monotonic() + 10
    while not all((tmp_path / name / "ready").exists() for name in ("a", "b")):
        assert time.monotonic() < deadline
        time.sleep(0.01)
    (tmp_path / "go").touch()
    assert sorted(outcome(a) + outcome(b)) == ["POST_GRANT_ALREADY_CONSUMED", "consumed"]
    assert outcome(launch("restarted")) == ["POST_GRANT_ALREADY_CONSUMED"]
    assert _claim_rows(auth) == [(auth.grant.grant_id, 0)]


def test_same_claim_cannot_start_dispatch_twice(tmp_path):
    envelope = _envelope()
    auth, _ = signed_post_authorization(tmp_path, envelope, account=_ACCOUNT, action="ENTER")
    claim = auth.consume_v1(
        account=_ACCOUNT,
        action="ENTER",
        envelope_digest=envelope.envelope_digest,
        attempt_root=tmp_path / "attempt",
    )
    foreign_key = SigningKey.generate()
    revocation = auth.authority.revocation_signing_bytes_v1(auth.grant.grant_id)
    with pytest.raises(SharedPostOwnerAuthorityError, match="POST_GRANT_SIGNATURE_UNPROVEN"):
        auth.authority.revoke_v1(auth.grant.grant_id, foreign_key.sign(revocation).signature)
    claim.start_dispatch_v1()
    with pytest.raises(SharedPostOwnerAuthorityError, match="POST_GRANT_DISPATCH_ALREADY_STARTED"):
        claim.start_dispatch_v1()


def test_reprovisioning_same_path_does_not_restore_an_old_grant_or_revocation(tmp_path):
    envelope = _envelope()
    auth, key = signed_post_authorization(tmp_path, envelope, account=_ACCOUNT, action="ENTER")
    args = dict(account=_ACCOUNT, action="ENTER", envelope_digest=envelope.envelope_digest)
    claim = auth.consume_v1(**args, attempt_root=tmp_path / "old-attempt")
    revocation = key.sign(auth.authority.revocation_signing_bytes_v1(auth.grant.grant_id)).signature

    auth.authority.path.unlink()
    auth.authority.provision_v1()
    assert auth.grant.store_binding_digest != auth.authority.binding_digest_v1()
    with pytest.raises(SharedPostOwnerAuthorityError, match="POST_GRANT_STORE_BINDING_MISMATCH"):
        auth.consume_v1(**args, attempt_root=tmp_path / "new-attempt")
    with pytest.raises(SharedPostOwnerAuthorityError, match="POST_GRANT_CLAIM_UNPROVEN"):
        claim.start_dispatch_v1()
    with pytest.raises(SharedPostOwnerAuthorityError, match="POST_GRANT_SIGNATURE_UNPROVEN"):
        auth.authority.revoke_v1(auth.grant.grant_id, revocation)
    assert _claim_rows(auth) == []


def test_local_shared_witness_cannot_enter_legacy_join(tmp_path):
    envelope = _envelope()
    auth, _ = signed_post_authorization(tmp_path, envelope, account=_ACCOUNT, action="ENTER")
    root = tmp_path / "attempt"
    claim = auth.consume_v1(
        account=_ACCOUNT,
        action="ENTER",
        envelope_digest=envelope.envelope_digest,
        attempt_root=root,
    )
    persist_durable_post_owner_go_consume_v1(
        store_root=root,
        owner_go_token=actual.OWNER_GO,
        baseline_origin_main_sha=actual.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        shared_post_owner_claim_digest=claim.receipt_digest_v1(),
    )
    with pytest.raises(
        CurrentProductiveOneShotFreshEnvelopeJoinError, match="POST_OWNER_GO_SHARED_CLAIM_MISMATCH"
    ):
        _attempt(root, envelope=envelope, persist_post_go=False)
    assert not load_external_effect_durable_consume_v1(store_root=root)["present"]
    assert _claim_rows(auth) == [(auth.grant.grant_id, 0)]
