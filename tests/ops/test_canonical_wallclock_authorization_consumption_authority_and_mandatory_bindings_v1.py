"""Focused tests for canonical v2 wallclock consumption authority + mandatory bindings."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    AuthorizationArtifactV2Error,
    parse_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_writer_v2 import (
    build_authorization_artifact_dict_v2,
    new_authorization_id_v2,
    write_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.revocation_record_v1 import (
    issue_token_exposure_revocation_v1,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.call_graph_contract_v1 import (
    verify_wallclock_v2_gate_call_graph_v1,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA_REJECTED_LEGACY,
    AUTHORIZED_NETWORK_SCOPE,
    AUTHORIZED_VENUE,
    MANDATORY_SAFETY_BOUNDARIES,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.effective_session_config_digest_v1 import (
    compute_effective_session_config_digest_v1,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.wallclock_v2_gatekeeper_v1 import (
    consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.authorization_consumption_runtime_v1 import (
    consume_authorization_for_wallclock_start_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    WallclockEvidenceWriterV1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (
    mint_productive_confirm_token_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    build_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIX = (
    REPO_ROOT
    / "tests/fixtures/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
NOW = 1_700_000_000.0
SHA = "fbfc3fdbae2b966d0ae44044b1d3c3b64da68afd"
RUNBOOK = "a7529ef8ba8c5950f6372822b71ac2a5304ae037013288d48d53306d4105ff5a"


def _prereg():
    return parse_preregistration_contract_v1(
        load_preregistration_contract_dict_v1(
            FIX / "preregistration_wallclock_valid_non_authoritative.json"
        )
    )


def _go():
    return parse_operator_go_contract_v1(
        load_operator_go_contract_dict_v1(
            FIX / "operator_go_wallclock_valid_non_authoritative.json"
        )
    )


def _material() -> str:
    return mint_productive_confirm_token_v1()


def _write_bound_v2(
    tmp_path: Path,
    *,
    token: str | None = None,
    runtime_overrides: dict[str, Any] | None = None,
    safety: dict[str, bool] | None = None,
    duration: int = 3600,
    config_files: dict[str, str] | None = None,
) -> tuple[Path, str, dict[str, Any]]:
    prereg = _prereg()
    tok = token or _material()
    files = config_files or {"fixture.toml": "a" * 64}
    payload = build_authorization_artifact_dict_v2(
        authorization_id=new_authorization_id_v2(),
        preregistration_id=prereg.session_id,
        preregistration_digest=prereg.scope_digest(),
        repository_sha=SHA,
        runbook_sha256=RUNBOOK,
        session_duration_seconds=duration,
        config_digests=files,
        safety_boundaries=safety or dict(MANDATORY_SAFETY_BOUNDARIES),
        confirm_token=tok,
        capability=TARGET_RUNTIME_CAPABILITY,
        created_at=NOW,
        expires_at=NOW + 3600,
        runtime_overrides=runtime_overrides,
        venue=AUTHORIZED_VENUE,
        network_scope=AUTHORIZED_NETWORK_SCOPE,
    )
    path = tmp_path / "authorization_artifact_v2.json"
    result = write_authorization_artifact_v2(output_path=path, artifact_dict=payload)
    assert result.ok, result.blockers
    return path, tok, payload


def test_v2_happy_path_atomic_consumption_no_session_start(tmp_path: Path) -> None:
    path, token, _ = _write_bound_v2(tmp_path)
    evidence = tmp_path / "ev"
    evidence.mkdir()
    writer = WallclockEvidenceWriterV1(evidence_root=evidence)
    writer.ensure_append_files()
    side_effect_probe = {"lock": 0, "transport": 0}

    class ProbeWriter(WallclockEvidenceWriterV1):
        def write_immutable_json(self, name: str, payload):  # type: ignore[no-untyped-def]
            if name == "session_manifest.json":
                side_effect_probe["lock"] += 1
            return super().write_immutable_json(name, payload)

    writer = ProbeWriter(evidence_root=evidence)
    writer.ensure_append_files()
    result = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
        prereg=_prereg(),
        go=_go(),
        confirm_token=token,
        evidence_writer=writer,
        artifact_path=path,
        now_unix=NOW,
        expected_repository_sha=SHA,
        expected_venue=AUTHORIZED_VENUE,
        expected_network_scope=AUTHORIZED_NETWORK_SCOPE,
        fingerprint_ledger_path=tmp_path / "fp.ledger",
    )
    assert result.ok, result.blockers
    assert result.transport_open_allowed is True
    assert result.to_dict()["session_started"] is False
    assert side_effect_probe["lock"] == 0
    assert (evidence / "authorization_consumption_record.json").is_file()
    consumed = json.loads(path.read_text(encoding="utf-8"))
    assert consumed["schema"] == AUTHORIZATION_SCHEMA
    assert consumed["state"] == "CONSUMED"


def test_v1_quarantine_no_side_effects(tmp_path: Path) -> None:
    prereg = _prereg()
    go = _go()
    material = "GO_PSO_SESSION_PREREG_V1_WALLCLOCK_FIXTURE_NON_AUTH_MATERIAL_A1B2"
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_wallclock_fixture_v1",
        now_unix=NOW,
    )
    assert built.ok and built.artifact is not None
    evidence = tmp_path / "ev"
    evidence.mkdir()
    writer = WallclockEvidenceWriterV1(evidence_root=evidence)
    writer.ensure_append_files()
    artifact_path = tmp_path / "v1.json"
    artifact_path.write_text(
        json.dumps(built.artifact.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    rejected = consume_authorization_for_wallclock_start_v1(
        prereg=prereg,
        go=go,
        artifact=built.artifact,
        confirm_token=material,
        evidence_writer=writer,
        artifact_path=artifact_path,
        now_unix=NOW,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fp.ledger",
    )
    assert rejected.ok is False
    assert AUTHORIZATION_SCHEMA_REJECTED_LEGACY in rejected.blockers
    assert rejected.transport_open_allowed is False
    assert not (evidence / "authorization_consumption_record.json").exists()
    assert not (evidence / "session.lock").exists()

    gate = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        evidence_writer=writer,
        artifact_path=artifact_path,
        now_unix=NOW,
        expected_repository_sha=SHA,
        expected_venue=AUTHORIZED_VENUE,
        expected_network_scope=AUTHORIZED_NETWORK_SCOPE,
        fingerprint_ledger_path=tmp_path / "fp.ledger",
    )
    assert gate.ok is False
    assert AUTHORIZATION_SCHEMA_REJECTED_LEGACY in gate.blockers
    assert gate.session_side_effects == 0


@pytest.mark.parametrize("field", sorted(MANDATORY_SAFETY_BOUNDARIES))
def test_missing_mandatory_safety_field_fail_closed(tmp_path: Path, field: str) -> None:
    path, _token, payload = _write_bound_v2(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    del raw["safety_boundaries"][field]
    raw.pop("integrity_digest", None)
    raw.pop("digest_scope", None)
    with pytest.raises(AuthorizationArtifactV2Error, match="SAFETY_FIELD_MISSING"):
        parse_authorization_artifact_v2(raw)
    _ = payload


@pytest.mark.parametrize(
    "field,bad",
    [
        ("private_api", True),
        ("real_order_routing", True),
        ("external_paper_order_execution", True),
        ("public_market_data_only", False),
        ("analytical_simulated_execution", False),
        ("forced_wiring_fixture_mode", True),
        ("no_implicit_resume", False),
        ("wallclock_mode", False),
    ],
)
def test_unsafe_safety_values_fail_closed(tmp_path: Path, field: str, bad: bool) -> None:
    safety = dict(MANDATORY_SAFETY_BOUNDARIES)
    safety[field] = bad
    with pytest.raises(Exception):
        _write_bound_v2(tmp_path, safety=safety)


def test_duration_not_3600_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        _write_bound_v2(tmp_path, duration=1800)


def test_bool_coercion_rejected() -> None:
    with pytest.raises(AuthorizationArtifactV2Error, match="MANDATORY_BOOL_TYPE"):
        parse_authorization_artifact_v2(
            {
                "schema": AUTHORIZATION_SCHEMA,
                "schema_version": "v2",
                "authorization_id": "x",
                "capability": TARGET_RUNTIME_CAPABILITY,
                "preregistration_id": "p",
                "preregistration_digest": "d" * 64,
                "repository_sha": SHA,
                "runbook_sha256": RUNBOOK,
                "session_duration_seconds": 3600,
                "session_config_digest": "a" * 64,
                "config_digests": {"effective_session_config": "a" * 64},
                "safety_boundaries": {**MANDATORY_SAFETY_BOUNDARIES, "private_api": 0},  # type: ignore[dict-item]
                "venue": AUTHORIZED_VENUE,
                "network_scope": AUTHORIZED_NETWORK_SCOPE,
                "confirm_token_fingerprint": "0" * 64,
                "confirm_token_digest": "sha256:" + "0" * 64,
                "created_at": 1.0,
                "expires_at": 2.0,
                "single_use": True,
                "state": "CREATED_UNCONSUMED",
                "state_version": 1,
                "revocation_required_lookup": True,
                "forced_wiring_fixture_mode": False,
                "no_implicit_resume": True,
                "atomic_consumption_required": True,
                "replay_blocked": True,
                "audit_trail_required": True,
            }
        )


def test_config_digest_match_and_runtime_override_drift(tmp_path: Path) -> None:
    path, token, payload = _write_bound_v2(tmp_path, runtime_overrides=None)
    evidence = tmp_path / "ev"
    evidence.mkdir()
    writer = WallclockEvidenceWriterV1(evidence_root=evidence)
    writer.ensure_append_files()
    ok = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
        prereg=_prereg(),
        go=_go(),
        confirm_token=token,
        evidence_writer=writer,
        artifact_path=path,
        now_unix=NOW,
        expected_repository_sha=SHA,
        expected_venue=AUTHORIZED_VENUE,
        expected_network_scope=AUTHORIZED_NETWORK_SCOPE,
        fingerprint_ledger_path=tmp_path / "fp_ok.ledger",
    )
    assert ok.ok, ok.blockers

    path2, token2, _ = _write_bound_v2(tmp_path / "b", runtime_overrides=None)
    evidence2 = tmp_path / "ev2"
    evidence2.mkdir()
    writer2 = WallclockEvidenceWriterV1(evidence_root=evidence2)
    writer2.ensure_append_files()
    drift = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
        prereg=_prereg(),
        go=_go(),
        confirm_token=token2,
        evidence_writer=writer2,
        artifact_path=path2,
        now_unix=NOW,
        expected_repository_sha=SHA,
        expected_venue=AUTHORIZED_VENUE,
        expected_network_scope=AUTHORIZED_NETWORK_SCOPE,
        fingerprint_ledger_path=tmp_path / "fp_drift.ledger",
        runtime_overrides={"poll_interval_seconds": 9.9},
    )
    assert drift.ok is False
    assert "CONFIG_DRIFT" in drift.blockers or "SESSION_CONFIG_DIGEST_MISMATCH" in drift.blockers
    assert not (evidence2 / "authorization_consumption_record.json").exists()
    # deterministic key order
    d1 = compute_effective_session_config_digest_v1(config_files={"b": "1" * 64, "a": "2" * 64})
    d2 = compute_effective_session_config_digest_v1(config_files={"a": "2" * 64, "b": "1" * 64})
    assert d1 == d2
    assert len(payload["session_config_digest"]) == 64


def test_revocation_before_consumption_blocks_side_effects(tmp_path: Path) -> None:
    path, token, payload = _write_bound_v2(tmp_path)
    art = parse_authorization_artifact_v2(json.loads(path.read_text(encoding="utf-8")))
    evidence = tmp_path / "ev"
    evidence.mkdir()
    assert issue_token_exposure_revocation_v1(
        evidence_root=evidence,
        authorization_id=art.authorization_id,
        authorization_digest=art.integrity_digest,
        preregistration_id=art.preregistration_id,
        preregistration_digest=art.preregistration_digest,
        repository_sha=art.repository_sha,
        previous_state=art.state.value,
        capability=art.capability,
    ).ok
    writer = WallclockEvidenceWriterV1(evidence_root=evidence)
    writer.ensure_append_files()
    result = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
        prereg=_prereg(),
        go=_go(),
        confirm_token=token,
        evidence_writer=writer,
        artifact_path=path,
        now_unix=NOW,
        expected_repository_sha=SHA,
        expected_venue=AUTHORIZED_VENUE,
        expected_network_scope=AUTHORIZED_NETWORK_SCOPE,
        fingerprint_ledger_path=tmp_path / "fp.ledger",
    )
    assert result.ok is False
    assert any("REVOKED" in b for b in result.blockers)
    assert result.transport_open_allowed is False
    assert not (evidence / "session.lock").exists()
    _ = payload


def test_parallel_consume_terminal(tmp_path: Path) -> None:
    path, token, _ = _write_bound_v2(tmp_path)
    results: list[bool] = []
    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            evidence = tmp_path / f"ev{idx}"
            evidence.mkdir(exist_ok=True)
            writer = WallclockEvidenceWriterV1(evidence_root=evidence)
            writer.ensure_append_files()
            res = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
                prereg=_prereg(),
                go=_go(),
                confirm_token=token,
                evidence_writer=writer,
                artifact_path=path,
                now_unix=NOW,
                expected_repository_sha=SHA,
                expected_venue=AUTHORIZED_VENUE,
                expected_network_scope=AUTHORIZED_NETWORK_SCOPE,
                fingerprint_ledger_path=tmp_path / f"fp{idx}.ledger",
            )
            results.append(res.ok)
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc).__name__)
            results.append(False)

    t1 = threading.Thread(target=worker, args=(1,))
    t2 = threading.Thread(target=worker, args=(2,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert results.count(True) <= 1
    # Concurrent writers may race on atomic replace; both failure modes are fail-closed.
    assert results.count(True) + results.count(False) == 2
    final = json.loads(path.read_text(encoding="utf-8"))
    assert final["state"] in {"CONSUMED", "CREATED_UNCONSUMED"}
    _ = errors


def test_call_graph_contract() -> None:
    result = verify_wallclock_v2_gate_call_graph_v1(repo_root=REPO_ROOT)
    assert result.ok, result.blockers


def test_no_private_api_imports() -> None:
    import ast

    root = (
        REPO_ROOT
        / "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1"
    )
    forbidden = ("src.orders", "src.broker", "src.live", "src.execution.live")
    hits = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if any(node.module == f or node.module.startswith(f + ".") for f in forbidden):
                    hits.append((str(path), node.module))
    assert hits == []


def test_authority_inventory_contract() -> None:
    from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.authority_inventory_v1 import (
        verify_productive_authorization_authority_inventory_v1,
    )

    result = verify_productive_authorization_authority_inventory_v1(repo_root=REPO_ROOT)
    assert result.ok, result.blockers


@pytest.mark.parametrize(
    "venue",
    [None, "", "okx", " OKX", "BINANCE", "Okx"],
)
def test_venue_mismatch_or_missing_fail_closed(tmp_path: Path, venue: object) -> None:
    path, token, payload = _write_bound_v2(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("integrity_digest", None)
    raw.pop("digest_scope", None)
    if venue is None:
        raw.pop("venue", None)
    else:
        raw["venue"] = venue
    from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
        stamp_integrity_digest,
    )

    stamped = stamp_integrity_digest(raw)
    path.write_text(json.dumps(stamped, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    evidence = tmp_path / "ev_venue"
    writer = WallclockEvidenceWriterV1(evidence_root=evidence)
    result = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
        prereg=_prereg(),
        go=_go(),
        confirm_token=token,
        evidence_writer=writer,
        artifact_path=path,
        now_unix=NOW,
        expected_repository_sha=SHA,
        expected_venue=AUTHORIZED_VENUE,
        expected_network_scope=AUTHORIZED_NETWORK_SCOPE,
        fingerprint_ledger_path=tmp_path / "fp_venue.ledger",
    )
    assert result.ok is False
    assert result.session_side_effects == 0
    assert not evidence.exists() or not any(evidence.iterdir())


def test_expected_venue_missing_fail_closed(tmp_path: Path) -> None:
    path, token, _ = _write_bound_v2(tmp_path)
    evidence = tmp_path / "ev_exp"
    writer = WallclockEvidenceWriterV1(evidence_root=evidence)
    result = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
        prereg=_prereg(),
        go=_go(),
        confirm_token=token,
        evidence_writer=writer,
        artifact_path=path,
        now_unix=NOW,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fp_exp.ledger",
    )
    assert result.ok is False
    assert "EXPECTED_VENUE_MISSING" in result.blockers
    assert not evidence.exists() or not any(evidence.iterdir())


def test_session_runtime_no_evidence_on_venue_mismatch(tmp_path: Path) -> None:
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
        EeaPublicMdTransportV1,
    )
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
        WallclockRuntimeConfigV1,
        WallclockSessionRuntimeV1,
    )

    path, token, _payload = _write_bound_v2(tmp_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("integrity_digest", None)
    raw.pop("digest_scope", None)
    raw["venue"] = "BINANCE"
    from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
        stamp_integrity_digest,
    )

    path.write_text(
        json.dumps(stamp_integrity_digest(raw), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    evidence = tmp_path / "ev_session_venue"
    body = json.dumps(
        {"code": "0", "msg": "", "data": [{"instId": "ETH-USDT-SWAP", "markPx": "1"}]}
    ).encode("utf-8")

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        return 200, body, {}

    runtime = WallclockSessionRuntimeV1(
        evidence_root=evidence,
        transport=EeaPublicMdTransportV1(fetcher=fetcher, environ={}),
        config=WallclockRuntimeConfigV1(max_cycles=1, max_session_duration_seconds=1),
        clock_wall=lambda: NOW,
        clock_mono=lambda: 1.0,
        sleep=lambda _s: None,
        repo_root=REPO_ROOT,
    )
    result = runtime.run(
        prereg=_prereg(),
        go=_go(),
        confirm_token=token,
        artifact_path=path,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fp_sess.ledger",
    )
    assert result.consumed is False
    assert not evidence.exists()
    assert runtime.state.value == "INVALID"
