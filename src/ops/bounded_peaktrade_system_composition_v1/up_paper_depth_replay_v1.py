"""Receipt-ordered replay of one public UP mark-price/books connection epoch."""

import json
import zlib
from collections import Counter
from dataclasses import dataclass, replace
from decimal import Decimal, DecimalException
from hashlib import sha256

from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import PaperBookV1
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    PUBLIC_V1_BEST_BID_ASK_MAX_AGE_SECONDS,
    PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS,
)

MS = 10**6
SECOND = 10**9
AGE = {
    "mark-price": PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS * SECOND,
    "books": PUBLIC_V1_BEST_BID_ASK_MAX_AGE_SECONDS * SECOND,
}


def _integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("invalid nonnegative integer")
    return value


def _event_ms(row):
    raw = row["ts"]
    if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal() or int(raw) == 0:
        raise ValueError("invalid exchange event timestamp")
    return int(raw)


@dataclass(frozen=True)
class Observation:
    event_ms: int
    received_ns: int
    frame: int
    value: object

    def until(self, channel):
        return self.event_ms * MS + AGE[channel] + 1


class Depth:
    def __init__(self, tick, lot):
        self.tick, self.lot = tick, lot
        self.levels = {"bids": {}, "asks": {}}
        self.seq = None
        self.snapshot_frame = None
        self.checksum_status = None

    def update(self, action, row, frame):
        seq = _integer(row["seqId"])
        prev = row.get("prevSeqId")
        if action == "snapshot":
            if prev not in (-1, None):
                raise ValueError("unexpected snapshot predecessor")
            self.levels = {"bids": {}, "asks": {}}
            self.snapshot_frame = frame
        elif action == "update":
            if self.seq is None or type(prev) is not int or self.seq != prev or seq < prev:
                raise ValueError("book sequence break; fresh snapshot required")
            if seq == prev and (row["bids"] or row["asks"]):
                raise ValueError("book changes without sequence advance")
        else:
            raise ValueError("unexpected book action")

        ordered = {}
        for side, levels in self.levels.items():
            changes = row[side]
            if not isinstance(changes, list):
                raise ValueError("malformed depth side")
            seen = set()
            for level in changes:
                if not isinstance(level, list) or len(level) < 2:
                    raise ValueError("malformed depth level")
                px, sz = level[:2]
                if not isinstance(px, str) or not isinstance(sz, str):
                    raise ValueError("non-original depth value")
                price, size = Decimal(px), Decimal(sz)
                if (
                    not price.is_finite()
                    or not size.is_finite()
                    or price <= 0
                    or size < 0
                    or price % self.tick
                    or size % self.lot
                    or price in seen
                    or (action == "snapshot" and size == 0)
                ):
                    raise ValueError("invalid order-book grid or repeated level")
                seen.add(price)
                if size:
                    levels[price] = (px, sz)
                else:
                    levels.pop(price, None)
            keys = sorted(levels, reverse=side == "bids")
            for price in keys[400:]:
                del levels[price]
            ordered[side] = [levels[price] for price in keys[:50]]
        checksum = row.get("checksum")
        self.checksum_status = "absent" if checksum is None else "zero_unverified"
        if checksum is not None and type(checksum) is not int:
            raise ValueError("invalid book checksum")
        if checksum:
            # OKX hashes original price/size spellings, alternating bid then ask by rank.
            fields = []
            for i in range(25):
                for side in ("bids", "asks"):
                    if i < len(ordered[side]):
                        fields.extend(ordered[side][i])
            if zlib.crc32(":".join(fields).encode()) != checksum % (1 << 32):
                raise ValueError("book checksum mismatch")
            self.checksum_status = "verified"
        book = PaperBookV1.from_okx_v1(ordered, tick=self.tick, lot=self.lot)
        unchanged = action == "update" and seq == self.seq
        self.seq = seq
        return None if unchanged else book


