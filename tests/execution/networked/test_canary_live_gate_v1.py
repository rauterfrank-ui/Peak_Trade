"""LB-EXE-001 — canary/live gate v1 (always denies outbound; explicit reasons)."""

from src.execution.networked.canary_live_gate_v1 import (
    ENV_PT_CANARY_SCOPE_REF,
    evaluate_canary_live_gate_v1,
    evaluate_canary_live_gate_v1_from_environ,
)


def test_gate_denies_when_not_dry_run() -> None:
    d = evaluate_canary_live_gate_v1(
        dry_run=False,
        mode="paper",
        external_approval_ref="TICKET-1",
    )
    assert d.outbound_live_or_canary_allowed is False
    assert d.reason_code == "deny:dry_run_required_v1"


def test_gate_denies_bad_mode() -> None:
    d = evaluate_canary_live_gate_v1(
        dry_run=True,
        mode="live",
        external_approval_ref="TICKET-1",
    )
    assert d.outbound_live_or_canary_allowed is False
    assert d.reason_code == "deny:mode_not_shadow_or_paper"


def test_gate_denies_missing_external_ref() -> None:
    d = evaluate_canary_live_gate_v1(
        dry_run=True,
        mode="paper",
        external_approval_ref=None,
    )
    assert d.outbound_live_or_canary_allowed is False
    assert d.reason_code == "deny:missing_external_approval_ref_lb_apr_001"
    assert d.external_approval_ref_present is False


def test_gate_denies_networkless_even_with_ref() -> None:
    d = evaluate_canary_live_gate_v1(
        dry_run=True,
        mode="shadow",
        external_approval_ref="CANARY-TICKET-42",
    )
    assert d.outbound_live_or_canary_allowed is False
    assert d.reason_code == "deny:v1_networkless_no_outbound_transport"
    assert d.external_approval_ref_present is True


def test_gate_from_environ_reads_pt_canary_scope_ref() -> None:
    d = evaluate_canary_live_gate_v1_from_environ(
        dry_run=True,
        mode="paper",
        environ={ENV_PT_CANARY_SCOPE_REF: "  ext-99  "},
    )
    assert d.outbound_live_or_canary_allowed is False
    assert d.external_approval_ref_present is True
    assert d.reason_code == "deny:v1_networkless_no_outbound_transport"
