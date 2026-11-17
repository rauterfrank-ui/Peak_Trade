"""Seed the pre-reversal occupied snapshot for original Close-recovery tests."""

from src.ops.p5_productive_layered_core_authority_seam_v1 import seam_v1


def seed_legacy_l10_close_snapshots(monkeypatch):
    persist = seam_v1.persist_layered_core_episode_v1

    def persist_legacy(root, episode, *, occupied_mark=None):
        if occupied_mark is not None:
            occupied_mark = dict(occupied_mark)
            occupied_mark["pending_close_episode_id"] = occupied_mark.pop(
                "pending_reversal_episode_id"
            )
        return persist(root, episode, occupied_mark=occupied_mark)

    monkeypatch.setattr(seam_v1, "persist_layered_core_episode_v1", persist_legacy)