class Pair:
    def __init__(self, plan, window):
        self.subscriptions = {item["channel"]: item for item in plan["subscriptions"]}
        self.native = plan["identity"]["native_id"]
        self.acked = set()
        self.data = {}
        self.watermark = {}
        self.depth = Depth(window.liquidity.tick_size, window.liquidity.lot_size)
        self.errors = {}
        self.terminal = None

    def accept(self, raw, received, frame):
        if self.terminal or raw == "pong":
            return False
        try:
            msg = json.loads(raw)
        except (TypeError, ValueError):
            self.terminal = "invalid public WebSocket message"
            return False
        if not isinstance(msg, dict):
            self.terminal = "invalid public WebSocket message"
            return False
        event = msg.get("event")
        if event == "notice" and msg.get("code") == "64010":
            return False
        arg = msg.get("arg") or {}
        channel = arg.get("channel") if isinstance(arg, dict) else None
        if channel not in self.subscriptions or arg.get("instId") != self.native:
            self.terminal = "unexpected subscription or connection event"
            return False
        if event == "subscribe" and channel not in self.acked:
            self.acked.add(channel)
            return False
        if event is not None or channel not in self.acked:
            self.terminal = "unconfirmed or interrupted subscription"
            return False
        changed = False
        try:
            rows = msg["data"]
            if not isinstance(rows, list) or not rows:
                raise ValueError("empty data frame")
            for row in rows:
                ts = _event_ms(row)
                if ts < self.watermark.get(channel, 0) or ts * MS > received:
                    raise ValueError("regressing or future exchange timestamp")
                if row.get("instId", self.native) != self.native:
                    raise ValueError("instrument mismatch")
                if channel == "mark-price":
                    if (row["instId"], row["instType"]) != (self.native, "FUTURES"):
                        raise ValueError("wrong mark instrument")
                    value = Decimal(row["markPx"])
                    if not value.is_finite() or value <= 0:
                        raise ValueError("invalid mark price")
                    old = self.data.get(channel)
                    if old and (ts, value) == (old.event_ms, old.value):
                        continue
                else:
                    if msg["action"] == "snapshot" and "books" in self.data:
                        self.data.pop("mark-price", None)
                    value = self.depth.update(msg["action"], row, frame)
                    if value is None:
                        continue
                self.data[channel] = Observation(ts, received, frame, value)
                self.watermark[channel] = ts
                self.errors.pop(channel, None)
                changed = True
        except (KeyError, TypeError, IndexError, DecimalException, ValueError) as exc:
            self.data.pop(channel, None)
            self.errors[channel] = str(exc)
            if channel == "books":
                self.depth.seq = None
                self.data.pop("mark-price", None)
            return False
        return changed

    def unavailable(self, signal_ms):
        if self.terminal:
            return self.terminal
        for channel in ("mark-price", "books"):
            if channel in self.errors:
                return self.errors[channel]
            if channel not in self.data:
                return f"awaiting {channel} " + (
                    "data" if channel in self.acked else "acknowledgement"
                )
        if self.data["mark-price"].event_ms < signal_ms:
            return "mark predates original signal"
        return None


