from pathlib import Path
from src.ops.p91 import P91AuditContextV1, build_shadow_soak_audit_v1


def test_p91_smoke_dict_boundary(tmp_path: Path):
    ctx = P91AuditContextV1(out_dir=tmp_path)
    out = build_shadow_soak_audit_v1(ctx)
    assert isinstance(out, dict)
    assert out["meta"]["version"] == "p91_shadow_soak_audit_v1"
