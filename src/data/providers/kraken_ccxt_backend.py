from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


def _optional_dep_error(symbol: str, exc: ModuleNotFoundError) -> ModuleNotFoundError:
    msg = (
        f"Optional dependency missing while importing '{symbol}'.\n\n"
        f"This backend depends on 'ccxt' (Kraken via ccxt).\n"
        f"Install ccxt (or the project's optional extra that includes ccxt) and retry.\n\n"
        f"Examples:\n"
        f"  pip install ccxt\n"
        f"  # or (if your project defines an extra)\n"
        f'  pip install -e ".[<extra-that-includes-ccxt>]"\n'
    )
    # Cause wird beim raise ... from exc gesetzt.
    return ModuleNotFoundError(msg)


def _to_float(v: Any) -> float:
    if v is None:
        return float("nan")
    return float(v)


@dataclass
class KrakenCcxtBackend:
    """
    Read-only Kraken OHLCV Backend via ccxt.

    Ziele:
    - importierbar ohne ccxt (lazy import in _exchange())
    - nur read-only calls: init, (optional) load_markets, fetch_ohlcv
    - canonical OHLCV output: UTC ms + floats
    """

    api_key: Optional[str] = None
    secret: Optional[str] = None
    enable_rate_limit: bool = True
    timeout_ms: int = 30000

    def __post_init__(self) -> None:
        self._exchange_instance: Any | None = None

    def _exchange(self) -> Any:
        """
        Erstellt (lazy) eine ccxt.kraken Instanz.
        """
        if self._exchange_instance is not None:
            return self._exchange_instance

        try:
            import importlib

            ccxt = importlib.import_module("ccxt")
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise _optional_dep_error("KrakenCcxtBackend", exc)

        cfg: dict[str, Any] = {
            "enableRateLimit": bool(self.enable_rate_limit),
            "timeout": int(self.timeout_ms),
        }
        if self.api_key:
            cfg["apiKey"] = self.api_key
        if self.secret:
            cfg["secret"] = self.secret

        ex = ccxt.kraken(cfg)  # pyright: ignore[reportArgumentType]

        # Optional: load_markets wenn vorhanden (kein harter Fail)
        try:
            if hasattr(ex, "load_markets"):
                ex.load_markets()
        except Exception:
            pass

        self._exchange_instance = ex
        return ex

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since_ms: int | None = None,
        limit: int | None = None,
        recorder: Any | None = None,
    ) -> list[dict]:
        """
        Fetch OHLCV und mappe auf canonical records:
        {"ts_ms": int, "open": float, "high": float, "low": float, "close": float, "volume": float}
        """
        ex = self._exchange()

        # ccxt signature: fetch_ohlcv(symbol, timeframe='1m', since=None, limit=None, params={})
        rows = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)

        out: list[dict] = []
        if not rows:
            return out

        for row in rows:
            # Expect: [timestamp, open, high, low, close, volume]
            ts = int(row[0])
            rec = {
                "ts_ms": ts,
                "open": _to_float(row[1]),
                "high": _to_float(row[2]),
                "low": _to_float(row[3]),
                "close": _to_float(row[4]),
                "volume": _to_float(row[5]),
            }
            out.append(rec)

        # Deterministische Reihenfolge
        out.sort(key=lambda r: r["ts_ms"])

        # Optional recorder hook (record-only, no side effects beyond IO)
        if recorder is not None:
            try:
                recorder.write_batch(out)
            except Exception:
                # Recorder darf nie den Fetch crashen
                pass

        return out


__all__ = ["KrakenCcxtBackend"]
