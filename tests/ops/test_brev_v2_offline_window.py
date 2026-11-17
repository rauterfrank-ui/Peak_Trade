from copy import deepcopy

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey
import pytest

from scripts.ops import brev_v2_offline_window as window


def test_window_grant_binds_manifest_and_requires_the_independent_test_key():
    issuer = SigningKey.generate()
    trust = window.OfflineWindowTrust(issuer.verify_key, lambda _: False)
    manifest = {"mode": "offline_replay", "bounds": {"expires_at_unix": 200}}
    body = window.grant_body(
        manifest, lock_sha="a" * 64, checkpoint_sha="b" * 64, not_before=101, expires_at=190
    )
    manifest["runtime_window"] = {
        "body": body,
        "signature": issuer.sign(window.canonical_json_dumps(body).encode()).signature.hex(),
    }
    assert window._verify_grant(manifest, trust)[0] == body
    changed = deepcopy(manifest)
    changed["bounds"]["expires_at_unix"] += 1
    with pytest.raises(window.WindowRefused, match="BREV_WINDOW_GRANT_INVALID"):
        window._verify_grant(changed, trust)
    unrelated = window.OfflineWindowTrust(SigningKey.generate().verify_key, lambda _: False)
    with pytest.raises(BadSignatureError):
        window._verify_grant(manifest, unrelated)


def test_competing_claim_cannot_replace_current_owner(tmp_path):
    path = tmp_path / "lock.json"
    claim = window._Claim(path, {"phase": "claimed", "deadline": 100})
    with window._guard(path):
        claim.publish()
        with pytest.raises(window.WindowRefused, match="BREV_WINDOW_CONCURRENT_CLAIM"):
            with window._guard(path):
                pytest.fail("another claimant entered the same guard")
        claim.assert_held()
    with window._guard(path):
        window._Claim(path, {"phase": "finished", "deadline": 100}).publish()
    with pytest.raises(window.WindowRefused, match="BREV_WINDOW_CLAIM_LOST"):
        claim.assert_held()
