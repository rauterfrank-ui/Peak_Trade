"""Shared integrity backend test double for CURRENT_PRODUCTIVE 29P chain tests."""

from __future__ import annotations

from dataclasses import dataclass

TRUSTED_TEST_ORIGIN_MAIN_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@dataclass(frozen=True)
class MockCurrentProductive29PIntegrityBackendV1:
    origin_main: str = TRUSTED_TEST_ORIGIN_MAIN_SHA
    head: str = TRUSTED_TEST_ORIGIN_MAIN_SHA
    drift: str = ""

    def resolve_origin_main_sha_v1(self) -> str:
        return self.origin_main

    def resolve_head_sha_v1(self) -> str:
        return self.head

    def diff_origin_main_for_paths_v1(self, paths: tuple[str, ...]) -> str:
        return self.drift
