"""Scoped, passive observation of the original final Master V2 input.

Disabled by default. The observer receives a detached copy and cannot change
the input consumed by the decision owner. No trading or persistence authority.
"""

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from copy import copy, deepcopy
from dataclasses import fields, is_dataclass
from typing import Any


_observer: ContextVar[Callable[[Any], None] | None] = ContextVar(
    "instrument_card_input_observer_v1", default=None
)


def _detached(value):
    # Governed seam records contain MappingProxyType: deepcopy cannot pickle
    # those. Copy mappings recursively while keeping DTO types and enum values.
    if is_dataclass(value) and not isinstance(value, type):
        result = copy(value)
        for field in fields(value):
            object.__setattr__(result, field.name, _detached(getattr(value, field.name)))
        return result
    if isinstance(value, Mapping):
        return {key: _detached(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_detached(item) for item in value)
    if isinstance(value, list):
        return [_detached(item) for item in value]
    return deepcopy(value)


@contextmanager
def observe_instrument_card_input_v1(observer: Callable[[Any], None]) -> Iterator[None]:
    token = _observer.set(observer)
    try:
        yield
    finally:
        _observer.reset(token)


def record_instrument_card_input_v1(replay_input: Any) -> None:
    observer = _observer.get()
    if observer is not None:
        observer(_detached(replay_input))
