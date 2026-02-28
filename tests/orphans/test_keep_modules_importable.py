"""Minimal import smoke for orphan KEEP modules."""

import importlib


def test_import_switch_layer_hook_v1() -> None:
    importlib.import_module("src.ai_orchestration.switch_layer_hook_v1")


def test_import_capsule_schema() -> None:
    importlib.import_module("src.aiops.p4c.capsule_schema")


def test_import_ai_execution_gate() -> None:
    importlib.import_module("src.ops.ai_execution_gate")


def test_import_portfolio_psychology() -> None:
    importlib.import_module("src.reporting.portfolio_psychology")


def test_import_shadow_jsonl_logger() -> None:
    importlib.import_module("src.data.shadow.jsonl_logger")
