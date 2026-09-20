"""Injectable macOS Keychain provisioning backend (upsert one bound item only)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Protocol

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.constants_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    REAL_KEYCHAIN_WRITE_AUTHORIZED,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.errors_v1 import (
    K1ProductiveMacosKeychainProvisioningError,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.provisioning_context_v1 import (
    ephemeral_keychain_provisioning_is_active_v1,
)

_ERR_SEC_SUCCESS = 0
_ERR_SEC_ITEM_NOT_FOUND = -25300


class OsNativeStoreProvisioningBackendV1(Protocol):
    """Upsert opaque bytes for exactly one generic-password item."""

    def upsert_bound_generic_password_opaque_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
        opaque: bytes,
    ) -> None: ...


@dataclass(frozen=True)
class MacosSecurityFrameworkProvisioningBackendV1:
    """Real Keychain upsert. Caller must supply Owner-GO and ephemeral provisioning scope."""

    def upsert_bound_generic_password_opaque_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
        opaque: bytes,
    ) -> None:
        if REAL_KEYCHAIN_WRITE_AUTHORIZED is True:
            raise K1ProductiveMacosKeychainProvisioningError(
                "STANDING_WRITE_MUST_REMAIN_UNAUTHORIZED"
            )
        if service != KEYCHAIN_SERVICE_ID or account != KEYCHAIN_ACCOUNT_ID:
            raise K1ProductiveMacosKeychainProvisioningError("KEYCHAIN_IDENTITY_MISMATCH")
        if not ephemeral_keychain_provisioning_is_active_v1():
            raise K1ProductiveMacosKeychainProvisioningError(
                "EPHEMERAL_PROVISIONING_SCOPE_REQUIRED"
            )
        if item_class != KEYCHAIN_ITEM_CLASS:
            raise K1ProductiveMacosKeychainProvisioningError("KEYCHAIN_ITEM_CLASS_MISMATCH")
        if not opaque:
            raise K1ProductiveMacosKeychainProvisioningError("OPAQUE_EMPTY")
        if sys.platform != "darwin":
            raise K1ProductiveMacosKeychainProvisioningError("OS_NOT_DARWIN")
        bound_keychain_sec_item_upsert_v1(service=service, account=account, opaque=opaque)


def bound_keychain_sec_item_upsert_v1(*, service: str, account: str, opaque: bytes) -> None:
    """SecItemUpdate or SecItemAdd for one generic-password item (isolated OS boundary)."""

    import ctypes
    from ctypes import POINTER, c_char_p, c_int32, c_long, c_uint32, c_void_p

    try:
        security = ctypes.CDLL("/System/Library/Frameworks/Security.framework/Security")
        core = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    except OSError as exc:
        raise K1ProductiveMacosKeychainProvisioningError("SECURITY_FRAMEWORK_UNAVAILABLE") from exc

    _CF_STRING_ENCODING_UTF8 = 0x08000100

    class _CFDictionaryKeyCallBacks(ctypes.Structure):
        _fields_ = [
            ("version", c_long),
            ("retain", c_void_p),
            ("release", c_void_p),
            ("copyDescription", c_void_p),
            ("equal", c_void_p),
            ("hash", c_void_p),
        ]

    class _CFDictionaryValueCallBacks(ctypes.Structure):
        _fields_ = [
            ("version", c_long),
            ("retain", c_void_p),
            ("release", c_void_p),
            ("copyDescription", c_void_p),
            ("equal", c_void_p),
        ]

    core.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_uint32]
    core.CFStringCreateWithCString.restype = c_void_p
    core.CFDataCreate.argtypes = [c_void_p, c_char_p, c_long]
    core.CFDataCreate.restype = c_void_p
    core.CFDictionaryCreate.argtypes = [
        c_void_p,
        POINTER(c_void_p),
        POINTER(c_void_p),
        c_long,
        c_void_p,
        c_void_p,
    ]
    core.CFDictionaryCreate.restype = c_void_p
    core.CFRelease.argtypes = [c_void_p]
    core.CFRelease.restype = None
    security.SecItemUpdate.argtypes = [c_void_p, c_void_p]
    security.SecItemUpdate.restype = c_int32
    security.SecItemAdd.argtypes = [c_void_p, c_void_p]
    security.SecItemAdd.restype = c_int32

    def _symbol(dll: ctypes.CDLL, name: str) -> c_void_p:
        return c_void_p.in_dll(dll, name)

    def _cf_string(text: str) -> c_void_p:
        ref = core.CFStringCreateWithCString(None, text.encode("utf-8"), _CF_STRING_ENCODING_UTF8)
        if not ref:
            raise K1ProductiveMacosKeychainProvisioningError("CF_STRING_CREATE_FAILED")
        return c_void_p(ref)

    def _cf_data(value: bytes) -> c_void_p:
        if not value:
            raise K1ProductiveMacosKeychainProvisioningError("OPAQUE_EMPTY")
        ref = core.CFDataCreate(None, value, len(value))
        if not ref:
            raise K1ProductiveMacosKeychainProvisioningError("CF_DATA_CREATE_FAILED")
        return c_void_p(ref)

    def _make_dict(pairs: tuple[tuple[c_void_p, c_void_p], ...]) -> c_void_p:
        n = len(pairs)
        keys = (c_void_p * n)(*[k for k, _ in pairs])
        vals = (c_void_p * n)(*[v for _, v in pairs])
        key_cbs = _CFDictionaryKeyCallBacks.in_dll(core, "kCFTypeDictionaryKeyCallBacks")
        val_cbs = _CFDictionaryValueCallBacks.in_dll(core, "kCFTypeDictionaryValueCallBacks")
        ref = core.CFDictionaryCreate(
            None,
            ctypes.cast(keys, POINTER(c_void_p)),
            ctypes.cast(vals, POINTER(c_void_p)),
            n,
            ctypes.byref(key_cbs),
            ctypes.byref(val_cbs),
        )
        if not ref:
            raise K1ProductiveMacosKeychainProvisioningError("CF_DICTIONARY_CREATE_FAILED")
        return c_void_p(ref)

    retained: list[c_void_p] = []
    query = None
    attrs = None
    add_item = None
    try:
        service_ref = _cf_string(service)
        account_ref = _cf_string(account)
        data_ref = _cf_data(opaque)
        retained.extend((service_ref, account_ref, data_ref))
        query = _make_dict(
            (
                (_symbol(security, "kSecClass"), _symbol(security, "kSecClassGenericPassword")),
                (_symbol(security, "kSecAttrService"), service_ref),
                (_symbol(security, "kSecAttrAccount"), account_ref),
            )
        )
        attrs = _make_dict(((_symbol(security, "kSecValueData"), data_ref),))
        status = int(security.SecItemUpdate(query, attrs))
        if status == _ERR_SEC_SUCCESS:
            return
        if status not in {_ERR_SEC_ITEM_NOT_FOUND}:
            raise K1ProductiveMacosKeychainProvisioningError(f"KEYCHAIN_UPDATE_FAILED:{status}")
        add_item = _make_dict(
            (
                (_symbol(security, "kSecClass"), _symbol(security, "kSecClassGenericPassword")),
                (_symbol(security, "kSecAttrService"), service_ref),
                (_symbol(security, "kSecAttrAccount"), account_ref),
                (_symbol(security, "kSecValueData"), data_ref),
            )
        )
        add_status = int(security.SecItemAdd(add_item, None))
        if add_status != _ERR_SEC_SUCCESS:
            raise K1ProductiveMacosKeychainProvisioningError(f"KEYCHAIN_ADD_FAILED:{add_status}")
    finally:
        for ref in (query, attrs, add_item):
            if ref:
                core.CFRelease(ref)
        for ref in retained:
            core.CFRelease(ref)
