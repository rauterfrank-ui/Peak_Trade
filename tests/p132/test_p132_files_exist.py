from pathlib import Path


def test_p132_docs_exist():
    assert Path("docs/analysis/p132/README.md").is_file()


def test_p132_tests_exist():
    assert Path("tests/p132/test_p132_transport_allow_handshake_v1.py").is_file()
