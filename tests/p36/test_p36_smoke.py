def test_import_smoke() -> None:
    from src.backtest.p36 import (
        read_bundle_tarball_v1,
        verify_bundle_tarball_v1,
        write_bundle_tarball_v1,
    )  # noqa: F401
