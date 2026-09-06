"""Host-selected file and directory durability syscalls.

This module chooses the strongest locally available durability primitive.
A successful return is not HOST_CRASH_DURABILITY proof and is not
POWER_LOSS_DURABILITY proof.
"""

from __future__ import annotations

import fcntl
import os
from typing import Final

PRIMITIVE_F_FULLFSYNC: Final[str] = "F_FULLFSYNC"
PRIMITIVE_OS_FSYNC: Final[str] = "OS_FSYNC"


def file_durability_primitive_name_v1() -> str:
    if hasattr(fcntl, "F_FULLFSYNC"):
        return PRIMITIVE_F_FULLFSYNC
    return PRIMITIVE_OS_FSYNC


def directory_durability_primitive_name_v1() -> str:
    return file_durability_primitive_name_v1()


def request_fd_durability_v1(fd: int) -> str:
    """Request durability for an open fd. Fail-closed. Not a crash proof."""
    if hasattr(fcntl, "F_FULLFSYNC"):
        fcntl.fcntl(fd, fcntl.F_FULLFSYNC)
        return PRIMITIVE_F_FULLFSYNC
    os.fsync(fd)
    return PRIMITIVE_OS_FSYNC
