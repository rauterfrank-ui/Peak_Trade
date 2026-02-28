"""Smoke: P4CCapsule schema loads and has expected symbol."""


def test_capsule_schema_has_expected_symbol() -> None:
    m = __import__("src.aiops.p4c.capsule_schema", fromlist=["P4CCapsule"])
    assert hasattr(m, "P4CCapsule")
