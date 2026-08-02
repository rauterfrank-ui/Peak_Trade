"""Portable repository-relative path serialization for Phase 9.2 evidence."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from src.ops.phase_9_2_public_md_session_preflight_v1.authorization_path_v1 import (
    prove_authorization_and_confirm_token_path_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import CORE_LOGIC_CHANGE
from src.ops.phase_9_2_public_md_session_preflight_v1.evidence_v1 import (
    build_preflight_evidence_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.path_portability_v1 import (
    PathPortabilityError,
    assert_no_absolute_local_paths_v1,
    to_repository_relative_posix_path_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.prerequisites_v1 import (
    prove_phase91_closed_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
# Case-sensitive local FS roots (avoid matching API paths like /api/v5/users/...).
ABS_LEAK_RE = re.compile(r"(?:/Users/|/home/|/private/tmp/|/var/folders/|/tmp/|(?i:file://))")
REPO_SHA = "debdfd7ca6151fdb3f7a28d4cd05ef9a5ab30956"


def _sha256_canonical(payload: dict) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_absolute_input_serialized_repository_relative(tmp_path: Path) -> None:
    root = tmp_path / "repo_a"
    target = root / "src" / "ops" / "example_v1.py"
    target.parent.mkdir(parents=True)
    target.write_text("# fixture\n", encoding="utf-8")
    rel = to_repository_relative_posix_path_v1(str(target.resolve()), repo_root=root)
    assert rel == "src/ops/example_v1.py"
    assert not Path(rel).is_absolute()
    assert ABS_LEAK_RE.search(rel) is None


def test_relative_paths_remain_stable(tmp_path: Path) -> None:
    root = tmp_path / "repo_b"
    (root / "docs" / "evidence").mkdir(parents=True)
    assert (
        to_repository_relative_posix_path_v1(
            "docs/evidence/capability_phase_9_2/foo.json",
            repo_root=root,
        )
        == "docs/evidence/capability_phase_9_2/foo.json"
    )
    assert (
        to_repository_relative_posix_path_v1(
            r"docs\evidence\capability_phase_9_2\foo.json",
            repo_root=root,
        )
        == "docs/evidence/capability_phase_9_2/foo.json"
    )
    assert (
        to_repository_relative_posix_path_v1(
            "./src/ops/module_v1.py",
            repo_root=root,
        )
        == "src/ops/module_v1.py"
    )


def test_paths_outside_repository_root_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "repo_c"
    root.mkdir()
    outside = tmp_path / "outside" / "secret.py"
    outside.parent.mkdir(parents=True)
    outside.write_text("x\n", encoding="utf-8")
    with pytest.raises(PathPortabilityError, match="path_outside_repository_root"):
        to_repository_relative_posix_path_v1(str(outside.resolve()), repo_root=root)
    with pytest.raises(PathPortabilityError, match="file_uri_forbidden"):
        to_repository_relative_posix_path_v1(
            f"file://{outside.resolve().as_posix()}",
            repo_root=root,
        )
    with pytest.raises(PathPortabilityError, match="path_outside_repository_root"):
        to_repository_relative_posix_path_v1(
            r"C:\Users\other\Peak_Trade\src\ops\x.py",
            repo_root=root,
        )
    with pytest.raises(PathPortabilityError, match="path_outside_repository_root"):
        to_repository_relative_posix_path_v1("../escape.py", repo_root=root)


def test_windows_and_posix_path_variants(tmp_path: Path) -> None:
    root = tmp_path / "repo_d"
    (root / "src" / "ops").mkdir(parents=True)
    posix_rel = to_repository_relative_posix_path_v1(
        "src/ops/authorization_path_v1.py",
        repo_root=root,
    )
    win_rel = to_repository_relative_posix_path_v1(
        r"src\ops\authorization_path_v1.py",
        repo_root=root,
    )
    assert posix_rel == win_rel == "src/ops/authorization_path_v1.py"


def test_cross_root_digest_determinism(tmp_path: Path) -> None:
    rel = "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/confirm_token_v1.py"
    digests: list[str] = []
    for name in ("Users_alice_Peak_Trade", "home_bob_Peak_Trade"):
        root = tmp_path / name
        target = root / rel
        target.parent.mkdir(parents=True)
        target.write_text("same-bytes\n", encoding="utf-8")
        serialized = to_repository_relative_posix_path_v1(str(target.resolve()), repo_root=root)
        payload = {
            "module_paths": {"confirm_token_v1": serialized},
            "semantic_marker": "unchanged",
        }
        digests.append(_sha256_canonical(payload))
        assert serialized == rel
    assert digests[0] == digests[1]


def test_authorization_path_persists_repository_relative_only() -> None:
    payload = prove_authorization_and_confirm_token_path_v1(repo_root=REPO_ROOT)
    assert payload["ok"] is True
    module_paths = payload["module_paths"]
    assert module_paths
    for key, value in module_paths.items():
        assert isinstance(value, str)
        assert value.startswith("src/ops/")
        assert "/" in value
        assert "\\" not in value
        assert not Path(value).is_absolute()
        assert ABS_LEAK_RE.search(value) is None
        assert str(REPO_ROOT.resolve()) not in value
    assert_no_absolute_local_paths_v1(payload, repo_root=REPO_ROOT)
    # Semantic identity unchanged beyond path portability.
    assert payload["AUTHORIZATION_ISSUED"] is False
    assert payload["AUTHORIZATION_CONSUMED"] is False
    assert payload["CONFIRM_TOKEN_PLAINTEXT_EXPOSED"] is False


def test_prerequisite_result_path_is_posix_relative() -> None:
    phase91 = prove_phase91_closed_v1(repo_root=REPO_ROOT)
    assert phase91["ok"] is True
    result_path = phase91["result_path"]
    assert result_path == (
        "docs/evidence/capability_phase_9_1_strategy_registry_closure_v1/"
        "productive_binding/phase_9_1_strategy_registry_closure_result_v1.json"
    )
    assert ABS_LEAK_RE.search(result_path) is None


def test_fixture_materialize_has_no_absolute_paths(tmp_path: Path) -> None:
    """Deterministic local generator probe into an isolated fixture root."""
    fixture_root = tmp_path / "fixture_repo"
    # Minimal tree: reuse productive activation/config + predecessor evidence via copies.
    copy_pairs = [
        "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json",
        "docs/evidence/capability_phase_9_1_strategy_registry_closure_v1/SUMMARY.json",
        (
            "docs/evidence/capability_phase_9_1_strategy_registry_closure_v1/"
            "productive_binding/phase_9_1_strategy_registry_closure_result_v1.json"
        ),
        (
            "docs/evidence/capability_7_2_single_future_stateful_no_order_runtime_activation_v1/"
            "SUMMARY.json"
        ),
        (
            "docs/evidence/capability_7_2_single_future_stateful_no_order_runtime_activation_v1/"
            "productive_binding/activation_status_v1.json"
        ),
        (
            "docs/evidence/capability_7_2_single_future_stateful_no_order_runtime_activation_v1/"
            "productive_binding/single_future_stateful_no_order_runtime_activation_result_v1.json"
        ),
        (
            "docs/evidence/capability_7_2_single_future_stateful_no_order_runtime_activation_v1/"
            "productive_binding/startup_restart_reconciliation_proof_v1.json"
        ),
    ]
    for rel in copy_pairs:
        src = REPO_ROOT / rel
        dst = fixture_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())

    evidence = build_preflight_evidence_v1(
        repository_sha=REPO_SHA,
        repo_root=fixture_root,
        materialize=True,
    )
    assert evidence.ok is True
    assert CORE_LOGIC_CHANGE is False

    generated_root = (
        fixture_root
        / "docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1"
    )
    findings: list[str] = []
    for path in generated_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".json", ".md", ".txt", ".sha256"}:
            continue
        text = path.read_text(encoding="utf-8")
        for match in ABS_LEAK_RE.finditer(text):
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 80)
            findings.append(f"{path.name}:{text[start:end]!r}")
        assert str(REPO_ROOT.resolve()) not in text
        assert str(fixture_root.resolve()) not in text
    assert findings == [], findings

    auth = json.loads(
        (generated_root / "preflight" / "authorization_confirm_token_path_v1.json").read_text(
            encoding="utf-8"
        )
    )
    for value in auth["module_paths"].values():
        assert value.startswith("src/ops/")
        assert not Path(value).is_absolute()

    # Productive session evidence under the real repo must remain untouched by this probe.
    session_marker = (
        REPO_ROOT
        / "docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1"
        / "sessions"
        / "phase_9_2_public_md_smoke_session_v1"
        / "phase_9_2_public_md_smoke_session_evidence_v1.json"
    )
    assert session_marker.is_file()
