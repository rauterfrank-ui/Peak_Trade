"""Contract tests for RUNBOOK B execution determinism helpers (seed_u64, SimClock).

Covers src/execution/determinism.py only via imports; production code must stay frozen.
"""

from __future__ import annotations

from src.execution.determinism import SimClock, seed_u64

_U64_MOD = 2**64


def test_seed_u64_same_inputs_equal() -> None:
    a = seed_u64("run_a", "SYM", "intent_1")
    b = seed_u64("run_a", "SYM", "intent_1")
    assert a == b


def test_seed_u64_returns_int_in_unsigned_u64_range() -> None:
    v = seed_u64("any_run", "ANY", "intent_x")
    assert isinstance(v, int)
    assert 0 <= v < _U64_MOD


def test_seed_u64_known_vector_matches_documented_formula() -> None:
    # Frozen material: f"{run_id}|{symbol}|{intent_id}" -> first 8 bytes of SHA-256, big-endian u64
    assert seed_u64("run_2026_042a", "BTCUSDT", "intent_open_001") == 16793980488433191217
    assert seed_u64("run_2026_042b", "BTCUSDT", "intent_open_001") == 883716340634873953
    assert seed_u64("run_2026_042a", "ETHUSDT", "intent_open_001") == 9786139545441831152


def test_seed_u64_meaningful_input_changes_alter_seed() -> None:
    triples = [
        ("r1", "BTC", "i1"),
        ("r2", "BTC", "i1"),
        ("r1", "ETH", "i1"),
        ("r1", "BTC", "i2"),
    ]
    seeds = {seed_u64(*t) for t in triples}
    assert len(seeds) == len(triples)


def test_seed_u64_utf8_strings_use_utf8_encoding() -> None:
    """Delimiter is ASCII; unicode scalars round-trip via UTF-8 material."""
    v = seed_u64("run_umlaut", "symbol_ß", "intent_你好")
    assert isinstance(v, int)
    assert 0 <= v < _U64_MOD
    assert v == seed_u64("run_umlaut", "symbol_ß", "intent_你好")


def test_sim_clock_starts_at_zero_and_ticks_monotonic_unit_steps() -> None:
    clock = SimClock()
    assert clock.tick() == 0
    assert clock.tick() == 1
    assert clock.tick() == 2


def test_sim_clock_independent_instances_do_not_share_state() -> None:
    c1 = SimClock()
    c2 = SimClock()
    assert c1.tick() == c2.tick() == 0
    assert c1.tick() == c2.tick() == 1


def test_sim_clock_recreated_instances_match_sequence() -> None:
    def first_n_ticks(n: int) -> list[int]:
        c = SimClock()
        return [c.tick() for _ in range(n)]

    a = first_n_ticks(6)
    b = first_n_ticks(6)
    assert a == b == [0, 1, 2, 3, 4, 5]
