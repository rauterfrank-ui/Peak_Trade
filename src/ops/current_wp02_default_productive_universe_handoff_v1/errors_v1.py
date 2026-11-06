"""Fail-closed errors for WP-02 productive default chain."""

from __future__ import annotations


class Wp02ProductiveDefaultChainError(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.code = code
