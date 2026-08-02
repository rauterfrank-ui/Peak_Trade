"""False-positive fix tests for Phase 9.2 rate_limit_event_count."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.phase_9_2_public_md_session_preflight_v1.rate_limit_metric_v1 import (
    compute_rate_limit_event_count_v1,
    count_rate_limit_events_in_payloads_v1,
    event_is_rate_limit_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ONE_HOUR_EVIDENCE = (
    REPO_ROOT
    / "docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1"
    / "sessions/phase_9_2_public_md_one_hour_governed_session_v1"
    / "phase_9_2_public_md_one_hour_governed_session_evidence_v1.json"
)


def _defective_substring_count(payloads: list[object]) -> int:
    """Reproduce the confirmed false-positive antipattern (do not use in production)."""
    return sum(1 for row in payloads if "429" in json.dumps(row, sort_keys=True))


def test_a_hash_false_positive_not_counted() -> None:
    payloads = [
        {
            "feature_digest": "9b429a1c0ffee0123456789abcdef429deadbeef",
            "sha256": "aa429bbccdddeeefff00112233445566778899aa",
            "id": "evt_429abc",
            "observation_id": "obs-429-hash-only",
        }
    ]
    assert _defective_substring_count(payloads) >= 1
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 0


def test_b_real_http_429_counted_once() -> None:
    payloads = [{"event": "http_response", "http_status": 429, "path": "/api/v5/market/ticker"}]
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 1
    assert event_is_rate_limit_v1(payloads[0]) is True


def test_c_multiple_real_http_429_exact_count() -> None:
    payloads = [
        {"http_status": 429, "seq": 1},
        {"status": 429, "seq": 2},
        {"status_code": "429", "seq": 3},
        {"error_code": "RATE_LIMIT_HTTP_429", "seq": 4},
    ]
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 4


def test_d_free_text_429_without_classification_not_counted() -> None:
    payloads = [
        {
            "exception": "upstream returned 429 in message body snippet",
            "message": "retry later: code=429",
            "note": "contains 429 but is not a rate-limit classification",
        }
    ]
    assert _defective_substring_count(payloads) >= 1
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 0


def test_e_dns_abort_not_counted_as_rate_limit() -> None:
    payloads = [
        {
            "event": "killstate",
            "detail": (
                "TRANSPORT_FAILURE:FETCH_FAILED:DNS_RESOLUTION_FAILED:"
                "[Errno 8] nodename nor servname provided, or not known"
            ),
            "trigger": "INVARIANT_VIOLATION",
        }
    ]
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 0


def test_f_mixed_events_exactly_one_real_429() -> None:
    payloads = [
        {"feature_digest": "deadbeef429cafe"},
        {
            "detail": (
                "TRANSPORT_FAILURE:FETCH_FAILED:DNS_RESOLUTION_FAILED:"
                "[Errno 8] nodename nor servname provided, or not known"
            )
        },
        {"error": "timeout", "message": "read timed out after 429ms"},
        {"http_status": 429, "path": "/api/v5/market/books"},
        {"exception": "saw 429 in free text"},
    ]
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 1


def test_authoritative_transport_http_429_count_preferred() -> None:
    payloads = [
        {"transport_telemetry": {"http_429_count": 2}},
        {"http_status": 429},
        {"http_status": 429},
        {"http_status": 429},
    ]
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 2


def test_canonical_error_chain_token_match() -> None:
    payloads = [
        {
            "detail": "FETCH_FAILED:RATE_LIMIT_RETRY_EXHAUSTED:RATE_LIMIT_HTTP_429",
        }
    ]
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 1


def test_evidence_root_scan_tmp(tmp_path: Path) -> None:
    root = tmp_path / "session"
    root.mkdir()
    (root / "connectivity_events.jsonl").write_text(
        json.dumps({"feature_digest": "x429y"}) + "\n" + json.dumps({"http_status": 429}) + "\n",
        encoding="utf-8",
    )
    (root / "shutdown_reason.json").write_text(
        json.dumps(
            {
                "detail": (
                    "TRANSPORT_FAILURE:FETCH_FAILED:DNS_RESOLUTION_FAILED:"
                    "[Errno 8] nodename nor servname provided, or not known"
                )
            }
        ),
        encoding="utf-8",
    )
    assert compute_rate_limit_event_count_v1(evidence_root=root) == 1


def test_g_regression_historical_one_hour_package_not_mutated_and_metric_zero() -> None:
    """Historical packaged evidence stays byte-identical; structured recount is 0."""
    if not ONE_HOUR_EVIDENCE.is_file():
        # Untracked local evidence may be absent in clean CI clones.
        return
    before = ONE_HOUR_EVIDENCE.read_bytes()
    packaged = json.loads(before.decode("utf-8"))
    assert packaged["metrics"]["rate_limit_event_count"] == 24

    session_dir = ONE_HOUR_EVIDENCE.parent
    wallclock = session_dir / "wallclock_run"
    runtime_path = wallclock / "runtime_events.jsonl"

    # Defective packager scanned runtime_events via bare "429" substring (== 24).
    payloads: list[object] = []
    if runtime_path.is_file():
        for line in runtime_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                payloads.append(json.loads(line))

    structured = compute_rate_limit_event_count_v1(evidence_root=session_dir)
    assert structured == 0

    if payloads:
        defective = _defective_substring_count(payloads)
        assert defective == 24
        assert count_rate_limit_events_in_payloads_v1(payloads) == 0

    after = ONE_HOUR_EVIDENCE.read_bytes()
    assert after == before
