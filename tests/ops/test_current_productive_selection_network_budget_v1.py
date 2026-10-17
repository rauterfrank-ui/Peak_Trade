"""Offline ceiling for CURRENT productive selection GETs. No venue I/O."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError

import pytest

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
    MAX_REQUEST_COUNT,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    UrllibEeaPublicUniverseGetTransportV1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    HTTP_MAX_RETRIES,
    MARK_ENDPOINT_PATH,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    OkxPublicEconomicMdReadAdapterV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap24_selection_state_canonical_writer_v1 import (
    OWNER_GO,
    PUBLISH_MANIFEST_FILENAME,
    execute_current_productive_cap24_selection_state_canonical_write_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_selection_network_budget_v1 import (
    SELECTION_ECONOMIC_MD_GETS_PER_INSTRUMENT,
    SELECTION_ECONOMIC_MD_MAX_RETRIES,
    SelectionNetworkBudgetError,
    SelectionNetworkBudgetExceeded,
    SelectionNetworkBudgetV1,
    build_budgeted_economic_md_source_v1,
)
from tests.ops.test_full_core_current_productive_cap24_selection_state_canonical_writer_v1 import (
    BASE_SHA,
    _INTEGRITY,
    _OBSERVED_UNIX,
    _acquisition,
    _economic_md_source,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_global_economic_md_retry_constant_unchanged() -> None:
    assert HTTP_MAX_RETRIES == 1
    assert SELECTION_ECONOMIC_MD_MAX_RETRIES == 0
    assert SELECTION_ECONOMIC_MD_GETS_PER_INSTRUMENT == 2
    assert MAX_REQUEST_COUNT == 4


def test_ceiling_counts_every_authorized_attempt_and_stops_before_the_next() -> None:
    budget = SelectionNetworkBudgetV1(max_total_attempts=2)
    budget.before_http_attempt()
    budget.before_http_attempt()
    with pytest.raises(SelectionNetworkBudgetExceeded):
        budget.before_http_attempt()
    assert budget.attempts == 2


def test_zero_eligible_fits_when_inventory_already_consumed_the_ceiling() -> None:
    budget = SelectionNetworkBudgetV1(max_total_attempts=4, attempts=4)
    budget.require_complete_economic_md_collection(eligible_count=0)


def test_one_eligible_exact_ceiling_and_one_above_ceiling() -> None:
    exact = SelectionNetworkBudgetV1(max_total_attempts=6, attempts=4)
    exact.require_complete_economic_md_collection(eligible_count=1)
    over = SelectionNetworkBudgetV1(max_total_attempts=5, attempts=4)
    with pytest.raises(SelectionNetworkBudgetExceeded, match="eligible=1"):
        over.require_complete_economic_md_collection(eligible_count=1)


def test_invalid_ceiling_is_rejected_before_any_attempt() -> None:
    with pytest.raises(SelectionNetworkBudgetError):
        SelectionNetworkBudgetV1(max_total_attempts=0)


def test_inventory_transport_does_not_open_when_the_ceiling_is_already_spent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened = {"count": 0}

    class _Opener:
        def open(self, *_args: object, **_kwargs: object) -> object:
            opened["count"] += 1
            raise AssertionError("HTTP_OPEN_FORBIDDEN")

    monkeypatch.setattr(
        "src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1.build_opener",
        lambda *_args, **_kwargs: _Opener(),
    )
    budget = SelectionNetworkBudgetV1(max_total_attempts=1, attempts=1)
    transport = UrllibEeaPublicUniverseGetTransportV1(before_attempt=budget.before_http_attempt)
    with pytest.raises(SelectionNetworkBudgetExceeded):
        transport.get(path=ENDPOINT_PUBLIC_INSTRUMENTS, query={"instType": "SWAP"})
    assert opened["count"] == 0
    assert transport.request_count == 0
    assert budget.attempts == 1


def test_inventory_timeout_still_counts_the_authorized_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Opener:
        def open(self, *_args: object, **_kwargs: object) -> object:
            raise URLError("timed out")

    monkeypatch.setattr(
        "src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1.build_opener",
        lambda *_args, **_kwargs: _Opener(),
    )
    budget = SelectionNetworkBudgetV1(max_total_attempts=4)
    transport = UrllibEeaPublicUniverseGetTransportV1(before_attempt=budget.before_http_attempt)
    result = transport.get(path=ENDPOINT_PUBLIC_INSTRUMENTS, query={"instType": "SWAP"})
    assert result.venue_live_contact is False
    assert transport.request_count == 1
    assert budget.attempts == 1


def test_economic_md_retry_inside_budget_counts_both_attempts() -> None:
    calls = {"n": 0}

    def _fetcher(_url: str, _timeout: float, _limit: int) -> tuple[int, bytes, dict[str, str]]:
        calls["n"] += 1
        if calls["n"] == 1:
            return 500, b"", {}
        return 200, b'{"code":"0","data":[]}', {}

    budget = SelectionNetworkBudgetV1(max_total_attempts=2)
    adapter = OkxPublicEconomicMdReadAdapterV1(
        capture_timestamp="2026-10-17T00:00:00Z",
        fetcher=_fetcher,
        max_retries=1,
        before_attempt=budget.before_http_attempt,
    )
    payload = adapter._get_json(MARK_ENDPOINT_PATH, {"instId": "SOL-USDT-SWAP"})
    assert payload["code"] == "0"
    assert calls["n"] == 2
    assert budget.attempts == 2
    assert HTTP_MAX_RETRIES == 1


def test_economic_md_retry_does_not_open_when_the_budget_is_exhausted() -> None:
    calls = {"n": 0}

    def _fetcher(_url: str, _timeout: float, _limit: int) -> tuple[int, bytes, dict[str, str]]:
        calls["n"] += 1
        return 500, b"", {}

    budget = SelectionNetworkBudgetV1(max_total_attempts=1)
    adapter = OkxPublicEconomicMdReadAdapterV1(
        capture_timestamp="2026-10-17T00:00:00Z",
        fetcher=_fetcher,
        max_retries=1,
        before_attempt=budget.before_http_attempt,
    )
    with pytest.raises(SelectionNetworkBudgetExceeded):
        adapter.collect_instrument_raw_input_v1(venue_native_id="SOL-USDT-SWAP")
    assert calls["n"] == 1
    assert budget.attempts == 1


def test_first_economic_md_timeout_is_a_venue_failure_not_a_silent_drop() -> None:
    def _fetcher(_url: str, _timeout: float, _limit: int) -> tuple[int, bytes, dict[str, str]]:
        raise TimeoutError("budgeted-offline-timeout")

    budget = SelectionNetworkBudgetV1(max_total_attempts=2)
    adapter = OkxPublicEconomicMdReadAdapterV1(
        capture_timestamp="2026-10-17T00:00:00Z",
        fetcher=_fetcher,
        max_retries=0,
        before_attempt=budget.before_http_attempt,
    )
    bundle = adapter.collect_instrument_raw_input_v1(venue_native_id="SOL-USDT-SWAP")
    assert bundle.failure_codes
    assert bundle.marks == ()
    assert budget.attempts == 1


def test_protected_writer_surface_does_not_accept_a_selection_budget() -> None:
    writer = (
        REPO_ROOT
        / "src/ops/governed_productive_account_equity_authority_producer_v1"
        / "current_productive_cap24_selection_state_canonical_writer_v1.py"
    )
    text = writer.read_text(encoding="utf-8")
    assert "selection_budget" not in text
    assert "assert_current_productive_29p_execution_identity_v1" in text
    budget = SelectionNetworkBudgetV1(max_total_attempts=4, attempts=4)
    source = build_budgeted_economic_md_source_v1(
        budget=budget,
        capture_timestamp="2026-10-17T00:00:00Z",
    )
    assert source.max_retries == 0
    assert source.selection_budget is budget
    assert source.before_attempt == budget.before_http_attempt
    assert HTTP_MAX_RETRIES == 1


def test_budget_shortfall_does_not_publish_a_partial_selection(tmp_path: Path) -> None:
    calls = {"n": 0}

    class _CountingSource:
        def collect_instrument_raw_input_v1(self, *, venue_native_id: str) -> object:
            calls["n"] += 1
            return _economic_md_source().collect_instrument_raw_input_v1(
                venue_native_id=venue_native_id
            )

    budget = SelectionNetworkBudgetV1(max_total_attempts=5, attempts=0)
    source = _CountingSource()
    source.selection_budget = budget
    prod = tmp_path / "prod"
    with pytest.raises(SelectionNetworkBudgetExceeded, match="eligible="):
        execute_current_productive_cap24_selection_state_canonical_write_v1(
            owner_go=OWNER_GO,
            origin_main_sha=BASE_SHA,
            acquisition_result=_acquisition(),
            economic_md_public_source=source,
            productivity_root=prod,
            repository_sha=BASE_SHA,
            producer_observed_at_unix=_OBSERVED_UNIX,
            execution_integrity_backend=_INTEGRITY,
        )
    assert calls["n"] == 0
    assert not (prod / PUBLISH_MANIFEST_FILENAME).exists()


def test_exact_budget_publishes_only_after_every_eligible_instrument_is_collected(
    tmp_path: Path,
) -> None:
    budget = SelectionNetworkBudgetV1(max_total_attempts=6)
    inner = _economic_md_source()

    class _CountingSource:
        def collect_instrument_raw_input_v1(self, *, venue_native_id: str) -> object:
            budget.before_http_attempt()
            budget.before_http_attempt()
            return inner.collect_instrument_raw_input_v1(venue_native_id=venue_native_id)

    prod = tmp_path / "prod"
    source = _CountingSource()
    source.selection_budget = budget
    result = execute_current_productive_cap24_selection_state_canonical_write_v1(
        owner_go=OWNER_GO,
        origin_main_sha=BASE_SHA,
        acquisition_result=_acquisition(),
        economic_md_public_source=source,
        productivity_root=prod,
        repository_sha=BASE_SHA,
        producer_observed_at_unix=_OBSERVED_UNIX,
        execution_integrity_backend=_INTEGRITY,
    )
    assert result.ok is True
    assert budget.attempts == 6
    manifest = json.loads((prod / PUBLISH_MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest["repository_sha"] == BASE_SHA


def test_productive_script_refuses_selection_without_an_explicit_ceiling() -> None:
    script = (
        REPO_ROOT
        / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
    )
    text = script.read_text(encoding="utf-8")
    assert "--selection-max-total-get-attempts" in text
    assert "build_budgeted_economic_md_source_v1(" in text
    assert "selection_budget=" not in text
    acquire_at = text.index("acquire_eea_universe_inventory_v1(")
    writer_at = text.index("execute_current_productive_cap24_selection_state_canonical_write_v1(")
    assert text.index("SELECTION_GET_BUDGET_EXPLICIT_REQUIRED") < acquire_at
    assert text.index("SELECTION_INVENTORY_ATTEMPTS_NOT_RECORDED") < writer_at
    assert text.index("build_budgeted_economic_md_source_v1(") < writer_at
    assert "economic_md_public_source=economic_md_source" in text
