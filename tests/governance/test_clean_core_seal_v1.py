"""CLEAN_CORE_SEAL_V1 static verifier contracts.

Does not import production trading modules as a runtime hook.
Uses the CI verifier as a stdlib script only.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER = REPO_ROOT / "scripts" / "ops" / "check_clean_core_seal_v1.py"
MANIFEST = REPO_ROOT / "config" / "governance" / "clean_core_seal_manifest_v1.json"
LINT_GATE = REPO_ROOT / ".github" / "workflows" / "lint_gate.yml"
NEEDLE = "scripts/ops/check_clean_core_seal_v1.py"


def _load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_clean_core_seal_v1", VERIFIER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), *args],
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def _seed_repo(tmp_path: Path) -> Path:
    module = _load_verifier()
    dest_manifest = tmp_path / "config" / "governance" / "clean_core_seal_manifest_v1.json"
    dest_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST, dest_manifest)
    for rel in module.FROZEN_PATHS:
        src = REPO_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    lint = tmp_path / ".github" / "workflows" / "lint_gate.yml"
    lint.parent.mkdir(parents=True, exist_ok=True)
    lint.write_text(
        "\n".join(
            [
                "name: Lint Gate",
                "jobs:",
                "  lint-gate:",
                "    steps:",
                "      - name: Clean Core Seal v1",
                "        if: ${{ steps.reuse_norm.outputs.reuse != 'true' }}",
                f"        run: python {NEEDLE}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return tmp_path


def _errors(proc: subprocess.CompletedProcess[str]) -> list[str]:
    payload = json.loads(proc.stdout)
    return list(payload.get("ERRORS") or [])


class TestCleanCoreSealCurrentCheckpointV1:
    def test_manifest_and_verifier_exist(self) -> None:
        assert VERIFIER.is_file()
        assert MANIFEST.is_file()
        assert LINT_GATE.is_file()

    def test_frozen_census_membership(self) -> None:
        module = _load_verifier()
        assert module.FROZEN_MEMBER_COUNT == 20
        assert sum(1 for m in module.CENSUS_MEMBERS if m["mode"] == module.WHOLE_FILE) == 7
        assert sum(1 for m in module.CENSUS_MEMBERS if m["mode"] == module.MIXED_FILE) == 13
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["schema_version"] == module.SCHEMA_VERSION
        assert manifest["state"] == "SEALED"
        assert manifest["unseal_implemented"] is False
        assert [m["id"] for m in manifest["members"]] == [m["id"] for m in module.CENSUS_MEMBERS]

    def test_current_checkpoint_cli_pass(self) -> None:
        proc = _run_cli()
        assert proc.returncode == 0, proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["CLEAN_CORE_SEAL_V1"] == "PASS"
        assert payload["MEMBER_COUNT"] == 20

    def test_lint_gate_invokes_verifier_and_is_not_applicable_gated(self) -> None:
        text = LINT_GATE.read_text(encoding="utf-8")
        assert NEEDLE in text
        lines = text.splitlines()
        needle_idx = next(i for i, line in enumerate(lines) if NEEDLE in line)
        window = "\n".join(lines[max(0, needle_idx - 12) : needle_idx + 1])
        assert "steps.detect.outputs.applicable" not in window
        assert "steps.reuse_norm.outputs.reuse != 'true'" in window

    def test_verifier_has_no_trading_import(self) -> None:
        source = VERIFIER.read_text(encoding="utf-8")
        assert "from trading" not in source
        assert "import trading" not in source
        assert "src.trading" not in source


class TestCleanCoreSealNegativeAndExtensionV1:
    def test_seeded_repo_passes(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 0, proc.stdout + proc.stderr

    @pytest.mark.parametrize(
        "rel",
        [
            "src/trading/master_v2/double_play_state.py",
            "src/trading/master_v2/survival_assessment_v1.py",
            "src/trading/master_v2/suitability_binding_v1.py",
            "src/trading/master_v2/directional_assessment_confirmation_integration_v1.py",
            "src/trading/master_v2/canonical_market_context_v1.py",
            "src/trading/master_v2/canonical_scope_initialization_v1.py",
            "src/trading/market_state/directional_confirmation_progress_v1.py",
        ],
    )
    def test_whole_file_mutation_fails(self, tmp_path: Path, rel: str) -> None:
        root = _seed_repo(tmp_path)
        target = root / rel
        target.write_text(
            target.read_text(encoding="utf-8") + "\n# seal-mutation\n", encoding="utf-8"
        )
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert any("whole_file_digest_mismatch" in err for err in _errors(proc))

    def test_mixed_protected_symbol_mutation_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        path = root / "src/trading/master_v2/chop_scope_event_policy_binding_v1.py"
        text = path.read_text(encoding="utf-8")
        mutated = text.replace(
            "reason_code=REASON_CHOP_CONTEXT_MISSING_FAIL_CLOSED,",
            "reason_code=REASON_UNKNOWN_NOT_BOUND_FAIL_CLOSED,",
            1,
        )
        assert mutated != text
        path.write_text(mutated, encoding="utf-8")
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert any("protected_ast_digest_mismatch" in err for err in _errors(proc))

    def test_mixed_protected_symbol_rename_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        path = root / "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "def derive_scope_adverse_exit_signal_v0(",
                "def derive_scope_adverse_exit_signal_renamed_v0(",
                1,
            ),
            encoding="utf-8",
        )
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert any("missing_protected_symbol" in err for err in _errors(proc))

    def test_protected_constant_mutation_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        path = (
            root
            / "src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py"
        )
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                "COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE = True",
                "COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE = False",
                1,
            ),
            encoding="utf-8",
        )
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert any("protected_ast_digest_mismatch" in err for err in _errors(proc))

    def test_unlisted_mixed_file_extension_passes(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        path = root / "src/trading/master_v2/chop_scope_event_policy_binding_v1.py"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\n\ndef _unlisted_extension_allowed_v1() -> int:\n    return 1\n",
            encoding="utf-8",
        )
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 0, proc.stdout + proc.stderr

    def test_ddo_decorator_only_change_passes(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        path = root / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
        text = path.read_text(encoding="utf-8")
        mutated = text.replace(
            '@observe_after_producer_v0(seam_id="core.double_play_entry_exit")',
            '@observe_after_producer_v0(seam_id="core.double_play_entry_exit.extension")',
            1,
        )
        assert mutated != text
        path.write_text(mutated, encoding="utf-8")
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 0, proc.stdout + proc.stderr

    def test_replay_unsealed_region_extension_passes(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        path = root / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
        text = path.read_text(encoding="utf-8")
        # Unlisted module-level helper plus an extra unsealed binder-name call
        # inside the already-unsealed 29P region does not change sealed join callees.
        insertion = "\n\ndef _unsealed_replay_downstream_extension_v1() -> None:\n    return None\n"
        marker = (
            "    sizing_binding = _crs_binding.bind_capital_risk_sizing_offline_replay_evidence_v0("
        )
        assert marker in text
        text = text.replace(
            marker,
            "    _unsealed_replay_downstream_extension_v1()\n" + marker,
            1,
        )
        path.write_text(text + insertion, encoding="utf-8")
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 0, proc.stdout + proc.stderr

    def test_manifest_member_removal_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        manifest_path = root / "config" / "governance" / "clean_core_seal_manifest_v1.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["members"] = payload["members"][1:]
        payload["seal_core_count"] = len(payload["members"])
        manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        errors = _errors(proc)
        assert any(
            "membership_count_mismatch" in err or "census_member_removed" in err for err in errors
        )

    def test_manifest_state_weakening_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        manifest_path = root / "config" / "governance" / "clean_core_seal_manifest_v1.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["state"] = "UNSEALED"
        manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert "manifest_state_not_sealed" in _errors(proc)

    def test_manifest_version_weakening_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        manifest_path = root / "config" / "governance" / "clean_core_seal_manifest_v1.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["schema_version"] = "clean_core_seal_manifest_v0"
        manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert "unsupported_manifest_version" in _errors(proc)

    def test_missing_protected_file_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        (root / "src/trading/master_v2/double_play_state.py").unlink()
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert any("missing_protected_path" in err for err in _errors(proc))

    def test_renamed_protected_file_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        src = root / "src/trading/master_v2/double_play_state.py"
        src.rename(src.with_name("double_play_state_renamed.py"))
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert any("missing_protected_path" in err for err in _errors(proc))

    def test_missing_manifest_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        (root / "config" / "governance" / "clean_core_seal_manifest_v1.json").unlink()
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert "missing_manifest" in _errors(proc)

    def test_lint_gate_binding_missing_fails(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path)
        (root / ".github" / "workflows" / "lint_gate.yml").write_text(
            "name: Lint Gate\njobs: {}\n", encoding="utf-8"
        )
        proc = _run_cli("--repo-root", str(root))
        assert proc.returncode == 1
        assert "lint_gate_verifier_not_invoked" in _errors(proc)
