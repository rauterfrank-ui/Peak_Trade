"""Evidence-bound host/filesystem capability probe for control-state WAL.

Does not guess filesystem type from the platform name. Unknown remains
UNKNOWN. Probe success is not HOST_CRASH_DURABILITY proof.
"""

from __future__ import annotations

import fcntl
import os
import platform
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from src.learning.mutation_critical_control_state_storage_v1.durability_primitives_v1 import (
    directory_durability_primitive_name_v1,
    file_durability_primitive_name_v1,
    request_fd_durability_v1,
)

HOST_CRASH_DURABILITY: Final[str] = "UNPROVEN"
POWER_LOSS_DURABILITY: Final[str] = "UNPROVEN"
HOST_CRASH_PROOF_ENVIRONMENT_PRESENT: Final[bool] = False
POWER_LOSS_PROOF_ENVIRONMENT_PRESENT: Final[bool] = False


def _decode_cstr(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def probe_filesystem_personality_v1(path: Path) -> str:
    """Return kernel fstype for path, or UNKNOWN. Platform name is not used."""
    resolved = str(path.resolve())
    if os.uname().sysname == "Darwin":
        personality = _darwin_statfs_fstypename_v1(resolved)
        if personality:
            return personality
        return "UNKNOWN"
    linux = _linux_mountinfo_fstype_v1(resolved)
    if linux:
        return linux
    return "UNKNOWN"


def _darwin_statfs_fstypename_v1(path: str) -> str | None:
    try:
        import ctypes
    except ImportError:
        return None

    class DarwinStatfs(ctypes.Structure):
        _fields_ = [
            ("f_bsize", ctypes.c_uint32),
            ("f_iosize", ctypes.c_int32),
            ("f_blocks", ctypes.c_uint64),
            ("f_bfree", ctypes.c_uint64),
            ("f_bavail", ctypes.c_uint64),
            ("f_files", ctypes.c_uint64),
            ("f_ffree", ctypes.c_uint64),
            ("f_fsid", ctypes.c_uint32 * 2),
            ("f_owner", ctypes.c_uint32),
            ("f_type", ctypes.c_uint32),
            ("f_flags", ctypes.c_uint32),
            ("f_fssubtype", ctypes.c_uint32),
            ("f_fstypename", ctypes.c_char * 16),
            ("f_mntonname", ctypes.c_char * 1024),
            ("f_mntfromname", ctypes.c_char * 1024),
            ("f_flags_ext", ctypes.c_uint32),
            ("f_reserved", ctypes.c_uint32 * 7),
        ]

    try:
        libc = ctypes.CDLL(None, use_errno=True)
        buf = DarwinStatfs()
        rc = libc.statfs(path.encode("utf-8"), ctypes.byref(buf))
    except Exception:
        return None
    if rc != 0:
        return None
    name = _decode_cstr(buf.f_fstypename)
    if not name or not name.replace("-", "").replace("_", "").isalnum():
        return None
    return name


def _linux_mountinfo_fstype_v1(path: str) -> str | None:
    mountinfo = Path("/proc/self/mountinfo")
    if not mountinfo.is_file():
        return None
    try:
        lines = mountinfo.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    best: tuple[int, str] | None = None
    for line in lines:
        parts = line.split()
        if len(parts) < 9:
            continue
        try:
            sep = parts.index("-")
        except ValueError:
            continue
        mount_point = parts[4].replace("\\040", " ")
        fstype = parts[sep + 1] if sep + 1 < len(parts) else ""
        if not fstype:
            continue
        if path == mount_point or path.startswith(mount_point.rstrip("/") + "/"):
            if best is None or len(mount_point) > best[0]:
                best = (len(mount_point), fstype)
    if best is None:
        return None
    return best[1]


@dataclass(frozen=True)
class HostFilesystemCapabilityV1:
    platform: str
    kernel_sysname: str
    filesystem_personality: str
    storage_path: str
    storage_dev: int
    fsync_available: bool
    fdatasync_available: bool
    f_fullfsync_available: bool
    os_replace_available: bool
    file_durability_primitive: str
    directory_durability_primitive: str
    file_durability_syscall_succeeded: bool
    directory_durability_syscall_succeeded: bool
    atomic_replace_same_filesystem_succeeded: bool
    temp_and_target_same_device: bool
    host_crash_durability: str
    power_loss_durability: str
    host_crash_proof_environment_present: bool
    power_loss_proof_environment_present: bool
    limitations: str


def probe_host_filesystem_capability_v1(root: Path | str) -> HostFilesystemCapabilityV1:
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    probe_dir = Path(tempfile.mkdtemp(prefix="pt_host_fs_probe_", dir=str(path)))
    file_ok = False
    dir_ok = False
    replace_ok = False
    try:
        probe_file = probe_dir / "probe.bin"
        fd = os.open(str(probe_file), os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(fd, b"peak-trade-host-fs-probe")
            request_fd_durability_v1(fd)
            file_ok = True
        finally:
            os.close(fd)
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        dir_fd = os.open(str(probe_dir), flags)
        try:
            request_fd_durability_v1(dir_fd)
            dir_ok = True
        finally:
            os.close(dir_fd)
        src = probe_dir / "replace_src"
        dst = probe_dir / "replace_dst"
        src.write_bytes(b"src")
        dst.write_bytes(b"dst")
        os.replace(str(src), str(dst))
        replace_ok = dst.read_bytes() == b"src" and not src.exists()
    except OSError:
        pass
    finally:
        for child in sorted(probe_dir.rglob("*"), reverse=True):
            try:
                if child.is_dir():
                    child.rmdir()
                else:
                    child.unlink()
            except OSError:
                pass
        try:
            probe_dir.rmdir()
        except OSError:
            pass
    tmp_root = Path(tempfile.gettempdir()).resolve()
    same_device = os.stat(path).st_dev == os.stat(tmp_root).st_dev
    return HostFilesystemCapabilityV1(
        platform=platform.platform(),
        kernel_sysname=os.uname().sysname,
        filesystem_personality=probe_filesystem_personality_v1(path),
        storage_path=str(path.resolve()),
        storage_dev=os.stat(path).st_dev,
        fsync_available=hasattr(os, "fsync"),
        fdatasync_available=hasattr(os, "fdatasync"),
        f_fullfsync_available=hasattr(fcntl, "F_FULLFSYNC"),
        os_replace_available=hasattr(os, "replace"),
        file_durability_primitive=file_durability_primitive_name_v1(),
        directory_durability_primitive=directory_durability_primitive_name_v1(),
        file_durability_syscall_succeeded=file_ok,
        directory_durability_syscall_succeeded=dir_ok,
        atomic_replace_same_filesystem_succeeded=replace_ok,
        temp_and_target_same_device=same_device,
        host_crash_durability=HOST_CRASH_DURABILITY,
        power_loss_durability=POWER_LOSS_DURABILITY,
        host_crash_proof_environment_present=HOST_CRASH_PROOF_ENVIRONMENT_PRESENT,
        power_loss_proof_environment_present=POWER_LOSS_PROOF_ENVIRONMENT_PRESENT,
        limitations=(
            "SYSCALL_SUCCESS_IS_NOT_HOST_KERNEL_CRASH_PROOF|"
            "SYSCALL_SUCCESS_IS_NOT_POWER_LOSS_PROOF|"
            "NO_HOST_KERNEL_CRASH_HARNESS|"
            "NO_POWER_LOSS_HARNESS|"
            "NO_DEVICE_WRITE_BARRIER_PROOF|"
            "DIRECTORY_ENTRY_DURABILITY_NOT_HOST_CRASH_PROVEN|"
            "PROCESS_KILL_IS_NOT_HOST_CRASH"
        ),
    )
