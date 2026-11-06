#!/usr/bin/env python3
"""
Tests für src.ops.doctor
========================

Testet das Ops Doctor Tool für Repository-Health-Checks.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.ops.doctor import Check, Doctor, DoctorReport


class TestCheck:
    """Tests für Check-Dataclass."""

    def test_check_creation(self):
        """Test: Check kann erstellt werden."""
        check = Check(
            id="test.check",
            severity="warn",
            status="ok",
            message="Test message",
            fix_hint="Test fix",
            evidence=["evidence1", "evidence2"],
        )

        assert check.id == "test.check"
        assert check.severity == "warn"
        assert check.status == "ok"
        assert check.message == "Test message"
        assert check.fix_hint == "Test fix"
        assert len(check.evidence) == 2

    def test_check_to_dict(self):
        """Test: Check kann zu dict konvertiert werden."""
        check = Check(
            id="test.check",
            severity="fail",
            status="fail",
            message="Failed",
        )

        d = check.to_dict()
        assert d["id"] == "test.check"
        assert d["severity"] == "fail"
        assert d["status"] == "fail"
        assert d["message"] == "Failed"


class TestDoctorReport:
    """Tests für DoctorReport."""

    def test_report_creation(self):
        """Test: Report kann erstellt werden."""
        report = DoctorReport()
        assert len(report.checks) == 0
        assert report.timestamp is not None

    def test_add_check(self):
        """Test: Checks können hinzugefügt werden."""
        report = DoctorReport()
        check = Check(id="test", severity="info", status="ok", message="OK")

        report.add_check(check)
        assert len(report.checks) == 1
        assert report.checks[0].id == "test"

    def test_summary(self):
        """Test: Summary zählt Status korrekt."""
        report = DoctorReport()

        report.add_check(Check(id="c1", severity="info", status="ok", message=""))
        report.add_check(Check(id="c2", severity="warn", status="warn", message=""))
        report.add_check(Check(id="c3", severity="fail", status="fail", message=""))
        report.add_check(Check(id="c4", severity="info", status="skip", message=""))

        summary = report.summary()
        assert summary["ok"] == 1
        assert summary["warn"] == 1
        assert summary["fail"] == 1
        assert summary["skip"] == 1

    def test_exit_code(self):
        """Test: Exit Code basiert auf Checks."""
        report = DoctorReport()

        # Alle OK → Exit 0
        report.add_check(Check(id="c1", severity="info", status="ok", message=""))
        assert report.exit_code() == 0

        # Warnings → Exit 2
        report.add_check(Check(id="c2", severity="warn", status="warn", message=""))
        assert report.exit_code() == 2

        # Failures → Exit 1
        report.add_check(Check(id="c3", severity="fail", status="fail", message=""))
        assert report.exit_code() == 1

    def test_to_dict(self):
        """Test: Report kann zu dict konvertiert werden."""
        report = DoctorReport()
        report.add_check(Check(id="test", severity="info", status="ok", message="OK"))

        d = report.to_dict()
        assert d["tool"] == "ops_inspector"
        assert d["mode"] == "doctor"
        assert "timestamp" in d
        assert "summary" in d
        assert "checks" in d
        assert len(d["checks"]) == 1


class TestDoctor:
    """Tests für Doctor-Klasse."""

    def test_doctor_creation(self):
        """Test: Doctor kann mit repo_root erstellt werden."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            doctor = Doctor(repo_root)
            assert doctor.repo_root == repo_root
            assert len(doctor.report.checks) == 0

    def test_check_git_root_success(self):
        """Test: check_git_root erkennt Git-Repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            git_dir = repo_root / ".git"
            git_dir.mkdir()

            doctor = Doctor(repo_root)
            doctor.check_git_root()

            assert len(doctor.report.checks) == 1
            check = doctor.report.checks[0]
            assert check.id == "repo.git_root"
            assert check.status == "ok"

    def test_check_git_root_failure(self):
        """Test: check_git_root erkennt fehlendes Git-Repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            doctor = Doctor(repo_root)
            doctor.check_git_root()

            assert len(doctor.report.checks) == 1
            check = doctor.report.checks[0]
            assert check.id == "repo.git_root"
            assert check.status == "fail"
            assert "git init" in check.fix_hint

    def test_check_pyproject_toml_missing(self):
        """Test: check_pyproject_toml erkennt fehlende Datei."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            doctor = Doctor(repo_root)
            doctor.check_pyproject_toml()

            assert len(doctor.report.checks) == 1
            check = doctor.report.checks[0]
            assert check.id == "config.pyproject"
            assert check.status == "fail"

    def test_check_pyproject_toml_valid(self):
        """Test: check_pyproject_toml erkennt valide Datei."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            pyproject = repo_root / "pyproject.toml"

            pyproject.write_text(
                """
[project]
name = "test_project"
version = "0.1.0"
"""
            )

            doctor = Doctor(repo_root)
            doctor.check_pyproject_toml()

            assert len(doctor.report.checks) == 1
            check = doctor.report.checks[0]
            assert check.id == "config.pyproject"
            assert check.status == "ok"
            assert "test_project" in check.message

    def test_check_config_files_missing(self):
        """Test: check_config_files erkennt fehlendes config/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            doctor = Doctor(repo_root)
            doctor.check_config_files()

            assert len(doctor.report.checks) == 1
            check = doctor.report.checks[0]
            assert check.id == "config.files"
            assert check.status == "skip"

    def test_check_config_files_ok(self):
        """Test: check_config_files erkennt vorhandene Configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_dir = repo_root / "config"
            config_dir.mkdir()

            (config_dir / "default.toml").write_text("[test]")
            (config_dir / "config.toml").write_text("[test]")

            doctor = Doctor(repo_root)
            doctor.check_config_files()

            assert len(doctor.report.checks) == 1
            check = doctor.report.checks[0]
            assert check.id == "config.files"
            assert check.status == "ok"

    def test_check_test_infrastructure_ok(self):
        """Test: check_test_infrastructure erkennt Test-Setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            (repo_root / "pytest.ini").write_text("[pytest]")

            tests_dir = repo_root / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_example.py").write_text("def test_foo(): pass")

            doctor = Doctor(repo_root)
            doctor.check_test_infrastructure()

            assert len(doctor.report.checks) == 1
            check = doctor.report.checks[0]
            assert check.id == "tests.infrastructure"
            assert check.status == "ok"

    def test_run_specific_checks(self):
        """Test: run_specific_checks führt nur gewählte Checks aus."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            git_dir = repo_root / ".git"
            git_dir.mkdir()

            doctor = Doctor(repo_root)
            report = doctor.run_specific_checks(["repo.git_root"])

            assert len(report.checks) == 1
            assert report.checks[0].id == "repo.git_root"

    def test_run_specific_checks_unknown(self):
        """Test: run_specific_checks überspringt unbekannte Checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            doctor = Doctor(repo_root)
            report = doctor.run_specific_checks(["unknown.check"])

            assert len(report.checks) == 1
            check = report.checks[0]
            assert check.id == "unknown.check"
            assert check.status == "skip"
            assert "Unknown check" in check.message

    def test_report_to_json(self):
        """Test: Report kann als JSON exportiert werden."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            doctor = Doctor(repo_root)
            doctor.check_git_root()

            report_dict = doctor.report.to_dict()
            json_str = json.dumps(report_dict, indent=2)

            assert "ops_inspector" in json_str
            assert "doctor" in json_str
            assert "repo.git_root" in json_str


@pytest.mark.smoke
def test_doctor_smoke():
    """Smoke Test: Doctor kann ausgeführt werden."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Minimales Setup
        git_dir = repo_root / ".git"
        git_dir.mkdir()

        doctor = Doctor(repo_root)
        report = doctor.run_all_checks()

        assert len(report.checks) > 0
        assert report.exit_code() in [0, 1, 2]