class Comparison:
    def __init__(self, window, plan, discontinuities):
        self.window = window
        self.pair = Pair(plan, window)
        self.gaps = []
        self.counts = Counter()
        self.first = None
        self.last_assessed_ns = None
        self.latest = {}
        self.longest_spacing = {}
        self.discontinuities = iter(discontinuities)
        self.next_break = next(self.discontinuities, None)

    def book_break(self, moment):
        while self.next_break and self.next_break[1] <= moment:
            self.next_break = next(self.discontinuities, None)
        return self.next_break

    def gap(self, a, b, reason):
        a, b = max(a, self.window.start_ns), min(b, self.window.end_ns)
        if a >= b:
            return
        if self.gaps and self.gaps[-1]["until_ns"] == a and self.gaps[-1]["reason"] == reason:
            self.gaps[-1]["until_ns"] = b
        else:
            self.gaps.append(dict(from_ns=a, until_ns=b, reason=reason))

    def fresh_until(self):
        return min((value.until(channel), channel) for channel, value in self.pair.data.items())

    def interval(self, a, b):
        start, end = max(a, self.window.start_ns), min(b, self.window.end_ns)
        while start < end:
            gap = self.book_break(start)
            if gap is None or end <= gap[0]:
                self.paired_interval(start, end)
                return
            self.paired_interval(start, min(end, gap[0]))
            self.gap(max(start, gap[0]), min(end, gap[1]), gap[2])
            start = gap[1]

    def paired_interval(self, start, end):
        if start >= end:
            return
        reason = self.pair.unavailable(self.window.signal_ms)
        if reason:
            self.gap(start, end, reason)
            return
        until, channel = self.fresh_until()
        self.gap(max(start, until), end, f"{channel} freshness expired")
        if start == self.window.start_ns and start < until and self.last_assessed_ns != start:
            self.assess(start)

    def assess(self, now):
        if not self.window.start_ns <= now < self.window.end_ns:
            return
        gap = self.book_break(now)
        if gap and gap[0] <= now < gap[1]:
            return
        if self.pair.unavailable(self.window.signal_ms) or now >= self.fresh_until()[0]:
            return
        self.last_assessed_ns = now
        mark, book = self.pair.data["mark-price"], self.pair.data["books"]
        depth = book.value
        book_hash = canonical_book_digest(depth)
        snap = replace(
            self.window.liquidity,
            mark=mark.value,
            book=depth,
            book_event_unix=book.event_ms / 1000,
            source_hashes={**self.window.liquidity.source_hashes, "book": book_hash},
        )
        check = snap.assess_quantity_v1(side=self.window.side, quantity=self.window.quantity)
        self.counts["evaluated"] += 1
        for reason in check["reason_codes"]:
            self.counts[reason] += 1
        if check["risk_admitted"]:
            self.counts["liquidity_pass"] += 1
            if self.first is None:
                self.first = dict(
                    known_at_ns=now,
                    before_execution_mark_ms=(self.window.end_ns - now) / MS,
                    mark_px=str(mark.value),
                    mark_event_ms=mark.event_ms,
                    book_event_ms=book.event_ms,
                    mark_received_ns=mark.received_ns,
                    book_received_ns=book.received_ns,
                    mark_minus_book_ms=mark.event_ms - book.event_ms,
                    mark_frame=mark.frame,
                    book_frame=book.frame,
                    book_seq_id=self.pair.depth.seq,
                    book_snapshot_frame=self.pair.depth.snapshot_frame,
                    checksum=self.pair.depth.checksum_status,
                    top50_content_sha256=book_hash,
                    liquidity=check,
                )

    def frame(self, raw, now, index):
        changed = self.pair.accept(raw, now, index)
        if not changed:
            return
        for channel, obs in self.pair.data.items():
            if obs.frame == index:
                previous = self.latest.get(channel)
                if previous:
                    gap = min(now, self.window.end_ns) - max(
                        previous.received_ns, self.window.start_ns
                    )
                    if gap > self.longest_spacing.get(channel, {}).get("inside_window_ns", 0):
                        self.longest_spacing[channel] = dict(
                            inside_window_ns=gap,
                            receipt_spacing_ns=now - previous.received_ns,
                            event_spacing_ms=obs.event_ms - previous.event_ms,
                            from_frame=previous.frame,
                            until_frame=index,
                        )
                self.latest[channel] = obs
        self.assess(now)


def canonical_book_digest(book):
    values = [[[str(p), str(q)] for p, q in levels] for levels in (book.bids, book.asks)]
    return sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def sealed_digest(digest, footer):
    sealed = digest.copy()
    sealed.update(json.dumps(footer, sort_keys=True, separators=(",", ":")).encode())
    return sealed.hexdigest()


