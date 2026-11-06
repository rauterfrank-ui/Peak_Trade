"""Synthetic macOS Keychain upsert binding tests (non-productive tuple only)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.errors_v1 import (
    K1ProductiveMacosKeychainProvisioningError,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.provisioning_backend_v1 import (
    bound_keychain_sec_item_upsert_v1,
)

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS Keychain only")

_SERVICE = "peak-trade.k1.ctypes.fix.v1.test"
_ACCOUNT = "synthetic-nonprod-account"
_OPAQUE_A = b"synthetic-opaque-material-v1-not-secret"
_OPAQUE_B = b"synthetic-opaque-material-v2-not-secret"


def _read_opaque(*, service: str, account: str) -> bytes:
    proc = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"KEYCHAIN_READ_FAILED:{proc.returncode}")
    return proc.stdout.rstrip(b"\n")


def _delete_item(*, service: str, account: str) -> None:
    subprocess.run(
        ["security", "delete-generic-password", "-s", service, "-a", account],
        capture_output=True,
        check=False,
    )


@pytest.fixture(autouse=True)
def _cleanup_synthetic_item() -> None:
    _delete_item(service=_SERVICE, account=_ACCOUNT)
    yield
    _delete_item(service=_SERVICE, account=_ACCOUNT)


def test_synthetic_add_and_readback_pass() -> None:
    bound_keychain_sec_item_upsert_v1(service=_SERVICE, account=_ACCOUNT, opaque=_OPAQUE_A)
    assert _read_opaque(service=_SERVICE, account=_ACCOUNT) == _OPAQUE_A


def test_synthetic_update_upsert_and_material_equality_pass() -> None:
    bound_keychain_sec_item_upsert_v1(service=_SERVICE, account=_ACCOUNT, opaque=_OPAQUE_A)
    bound_keychain_sec_item_upsert_v1(service=_SERVICE, account=_ACCOUNT, opaque=_OPAQUE_B)
    assert _read_opaque(service=_SERVICE, account=_ACCOUNT) == _OPAQUE_B


def test_malformed_empty_opaque_fail_closed() -> None:
    with pytest.raises(K1ProductiveMacosKeychainProvisioningError, match="OPAQUE_EMPTY"):
        bound_keychain_sec_item_upsert_v1(service=_SERVICE, account=_ACCOUNT, opaque=b"")


def test_cleanup_removes_synthetic_item() -> None:
    bound_keychain_sec_item_upsert_v1(service=_SERVICE, account=_ACCOUNT, opaque=_OPAQUE_A)
    _delete_item(service=_SERVICE, account=_ACCOUNT)
    proc = subprocess.run(
        ["security", "find-generic-password", "-s", _SERVICE, "-a", _ACCOUNT, "-w"],
        capture_output=True,
        check=False,
    )
    assert proc.returncode != 0
