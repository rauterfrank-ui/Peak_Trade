"""Fail-closed K1 Keychain provisioning authority errors (no secret payload)."""

from __future__ import annotations


class K1ProductiveMacosKeychainProvisioningError(RuntimeError):
    """Bounded provisioning contract violation."""
