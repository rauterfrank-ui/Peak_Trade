import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md"


def test_canonical_matrix_path_exists():
    assert CANONICAL.is_file(), f"Missing canonical matrix file: {CANONICAL}"