def _read_recording(recording, plan, *, on_start, on_frame, on_end):
    digest = sha256()
    count = 0
    with recording.open("rb") as stream:
        header = stream.readline()
        start = json.loads(header)
        if start.get("kind") != "start" or any(start.get(k) != v for k, v in plan.items()):
            raise ValueError("joint UP Paper recording and original ranked binding required")
        if start.get("source") not in {"public_websocket", "offline_fixture"}:
            raise ValueError("unknown recording provenance")
        digest.update(header)
        first = previous = _integer(start["received_ns"])
        mono = _integer(start["received_mono_ns"])
        on_start(first)
        for line in stream:
            row = json.loads(line)
            now, current_mono = _integer(row["received_ns"]), _integer(row["received_mono_ns"])
            if now < previous or current_mono < mono:
                raise ValueError("recording clocks regressed")
            if row["kind"] == "end":
                footer = {
                    key: value
                    for key, value in row.items()
                    if key not in {"kind", "content_sha256"}
                }
                if (
                    row["content_sha256"] != sealed_digest(digest, footer)
                    or row["frames"] != count
                    or stream.read(1)
                ):
                    raise ValueError("recording footer or content digest mismatch")
                on_end(previous, now)
                break
            count += 1
            if row["kind"] != "frame" or row["frame"] != count:
                raise ValueError("missing or unordered raw frame")
            digest.update(line)
            on_frame(previous, now, count, row["raw"])
            previous, mono = now, current_mono
        else:
            raise ValueError("incomplete recording: no sealed end or verified frame count")
    return dict(
        content_sha256=row["content_sha256"],
        source=start["source"],
        transport_version=start["transport_version"],
        clock_host=start["clock_host"],
        frames=count,
        from_ns=first,
        until_ns=now,
        end_status=row["status"],
    )


def compare_recording(recording, plan, window):
    # A missing delta is only detectable on a later frame. Mark updates in the
    # intervening interval cannot prove a pass using the last retained book.
    inspector = Pair(plan, window)
    breaks = []

    def inspect(previous, now, count, raw):
        old_book = inspector.data.get("books")
        inspector.accept(raw, now, count)
        if old_book and old_book.received_ns < now:
            reason = inspector.errors.get("books")
            if inspector.depth.snapshot_frame == count:
                reason = "new book snapshot without a continuous update chain"
            if reason:
                breaks.append((old_book.received_ns + 1, now, reason))

    original = _read_recording(
        recording, plan, on_start=lambda _: None, on_frame=inspect, on_end=lambda *_: None
    )
    comparison = Comparison(window, plan, breaks)

    def frame(previous, now, count, raw):
        comparison.interval(previous, now)
        comparison.frame(raw, now, count)

    def end(previous, now):
        comparison.interval(previous, now)
        comparison.gap(now, window.end_ns, "outside recording")

    verified = _read_recording(
        recording,
        plan,
        on_start=lambda now: comparison.gap(window.start_ns, now, "outside recording"),
        on_frame=frame,
        on_end=end,
    )
    if verified != original:
        raise ValueError("recording changed during comparison")
    if comparison.first is not None:
        comparison.first["source"] = verified["source"]
    return dict(
        scope="observed liquidity for fixed original native reversal quantity",
        clock_basis="host UTC receipt versus exchange UTC event (clock offset unmeasured)",
        freshness_seconds={channel: age // SECOND for channel, age in AGE.items()},
        decision_id=window.decision_id,
        signal_mark_ms=window.signal_ms,
        side=window.side,
        quantity_contracts=str(window.quantity),
        from_ns=window.start_ns,
        until_ns=window.end_ns,
        end_basis="original execution-input mark exchange time (exclusive)",
        original_evidence=window.evidence,
        identity=plan["identity"],
        recording=dict(
            **verified,
            acknowledged=sorted(comparison.pair.acked),
            protocol_error=comparison.pair.terminal,
        ),
        assessment_counts=dict(comparison.counts),
        first_observed_liquidity_pass=comparison.first,
        longest_inter_observation_spacing=comparison.longest_spacing,
        unassessable_intervals=comparison.gaps,
    )
