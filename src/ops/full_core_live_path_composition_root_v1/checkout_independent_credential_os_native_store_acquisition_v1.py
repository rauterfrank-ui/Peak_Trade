"""Bounded opaque macOS Keychain acquisition behind the EA adapter.

Input identity is the already-bound DZ/EB tuple. The OS lookup returns opaque
bytes only. No payload schema, no UTF-8 field parse, no capability material
flag, no V5 join, no GET, no sign, no POST.

The canonical default lookup backend is MacosSecurityFrameworkLookupBackendV1.
Default wiring does not authorize OS access. REAL_KEYCHAIN_ACCESS_AUTHORIZED
is the explicit Keychain-access gate: false fails closed before
SecItemCopyMatching. resolve_capability_v1 remains fail-closed.

OWNER_GO=OWNER_GO_K1_PRODUCTIVE_MACOS_KEYCHAIN_CREDENTIAL_CLOSEOUT_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any, Iterator, Mapping, NoReturn, Protocol

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialSourceRefV1,
    assert_checkout_independent_source_ref_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    PROVIDER_REF_IDENTIFIER,
    SOURCE_REF_URI,
    resolve_bound_keychain_item_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
    KEYCHAIN_VALUE_DATA_REPRESENTATION,
    KEYCHAIN_VALUE_ENCODING,
    PAYLOAD_SCHEMA_BOUND,
    resolve_bound_keychain_item_class_and_value_encoding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    PRODUCTIVE_TARGET_BACKEND,
    SOURCE_BACKEND_CLASS,
)

OWNER_GO = "OWNER_GO_K1_PRODUCTIVE_MACOS_KEYCHAIN_CREDENTIAL_CLOSEOUT_V1"
THIS_SLICE = "K1_PRODUCTIVE_MACOS_KEYCHAIN_CREDENTIAL_CLOSEOUT_V1"
CONTRACT_VERSION = "v1"
K1_REAL_KEYCHAIN_ACQUISITION_IMPLEMENTED = True
REAL_KEYCHAIN_ACCESS_IMPLEMENTED = False
REAL_KEYCHAIN_ACCESS_AUTHORIZED = False
PRODUCTIVE_PROVIDER_ACTIVE = False
V5_JOINED = False
V5_USES_NEW_PROVIDER = False
EPHEMERAL_MATERIAL_PATH_IMPLEMENTED = False
MATERIAL_LOADED_TRUE_REACHABLE = False
PAYLOAD_SCHEMA_INTRODUCED = False

REASON_ITEM_ABSENT = "KEYCHAIN_ITEM_ABSENT"
REASON_ITEM_AMBIGUOUS = "KEYCHAIN_ITEM_AMBIGUOUS"
REASON_OS_NATIVE_STORE_ERROR = "KEYCHAIN_OS_NATIVE_STORE_ERROR"
REASON_UNEXPECTED_REPRESENTATION = "KEYCHAIN_VALUE_UNEXPECTED_REPRESENTATION"
REASON_IDENTITY_MISMATCH = "KEYCHAIN_IDENTITY_MISMATCH"
REASON_BACKEND_REQUIRED = "OS_NATIVE_STORE_LOOKUP_BACKEND_REQUIRED"
REASON_ACCESS_FORBIDDEN = "REAL_KEYCHAIN_ACCESS_FORBIDDEN"

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"

_ERR_SEC_SUCCESS = 0
_ERR_SEC_ITEM_NOT_FOUND = -25300
_CF_STRING_ENCODING_UTF8 = 0x08000100

_HELD_OPAQUE: dict[int, bytearray] = {}

# Bounded ephemeral Keychain access (module REAL_KEYCHAIN_ACCESS_AUTHORIZED stays false).
_EPHEMERAL_KEYCHAIN_ACCESS_CTX: ContextVar[bool] = ContextVar(
    "full_core_ephemeral_keychain_access_v1",
    default=False,
)
EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_PL_TF_002 = "PL_TF_002_PRODUCTIVE_READ_ONLY_SESSION_EXECUTOR_V1"
EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST = (
    "CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
)
ALLOWED_EPHEMERAL_KEYCHAIN_ACCESS_CONSUMERS_V1: frozenset[str] = frozenset(
    {
        EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_PL_TF_002,
        EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST,
    }
)


def ephemeral_keychain_access_is_active_v1() -> bool:
    return _EPHEMERAL_KEYCHAIN_ACCESS_CTX.get() is True


@contextmanager
def bounded_ephemeral_keychain_access_v1(*, consumer_id: str) -> Iterator[None]:
    """Grant Keychain lookup only inside this context. Never flips module constants."""

    if str(consumer_id or "") not in ALLOWED_EPHEMERAL_KEYCHAIN_ACCESS_CONSUMERS_V1:
        _error("EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_FORBIDDEN")
    token: Token[bool] = _EPHEMERAL_KEYCHAIN_ACCESS_CTX.set(True)
    try:
        yield
    finally:
        _EPHEMERAL_KEYCHAIN_ACCESS_CTX.reset(token)


def borrow_held_opaque_bytes_for_bounded_parse_v1(*, holder_id: int) -> bytes:
    """Return opaque Keychain bytes only during an active ephemeral access scope."""

    if not ephemeral_keychain_access_is_active_v1():
        _error("EPHEMERAL_KEYCHAIN_ACCESS_REQUIRED_FOR_OPAQUE_BORROW")
    buf = _HELD_OPAQUE.get(int(holder_id))
    if buf is None:
        _error("OPAQUE_MATERIAL_NOT_HELD")
    return bytes(buf)


class FullCoreCheckoutIndependentOsNativeStoreAcquisitionError(
    FullCoreCheckoutIndependentCredentialCapabilityError
):
    """Fail-closed opaque Keychain acquisition contract violation."""


class OsNativeStoreLookupBackendV1(Protocol):
    """OS-native generic-password lookup. Must not parse payload fields."""

    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes: ...


@dataclass(frozen=True)
class FullCoreOsNativeStoreAcquisitionProofV1:
    """Public acquisition proof. Never carries opaque credential bytes."""

    acquired: str
    source_ref_uri: str
    keychain_service_id: str
    keychain_account_id: str
    provider_ref_identifier: str
    keychain_item_class: str
    keychain_value_data_representation: str
    payload_schema_bound: str
    material_emitted: str
    material_loaded_on_capability: str
    utf8_payload_parsed: str
    real_keychain_access_authorized: str
    productive_provider_active: str
    v5_joined: str

    def to_dict(self) -> dict[str, str]:
        return {
            "acquired": self.acquired,
            "source_ref_uri": self.source_ref_uri,
            "keychain_service_id": self.keychain_service_id,
            "keychain_account_id": self.keychain_account_id,
            "provider_ref_identifier": self.provider_ref_identifier,
            "keychain_item_class": self.keychain_item_class,
            "keychain_value_data_representation": self.keychain_value_data_representation,
            "payload_schema_bound": self.payload_schema_bound,
            "material_emitted": self.material_emitted,
            "material_loaded_on_capability": self.material_loaded_on_capability,
            "utf8_payload_parsed": self.utf8_payload_parsed,
            "real_keychain_access_authorized": self.real_keychain_access_authorized,
            "productive_provider_active": self.productive_provider_active,
            "v5_joined": self.v5_joined,
        }

    def __repr__(self) -> str:
        return "FullCoreOsNativeStoreAcquisitionProofV1(redacted)"

    def __str__(self) -> str:
        return "FullCoreOsNativeStoreAcquisitionProofV1(redacted)"


def _error(code: str) -> NoReturn:
    raise FullCoreCheckoutIndependentOsNativeStoreAcquisitionError(code)


def assert_real_keychain_access_authorized_for_os_lookup_v1() -> None:
    """Fail closed before SecItemCopyMatching unless the K1 access gate is true."""

    if ephemeral_keychain_access_is_active_v1():
        return
    if REAL_KEYCHAIN_ACCESS_AUTHORIZED is not True:
        _error(REASON_ACCESS_FORBIDDEN)


def wipe_opaque_os_native_store_material_v1(holder_id: int) -> None:
    buf = _HELD_OPAQUE.pop(int(holder_id), None)
    if buf is None:
        return
    for index in range(len(buf)):
        buf[index] = 0


def opaque_os_native_store_material_is_held_v1(holder_id: int) -> bool:
    return int(holder_id) in _HELD_OPAQUE


def _hold_opaque_bytes_v1(holder_id: int, value: bytes) -> None:
    wipe_opaque_os_native_store_material_v1(holder_id)
    _HELD_OPAQUE[int(holder_id)] = bytearray(value)


def assert_bound_os_native_store_query_identity_v1(
    *,
    service: str,
    account: str,
    item_class: str,
) -> None:
    if service != KEYCHAIN_SERVICE_ID or account != KEYCHAIN_ACCOUNT_ID:
        _error(REASON_IDENTITY_MISMATCH)
    if item_class != KEYCHAIN_ITEM_CLASS:
        _error(REASON_IDENTITY_MISMATCH)
    if SOURCE_BACKEND_CLASS != "OS_NATIVE_SECRET_STORE":
        _error("SOURCE_BACKEND_CLASS_DRIFT")
    if PRODUCTIVE_TARGET_BACKEND != "MACOS_KEYCHAIN":
        _error("PRODUCTIVE_TARGET_BACKEND_DRIFT")


def coerce_opaque_value_data_v1(raw: object) -> bytes:
    if isinstance(raw, memoryview):
        raw = raw.tobytes()
    if not isinstance(raw, (bytes, bytearray)):
        _error(REASON_UNEXPECTED_REPRESENTATION)
    if isinstance(raw, bytearray):
        raw = bytes(raw)
    if raw == b"":
        _error(REASON_UNEXPECTED_REPRESENTATION)
    return raw


def _proof_for_bound_identity_v1() -> FullCoreOsNativeStoreAcquisitionProofV1:
    if PAYLOAD_SCHEMA_BOUND is True or PAYLOAD_SCHEMA_INTRODUCED is True:
        _error("PAYLOAD_SCHEMA_MUST_REMAIN_UNBOUND")
    authorized = (
        TRUE_TOKEN
        if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True or ephemeral_keychain_access_is_active_v1()
        else FALSE_TOKEN
    )
    return FullCoreOsNativeStoreAcquisitionProofV1(
        acquired=TRUE_TOKEN,
        source_ref_uri=SOURCE_REF_URI,
        keychain_service_id=KEYCHAIN_SERVICE_ID,
        keychain_account_id=KEYCHAIN_ACCOUNT_ID,
        provider_ref_identifier=PROVIDER_REF_IDENTIFIER,
        keychain_item_class=KEYCHAIN_ITEM_CLASS,
        keychain_value_data_representation=KEYCHAIN_VALUE_DATA_REPRESENTATION,
        payload_schema_bound=FALSE_TOKEN,
        material_emitted=FALSE_TOKEN,
        material_loaded_on_capability=FALSE_TOKEN,
        utf8_payload_parsed=FALSE_TOKEN,
        real_keychain_access_authorized=authorized,
        productive_provider_active=FALSE_TOKEN,
        v5_joined=FALSE_TOKEN,
    )


def public_surfaces_must_not_contain_opaque_material_v1(
    *objs: object,
    sentinel: bytes,
) -> None:
    if not sentinel:
        _error(REASON_UNEXPECTED_REPRESENTATION)
    needles = (sentinel, repr(sentinel), str(sentinel))
    for obj in objs:
        surfaces = (repr(obj), str(obj))
        if isinstance(obj, Mapping):
            surfaces = surfaces + (repr(dict(obj)), str(dict(obj)))
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            payload = obj.to_dict()
            surfaces = surfaces + (repr(payload), str(payload))
        blob = "\n".join(surfaces)
        for needle in needles:
            token = (
                needle.decode("utf-8", "surrogateescape") if isinstance(needle, bytes) else needle
            )
            if token and token in blob:
                _error("OPAQUE_MATERIAL_MUST_NOT_BE_EMITTED")


def run_opaque_os_native_store_acquisition_v1(
    *,
    source_ref: str | FullCoreCheckoutIndependentCredentialSourceRefV1,
    backend: OsNativeStoreLookupBackendV1 | None,
    holder_id: int,
) -> FullCoreOsNativeStoreAcquisitionProofV1:
    """Acquire opaque bytes inside the credential boundary. No public emit."""

    if backend is None:
        backend = MacosSecurityFrameworkLookupBackendV1()
    copy_fn = getattr(backend, "copy_matching_generic_password_value_data_v1", None)
    if not callable(copy_fn):
        _error(REASON_BACKEND_REQUIRED)
    parsed = assert_checkout_independent_source_ref_v1(source_ref)
    identity = resolve_bound_keychain_item_identity_v1(parsed.as_uri())
    encoding = resolve_bound_keychain_item_class_and_value_encoding_v1(parsed.as_uri())
    if identity.source_ref_uri != SOURCE_REF_URI:
        _error(REASON_IDENTITY_MISMATCH)
    if encoding.keychain_item_class != KEYCHAIN_ITEM_CLASS:
        _error(REASON_IDENTITY_MISMATCH)
    if encoding.keychain_value_data_representation != KEYCHAIN_VALUE_DATA_REPRESENTATION:
        _error(REASON_UNEXPECTED_REPRESENTATION)
    if encoding.keychain_value_encoding != KEYCHAIN_VALUE_ENCODING:
        _error("KEYCHAIN_VALUE_ENCODING_DRIFT")
    if encoding.payload_schema_bound != FALSE_TOKEN:
        _error("PAYLOAD_SCHEMA_MUST_REMAIN_UNBOUND")
    assert_bound_os_native_store_query_identity_v1(
        service=identity.keychain_service_id,
        account=identity.keychain_account_id,
        item_class=encoding.keychain_item_class,
    )
    try:
        raw = copy_fn(
            service=identity.keychain_service_id,
            account=identity.keychain_account_id,
            item_class=encoding.keychain_item_class,
        )
        value = coerce_opaque_value_data_v1(raw)
    except FullCoreCheckoutIndependentCredentialCapabilityError:
        wipe_opaque_os_native_store_material_v1(holder_id)
        raise
    except Exception:
        wipe_opaque_os_native_store_material_v1(holder_id)
        _error(REASON_OS_NATIVE_STORE_ERROR)
    _hold_opaque_bytes_v1(holder_id, value)
    proof = _proof_for_bound_identity_v1()
    public_surfaces_must_not_contain_opaque_material_v1(proof, proof.to_dict(), sentinel=value)
    return proof


class MacosSecurityFrameworkLookupBackendV1:
    """macOS Security.framework generic-password lookup. No payload parse."""

    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        assert_bound_os_native_store_query_identity_v1(
            service=service,
            account=account,
            item_class=item_class,
        )
        assert_real_keychain_access_authorized_for_os_lookup_v1()
        payloads = copy_matching_generic_password_payloads_v1(
            service=service,
            account=account,
            item_class=item_class,
        )
        if len(payloads) == 0:
            _error(REASON_ITEM_ABSENT)
        if len(payloads) > 1:
            _error(REASON_ITEM_AMBIGUOUS)
        return coerce_opaque_value_data_v1(payloads[0])


def copy_matching_generic_password_payloads_v1(
    *,
    service: str,
    account: str,
    item_class: str,
) -> list[bytes]:
    """Exact service/account/generic-password SecItemCopyMatching.

    Isolated so tests can substitute this OS boundary. Does not interpret UTF-8
    payload fields.
    """

    assert_bound_os_native_store_query_identity_v1(
        service=service,
        account=account,
        item_class=item_class,
    )
    assert_real_keychain_access_authorized_for_os_lookup_v1()
    if sys.platform != "darwin":
        _error(REASON_OS_NATIVE_STORE_ERROR)
    return _sec_item_copy_matching_generic_password_payloads_v1(
        service=service,
        account=account,
    )


def _sec_item_copy_matching_generic_password_payloads_v1(
    *,
    service: str,
    account: str,
) -> list[bytes]:
    import ctypes
    from ctypes import POINTER, c_char_p, c_int32, c_long, c_uint32, c_void_p, create_string_buffer

    try:
        security = ctypes.CDLL("/System/Library/Frameworks/Security.framework/Security")
        core = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    except OSError:
        _error(REASON_OS_NATIVE_STORE_ERROR)

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
    core.CFDictionaryCreate.argtypes = [
        c_void_p,
        POINTER(c_void_p),
        POINTER(c_void_p),
        c_long,
        c_void_p,
        c_void_p,
    ]
    core.CFDictionaryCreate.restype = c_void_p
    core.CFDictionaryGetValue.argtypes = [c_void_p, c_void_p]
    core.CFDictionaryGetValue.restype = c_void_p
    core.CFGetTypeID.argtypes = [c_void_p]
    core.CFGetTypeID.restype = c_long
    core.CFDataGetTypeID.argtypes = []
    core.CFDataGetTypeID.restype = c_long
    core.CFArrayGetTypeID.argtypes = []
    core.CFArrayGetTypeID.restype = c_long
    core.CFDictionaryGetTypeID.argtypes = []
    core.CFDictionaryGetTypeID.restype = c_long
    core.CFArrayGetCount.argtypes = [c_void_p]
    core.CFArrayGetCount.restype = c_long
    core.CFArrayGetValueAtIndex.argtypes = [c_void_p, c_long]
    core.CFArrayGetValueAtIndex.restype = c_void_p
    core.CFDataGetLength.argtypes = [c_void_p]
    core.CFDataGetLength.restype = c_long
    core.CFDataGetBytePtr.argtypes = [c_void_p]
    core.CFDataGetBytePtr.restype = ctypes.POINTER(ctypes.c_ubyte)
    core.CFStringGetLength.argtypes = [c_void_p]
    core.CFStringGetLength.restype = c_long
    core.CFStringGetMaximumSizeForEncoding.argtypes = [c_long, c_uint32]
    core.CFStringGetMaximumSizeForEncoding.restype = c_long
    core.CFStringGetCString.argtypes = [c_void_p, c_char_p, c_long, c_uint32]
    core.CFStringGetCString.restype = c_int32
    core.CFEqual.argtypes = [c_void_p, c_void_p]
    core.CFEqual.restype = c_int32
    core.CFRelease.argtypes = [c_void_p]
    core.CFRelease.restype = None
    security.SecItemCopyMatching.argtypes = [c_void_p, POINTER(c_void_p)]
    security.SecItemCopyMatching.restype = c_int32

    def _symbol(dll: Any, name: str) -> c_void_p:
        return c_void_p.in_dll(dll, name)

    def _cf_string(text: str) -> c_void_p:
        ref = core.CFStringCreateWithCString(
            None,
            text.encode("utf-8"),
            _CF_STRING_ENCODING_UTF8,
        )
        if not ref:
            _error(REASON_OS_NATIVE_STORE_ERROR)
        return c_void_p(ref)

    def _cf_string_text(ref: c_void_p | int | None) -> str:
        if not ref:
            _error(REASON_IDENTITY_MISMATCH)
        length = int(core.CFStringGetLength(ref))
        max_size = int(core.CFStringGetMaximumSizeForEncoding(length, _CF_STRING_ENCODING_UTF8))
        if max_size < 0:
            _error(REASON_OS_NATIVE_STORE_ERROR)
        buf = create_string_buffer(max_size + 1)
        if int(core.CFStringGetCString(ref, buf, max_size + 1, _CF_STRING_ENCODING_UTF8)) == 0:
            _error(REASON_UNEXPECTED_REPRESENTATION)
        return buf.value.decode("utf-8")

    def _cf_data_bytes(ref: c_void_p | int | None) -> bytes:
        if not ref:
            _error(REASON_UNEXPECTED_REPRESENTATION)
        length = int(core.CFDataGetLength(ref))
        if length <= 0:
            _error(REASON_UNEXPECTED_REPRESENTATION)
        ptr = core.CFDataGetBytePtr(ref)
        if not ptr:
            _error(REASON_UNEXPECTED_REPRESENTATION)
        return bytes(ptr[:length])

    retained: list[c_void_p] = []
    query = None
    result = c_void_p()
    try:
        service_ref = _cf_string(service)
        account_ref = _cf_string(account)
        retained.extend((service_ref, account_ref))
        # SecItem: kSecReturnData + kSecReturnAttributes + kSecMatchLimitAll is invalid (-50 paramErr).
        # Closed-world single generic-password payload: ReturnData + MatchLimitOne only.
        keys = (
            _symbol(security, "kSecClass"),
            _symbol(security, "kSecAttrService"),
            _symbol(security, "kSecAttrAccount"),
            _symbol(security, "kSecReturnData"),
            _symbol(security, "kSecMatchLimit"),
        )
        values = (
            _symbol(security, "kSecClassGenericPassword"),
            service_ref,
            account_ref,
            _symbol(core, "kCFBooleanTrue"),
            _symbol(security, "kSecMatchLimitOne"),
        )
        n = len(keys)
        key_arr = (c_void_p * n)(*[c_void_p(int(k.value or 0)) for k in keys])
        val_arr = (c_void_p * n)(*[c_void_p(int(v.value or 0)) for v in values])
        key_cbs = _CFDictionaryKeyCallBacks.in_dll(core, "kCFTypeDictionaryKeyCallBacks")
        val_cbs = _CFDictionaryValueCallBacks.in_dll(core, "kCFTypeDictionaryValueCallBacks")
        query = core.CFDictionaryCreate(
            None,
            ctypes.cast(key_arr, POINTER(c_void_p)),
            ctypes.cast(val_arr, POINTER(c_void_p)),
            n,
            ctypes.byref(key_cbs),
            ctypes.byref(val_cbs),
        )
        if not query:
            _error(REASON_OS_NATIVE_STORE_ERROR)
        status = int(security.SecItemCopyMatching(query, ctypes.byref(result)))
        if status == _ERR_SEC_ITEM_NOT_FOUND:
            return []
        if status != _ERR_SEC_SUCCESS:
            _error(REASON_OS_NATIVE_STORE_ERROR)
        if not result.value:
            return []
        type_id = int(core.CFGetTypeID(result))
        data_tid = int(core.CFDataGetTypeID())
        array_tid = int(core.CFArrayGetTypeID())
        dict_tid = int(core.CFDictionaryGetTypeID())
        items: list[c_void_p] = []
        if type_id == data_tid:
            items = [result]
        elif type_id == dict_tid:
            items = [result]
        elif type_id == array_tid:
            count = int(core.CFArrayGetCount(result))
            if count > 1:
                _error(REASON_ITEM_AMBIGUOUS)
            items = [c_void_p(core.CFArrayGetValueAtIndex(result, idx)) for idx in range(count)]
        else:
            _error(REASON_UNEXPECTED_REPRESENTATION)
        payloads: list[bytes] = []
        value_key = _symbol(security, "kSecValueData")
        service_key = _symbol(security, "kSecAttrService")
        account_key = _symbol(security, "kSecAttrAccount")
        class_key = _symbol(security, "kSecClass")
        generic = _symbol(security, "kSecClassGenericPassword")
        for item in items:
            if not item:
                _error(REASON_UNEXPECTED_REPRESENTATION)
            item_tid = int(core.CFGetTypeID(item))
            if item_tid == data_tid:
                payloads.append(_cf_data_bytes(item))
                continue
            if item_tid != dict_tid:
                _error(REASON_UNEXPECTED_REPRESENTATION)
            found_class = core.CFDictionaryGetValue(item, class_key)
            if found_class and int(core.CFEqual(found_class, generic)) == 0:
                _error(REASON_IDENTITY_MISMATCH)
            found_service = core.CFDictionaryGetValue(item, service_key)
            found_account = core.CFDictionaryGetValue(item, account_key)
            if (
                _cf_string_text(found_service) != service
                or _cf_string_text(found_account) != account
            ):
                _error(REASON_IDENTITY_MISMATCH)
            data_ref = core.CFDictionaryGetValue(item, value_key)
            payloads.append(_cf_data_bytes(data_ref))
        return payloads
    except FullCoreCheckoutIndependentCredentialCapabilityError:
        raise
    except Exception:
        _error(REASON_OS_NATIVE_STORE_ERROR)
    finally:
        if result.value:
            core.CFRelease(result)
        if query:
            core.CFRelease(query)
        for ref in retained:
            if ref and ref.value:
                core.CFRelease(ref)
