/**
 * Market Dashboard Landscape V2 — presentation-only client helpers.
 * No fetch mutation, no decision/risk/sizing logic, no write endpoints.
 * Renders materialized OHLCV from SSR/poll JSON only (never fabricates candles).
 * Canonical Landscape shell host: GET /market is HTML SSR — do not JSON-bootstrap
 * that document. Continuous refresh uses GET /api/market/landscape/ohlcv only.
 * Optional supervised hosts may expose JSON at GET /market from a non-shell page;
 * that host must not be required for the canonical shell contract.
 * Never calls OKX or any browser-direct network venue.
 *
 * Canonical OHLCV accepted from body.ohlcv and/or body.read_model (and legacy
 * body.browser_payload when present). Candle close is never used as live mark.
 *
 * Update classification:
 *   NO_CHANGE | METADATA_ONLY | MARK_ONLY | SAME_TIMESTAMP_LAST_CANDLE_CHANGE
 *   | NEW_CANDLE_APPEND | HISTORICAL_SERIES_CHANGE | SCALE_DOMAIN_ESCAPE
 *
 * Candle geometry keys off candle_series_digest (authentic O/H/L/C only).
 * Mark and captured_at never trigger full-series redraw.
 * Canvas CSS size is CSS-owned; JS only sets backing-store width/height.
 */
(function () {
  "use strict";
  var root = document.querySelector('[data-market-landscape-v2="true"]');
  if (!root) return;

  var chartLayout = null;
  var volumeLayout = null;
  var lastBars = null;
  var lastCandleSeriesDigest = "";
  var lastMetadataDigest = "";
  var lastMark = null;
  // Presentation-only poll-close baseline for authentic last-price delta (not a signal).
  var lastPricePollClose = null;
  var lastPricePollTs = null;
  var chartInstanceId = "mdl-chart-" + String(Date.now());

  var engineering = root.querySelector("[data-mdl-engineering]");
  if (engineering) {
    engineering.addEventListener("toggle", function () {
      root.setAttribute(
        "data-mdl-engineering-open",
        engineering.open ? "true" : "false"
      );
    });
  }

  // Primary landscape composition assumes the diagnostic drawer starts closed.
  if (engineering && engineering.open) {
    engineering.open = false;
  }

  root.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    if (engineering && engineering.open) {
      engineering.open = false;
      var summary = engineering.querySelector("summary");
      if (summary) summary.focus();
    }
  });

  function markBlank(canvas, reason) {
    if (!canvas) return;
    canvas.setAttribute("data-mdl-chart-geometry", "absent");
    canvas.setAttribute("data-mdl-chart-blank", "true");
    canvas.setAttribute("data-mdl-chart-bar-count", "0");
    if (reason) canvas.setAttribute("data-mdl-chart-error", reason);
    clearLastPriceMarker(canvas);
    markVolumeBlank(reason || "chart_blank");
  }

  function markVolumeBlank(reason) {
    var panel = root.querySelector("[data-mdl-volume-panel]");
    var canvas = root.querySelector("[data-mdl-volume-canvas]");
    volumeLayout = null;
    if (panel) {
      panel.setAttribute("data-mdl-volume-synced-with-chart", "false");
    }
    if (canvas) {
      canvas.setAttribute("data-mdl-volume-geometry", "absent");
      canvas.setAttribute("data-mdl-volume-bar-count", "0");
      if (reason) canvas.setAttribute("data-mdl-volume-error", reason);
      var ctx = canvas.getContext("2d");
      if (ctx) {
        var box = resolveCssBox(canvas, canvas.parentElement);
        syncBackingStore(canvas, box.cssWidth, box.cssHeight);
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  }

  function setVolumePanelState(state, message) {
    var panel = root.querySelector("[data-mdl-volume-panel]");
    var label = root.querySelector("[data-mdl-volume-state-label]");
    var msg = root.querySelector("[data-mdl-volume-message]");
    var token = String(state || "MISSING_SOURCE");
    if (panel) panel.setAttribute("data-mdl-volume-state", token);
    if (label) {
      label.textContent = token;
      label.setAttribute("data-mdl-volume-state", token);
    }
    if (msg) msg.textContent = message ? String(message) : "";
  }

  function setConnectionState(state) {
    var node = root.querySelector(".mdl-v2-chart__chrome [data-mdl-data-connection-state]");
    if (node) {
      node.textContent = state;
      node.setAttribute("data-connection-state", state);
    }
    root.setAttribute("data-mdl-data-connection-state", state);
  }

  // --- connection-state fail-closed helpers (begin) ---
  // Poll arming and poll payloads must never invent HEALTHY from availability,
  // timer start, or missing payload fields. Preserve existing DOM truth or
  // fail closed to MISSING_SOURCE.
  function normalizeConnectionStateToken(raw) {
    var state = String(raw || "").trim();
    if (!state) return "";
    if (state === "LIVE_DATA") return "HEALTHY";
    if (
      state === "HEALTHY" ||
      state === "DEGRADED" ||
      state === "DISCONNECTED" ||
      state === "MISSING_SOURCE" ||
      state === "STALE"
    ) {
      return state;
    }
    return "";
  }

  function readExistingConnectionState() {
    var node = root.querySelector(
      ".mdl-v2-chart__chrome [data-mdl-data-connection-state]"
    );
    var fromNode = "";
    if (node) {
      fromNode = node.getAttribute("data-connection-state") || "";
      if (!fromNode && node.textContent) fromNode = String(node.textContent);
    }
    var fromRoot = root.getAttribute("data-mdl-data-connection-state") || "";
    return (
      normalizeConnectionStateToken(fromNode) ||
      normalizeConnectionStateToken(fromRoot)
    );
  }

  function resolveConnectionStateForPollPayload(body) {
    var payloadRaw =
      (body && (body.connection_state || body.data_connection_state)) || "";
    var fromPayload = normalizeConnectionStateToken(payloadRaw);
    if (fromPayload) return fromPayload;
    var existing = readExistingConnectionState();
    if (existing) return existing;
    return "MISSING_SOURCE";
  }
  // --- connection-state fail-closed helpers (end) ---

  function setUpdateClass(kind) {
    root.setAttribute("data-mdl-ohlcv-update-class", kind);
  }

  function failVisible(reason) {
    root.setAttribute("data-mdl-canonical-fail", "true");
    root.setAttribute("data-mdl-canonical-fail-reason", String(reason || "canonical_unavailable"));
    setConnectionState("MISSING_SOURCE");
    setVolumePanelState(
      "MISSING_SOURCE",
      "Volume MISSING_SOURCE — canonical OHLCV unavailable; no fabricated volume bars."
    );
    markVolumeBlank(String(reason || "canonical_unavailable"));
    var message = root.querySelector("[data-mdl-chart-message]");
    if (message) {
      message.textContent = "CANONICAL_DATA_UNAVAILABLE: " + String(reason || "unknown");
    }
  }

  function clearFailVisible() {
    root.removeAttribute("data-mdl-canonical-fail");
    root.removeAttribute("data-mdl-canonical-fail-reason");
    var message = root.querySelector("[data-mdl-chart-message]");
    if (message) {
      var text = String(message.textContent || "");
      if (text.indexOf("CANONICAL_DATA_UNAVAILABLE:") === 0) {
        // Successful poll / SSR recovery must fully clear the fail-visible text.
        message.textContent = "";
      }
    }
  }

  function clientDigest(text) {
    // Client-only FNV-1a 32-bit digest for update classification — not authority.
    var h = 2166136261;
    var i;
    for (i = 0; i < text.length; i += 1) {
      h ^= text.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return ("00000000" + (h >>> 0).toString(16)).slice(-8);
  }

  function finiteBarNumber(raw) {
    if (raw === undefined || raw === null || raw === "") return null;
    var n = Number(raw);
    return Number.isFinite(n) ? n : null;
  }

  function usableVolumeValue(raw) {
    // Finite non-negative only — never invent zeros for missing/invalid volume.
    var n = finiteBarNumber(raw);
    if (n === null || n < 0) return null;
    return n;
  }

  function classifyVolumeBarDirection(openV, closeV) {
    // Candle direction for volume styling — not buy/sell volume semantics.
    if (closeV > openV) return "up";
    if (closeV < openV) return "down";
    return "neutral";
  }

  function volumeDirectionColor(direction) {
    if (direction === "up") return "#34d399";
    if (direction === "down") return "#f87171";
    return "#94a3b8";
  }

  function resolveVolumePanelState(payload, bars) {
    if (!payload || !Array.isArray(bars) || !bars.length) {
      return {
        state: "MISSING_SOURCE",
        message: "Volume MISSING_SOURCE — no OHLCV volume field in existing payload.",
      };
    }
    var usable = 0;
    var missing = 0;
    var invalid = 0;
    var i;
    for (i = 0; i < bars.length; i += 1) {
      var row = bars[i] || {};
      var raw = row.volume;
      if (raw === undefined || raw === null || raw === "") {
        missing += 1;
        continue;
      }
      if (usableVolumeValue(raw) === null) {
        invalid += 1;
        continue;
      }
      usable += 1;
    }
    if (usable === 0 && missing === bars.length) {
      return {
        state: "MISSING_SOURCE",
        message: "Volume MISSING_SOURCE — volume field absent on all bars.",
      };
    }
    if (usable === 0) {
      return {
        state: "NOT_BOUND",
        message:
          "Volume NOT_BOUND — volume present but not usable in presentation binding.",
      };
    }
    var freshness = String(payload.freshness_state || "").toLowerCase();
    var isStale = payload.is_stale === true || freshness === "stale";
    if (isStale) {
      return {
        state: "STALE",
        message:
          "Volume STALE — canonical OHLCV freshness reports stale; bars retained.",
      };
    }
    return {
      state: "AVAILABLE",
      message: "",
    };
  }

  function normalizeCanonicalBars(rawBars) {
    if (!Array.isArray(rawBars) || !rawBars.length) return null;
    var bars = [];
    var i;
    for (i = 0; i < rawBars.length; i += 1) {
      var row = rawBars[i];
      if (!row || typeof row !== "object") return null;
      var ts = row.ts;
      if (typeof ts !== "string" || !ts.trim()) return null;
      var openV = finiteBarNumber(row.open);
      var highV = finiteBarNumber(row.high);
      var lowV = finiteBarNumber(row.low);
      var closeV = finiteBarNumber(row.close);
      var volumeV = finiteBarNumber(row.volume);
      if (openV === null || highV === null || lowV === null || closeV === null || volumeV === null) {
        return null;
      }
      var confirmRaw = row.confirm;
      var confirm =
        confirmRaw === undefined || confirmRaw === null
          ? true
          : typeof confirmRaw === "boolean"
            ? confirmRaw
            : String(confirmRaw) === "1" || String(confirmRaw) === "true";
      bars.push({
        ts: ts.trim(),
        open: openV,
        high: highV,
        low: lowV,
        close: closeV,
        volume: volumeV,
        display_close: closeV,
        display_high: highV,
        display_low: lowV,
        confirm: confirm,
        provisional: !confirm,
      });
    }
    return bars;
  }

  function pickCanonicalOhlcvSource(body) {
    if (!body || typeof body !== "object") return null;
    if (
      body.browser_payload &&
      Array.isArray(body.browser_payload.bars) &&
      body.browser_payload.bars.length
    ) {
      return { kind: "browser_payload", source: body.browser_payload };
    }
    if (body.ohlcv && Array.isArray(body.ohlcv.bars) && body.ohlcv.bars.length) {
      return { kind: "ohlcv", source: body.ohlcv };
    }
    if (body.read_model && Array.isArray(body.read_model.bars) && body.read_model.bars.length) {
      return { kind: "read_model", source: body.read_model };
    }
    var proj = body.read_model && body.read_model.ohlcv_projection;
    if (proj && Array.isArray(proj.bars) && proj.bars.length) {
      return { kind: "ohlcv_projection", source: proj };
    }
    return null;
  }

  function buildClientPayloadFromCanonical(source, body, kind) {
    // Prefer already-normalized browser_payload bars/digests when present.
    if (kind === "browser_payload") {
      var legacy = Object.assign({}, source);
      // Never invent live mark from candle close.
      if (legacy.live_mark_price === undefined) {
        legacy.live_mark_price = null;
      }
      if (!legacy.first_timestamp && Array.isArray(legacy.bars) && legacy.bars.length) {
        legacy.first_timestamp = legacy.bars[0].ts;
      }
      if (!legacy.last_timestamp && Array.isArray(legacy.bars) && legacy.bars.length) {
        legacy.last_timestamp = legacy.bars[legacy.bars.length - 1].ts;
      }
      return legacy;
    }
    var bars = normalizeCanonicalBars(source.bars);
    if (!bars) return null;
    var rm = (body && body.read_model) || {};
    var seriesKey = bars
      .map(function (b) {
        return [b.ts, b.open, b.high, b.low, b.close, b.volume, b.confirm ? 1 : 0].join(",");
      })
      .join("|");
    var markRaw =
      source.live_mark_price !== undefined && source.live_mark_price !== null
        ? source.live_mark_price
        : rm.live_mark_price !== undefined && rm.live_mark_price !== null
          ? rm.live_mark_price
          : null;
    // Explicit: never substitute candle close for live mark price.
    var liveMark = finiteBarNumber(markRaw);
    var metaKey = [
      source.captured_at || rm.captured_at || "",
      source.candle_captured_at || "",
      source.freshness_state || rm.freshness_state || "",
      String(liveMark === null ? "" : liveMark),
      body && body.repository_sha ? body.repository_sha : rm.repository_sha || "",
    ].join("|");
    return {
      schema_name: "market_landscape_ohlcv_browser_payload.v1",
      schema_version: 1,
      instrument_id:
        source.instrument_id || rm.instrument_id || rm.instrument || null,
      venue: source.venue || rm.venue || null,
      interval: source.interval || rm.interval || null,
      bar_count: bars.length,
      bars: bars,
      first_timestamp: bars[0].ts,
      last_timestamp: bars[bars.length - 1].ts,
      captured_at: source.captured_at || rm.captured_at || null,
      candle_captured_at:
        source.candle_captured_at || source.captured_at || rm.captured_at || null,
      freshness_state: source.freshness_state || rm.freshness_state || null,
      is_stale: Boolean(source.is_stale || rm.is_stale),
      live_mark_price: liveMark,
      candle_series_digest: clientDigest(seriesKey),
      metadata_digest: clientDigest(metaKey),
      chart_digest: clientDigest(seriesKey),
      canonical_source_kind: kind,
      non_authoritative_client_derivation: true,
    };
  }

  function extractCanonicalOhlcvPayload(body) {
    var picked = pickCanonicalOhlcvSource(body);
    if (!picked) return null;
    return buildClientPayloadFromCanonical(picked.source, body, picked.kind);
  }

  function bindCanonicalIdentityFromMarket(body) {
    if (!body || typeof body !== "object") return false;
    var rm = body.read_model || {};
    var sessionId = body.session_id || "";
    var repoSha = rm.repository_sha || body.repository_sha || "";
    var instrument = rm.instrument_id || rm.instrument || "";
    var venue = rm.venue || "";
    var connectionState = body.connection_state || rm.connection_state || "";
    root.setAttribute("data-session-id", String(sessionId || ""));
    root.setAttribute("data-repository-sha", String(repoSha || ""));
    var sessionNode = root.querySelector('[data-mdl-field="session_id"]');
    if (sessionNode) sessionNode.textContent = sessionId || "—";
    var shaNode = root.querySelector('[data-mdl-field="repository_sha"]');
    if (shaNode) shaNode.textContent = repoSha || "—";
    var instrumentNode = root.querySelector('[data-mdl-field="instrument"]');
    if (instrumentNode && instrument) instrumentNode.textContent = String(instrument);
    var selectedNode = root.querySelector('[data-mdl-field="selected_instrument"]');
    if (selectedNode && instrument) selectedNode.textContent = String(instrument);
    var venueNode = root.querySelector('[data-mdl-field="venue"]');
    if (venueNode && venue) venueNode.textContent = String(venue);
    if (connectionState) setConnectionState(String(connectionState));
    return true;
  }

  function resolvePresentationTickSize(payload) {
    var fromRoot = root.getAttribute("data-mdl-tick-size");
    if (fromRoot && String(fromRoot).trim()) return String(fromRoot).trim();
    if (payload && payload.tick_size != null && String(payload.tick_size).trim()) {
      return String(payload.tick_size).trim();
    }
    if (payload && payload.tickSz != null && String(payload.tickSz).trim()) {
      return String(payload.tickSz).trim();
    }
    return null;
  }

  function tickFractionDigits(tickSize) {
    if (tickSize === undefined || tickSize === null || tickSize === "") return null;
    var raw = String(tickSize).trim();
    if (!raw) return null;
    var n = Number(raw);
    if (!Number.isFinite(n) || n <= 0) return null;
    if (raw.indexOf("e") >= 0 || raw.indexOf("E") >= 0) {
      var expanded = expandScientificToPlain(raw);
      if (!expanded) return null;
      raw = expanded;
    }
    var dot = raw.indexOf(".");
    if (dot < 0) return 0;
    return raw.length - dot - 1;
  }

  function expandScientificToPlain(raw) {
    var s = String(raw).trim();
    var match = /^([+-]?)(\d+)(?:\.(\d+))?e([+-]?\d+)$/i.exec(s);
    if (!match) return null;
    var sign = match[1] === "-" ? "-" : "";
    var intPart = match[2];
    var fracPart = match[3] || "";
    var exp = parseInt(match[4], 10);
    if (!Number.isFinite(exp)) return null;
    var digits = intPart + fracPart;
    var exponent = exp - fracPart.length;
    if (exponent >= 0) {
      return sign + digits + new Array(exponent + 1).join("0");
    }
    var pointAt = digits.length + exponent;
    if (pointAt <= 0) {
      return sign + "0." + new Array(1 - pointAt).join("0") + digits;
    }
    return sign + digits.slice(0, pointAt) + "." + digits.slice(pointAt);
  }

  function decimalSafePlainFromInput(value) {
    if (value === undefined || value === null || value === "") return null;
    if (typeof value === "string") {
      var trimmed = value.trim();
      if (!trimmed) return null;
      if (/[eE]/.test(trimmed)) {
        return expandScientificToPlain(trimmed);
      }
      if (!Number.isFinite(Number(trimmed))) return null;
      return trimmed;
    }
    var n = Number(value);
    if (!Number.isFinite(n)) return null;
    var asString = String(n);
    if (/[eE]/.test(asString)) {
      return expandScientificToPlain(asString);
    }
    return asString;
  }

  function formatMarketPriceDisplay(value, tickSize) {
    // Presentation-only plain decimal; never toExponential. Prefer tick decimals.
    var plain = decimalSafePlainFromInput(value);
    if (plain === null) {
      if (value === undefined || value === null || value === "") return "—";
      return String(value);
    }
    var digits = tickFractionDigits(tickSize);
    if (digits !== null) {
      var num = Number(plain);
      if (!Number.isFinite(num)) return plain;
      // Display-only fixed digits from tick; avoid scientific via plain expansion.
      var fixed = num.toFixed(digits);
      if (/[eE]/.test(fixed)) {
        var expandedFixed = expandScientificToPlain(fixed);
        return expandedFixed || plain;
      }
      return fixed;
    }
    // Documented fallback when tick/precision metadata is absent.
    return plain;
  }

  function formatMarketVolumeDisplay(value) {
    var plain = decimalSafePlainFromInput(value);
    if (plain === null) {
      if (value === undefined || value === null || value === "") return "—";
      return String(value);
    }
    var num = Number(plain);
    if (Number.isFinite(num) && Number.isInteger(num)) return String(num);
    return plain;
  }

  function formatMarketChangePctDisplay(openV, closeV) {
    var o = Number(openV);
    var c = Number(closeV);
    if (!Number.isFinite(o) || !Number.isFinite(c) || o === 0) return "—";
    var pct = ((c - o) / o) * 100;
    if (!Number.isFinite(pct)) return "—";
    var plain = pct.toFixed(4);
    if (pct > 0) return "+" + plain + "%";
    return plain + "%";
  }

  function formatMetaNumber(value, tickSize) {
    return formatMarketPriceDisplay(value, tickSize);
  }

  /**
   * Authentic poll-to-poll close delta for the active candle only.
   * Same ts: delta = nextClose - prevClose.
   * New ts / missing prev: baseline reset → delta 0 (not inventing cross-candle motion).
   * Never fabricates closes; returns nulls when inputs are non-finite.
   */
  function resolveLastPricePollDelta(prevClose, prevTs, nextClose, nextTs) {
    var close = Number(nextClose);
    var ts = nextTs === undefined || nextTs === null ? "" : String(nextTs);
    if (!Number.isFinite(close) || !ts) {
      return { close: null, ts: "", delta: null, deltaPct: null, baselineReset: true };
    }
    var prevC = Number(prevClose);
    var prevT = prevTs === undefined || prevTs === null ? "" : String(prevTs);
    if (Number.isFinite(prevC) && prevT && prevT === ts) {
      var delta = close - prevC;
      var deltaPct = prevC !== 0 ? (delta / prevC) * 100 : null;
      return {
        close: close,
        ts: ts,
        delta: delta,
        deltaPct: deltaPct,
        baselineReset: false,
      };
    }
    return { close: close, ts: ts, delta: 0, deltaPct: 0, baselineReset: true };
  }

  function formatLastPriceMarkerLabel(close, delta, deltaPct) {
    // Retained for contract tests; in-chart text box is intentionally unused.
    if (!Number.isFinite(close)) return "";
    var parts = ["Close " + formatMetaNumber(close)];
    if (Number.isFinite(delta)) {
      var sign = delta > 0 ? "+" : "";
      parts.push("Change " + sign + formatMetaNumber(delta));
    }
    if (Number.isFinite(deltaPct)) {
      var pctSign = deltaPct > 0 ? "+" : "";
      parts.push("(" + pctSign + formatMetaNumber(deltaPct) + "%)");
    }
    return parts.join(" · ");
  }

  function ensureLastPriceMarkerEl() {
    var stage = root.querySelector("[data-mdl-chart-stage]");
    if (!stage) return null;
    var el = stage.querySelector("[data-mdl-last-price-marker]");
    if (el) return el;
    el = document.createElement("div");
    el.className = "mdl-v2-last-price-marker";
    el.setAttribute("data-mdl-last-price-marker", "true");
    el.setAttribute("data-mdl-last-price-visible", "false");
    el.setAttribute("aria-hidden", "true");
    el.setAttribute(
      "title",
      "Presentation observation of last candle close; not a trading signal."
    );
    el.innerHTML =
      '<div class="mdl-v2-last-price-marker__line" data-mdl-last-price-line="true"></div>';
    stage.appendChild(el);
    return el;
  }

  function clearLastPriceMarker(canvas) {
    lastPricePollClose = null;
    lastPricePollTs = null;
    var el = root.querySelector("[data-mdl-last-price-marker]");
    if (el) {
      el.setAttribute("data-mdl-last-price-visible", "false");
      el.removeAttribute("data-mdl-last-price-close");
      el.removeAttribute("data-mdl-last-price-delta");
      el.removeAttribute("data-mdl-last-price-delta-pct");
      el.removeAttribute("data-mdl-last-price-y");
      el.removeAttribute("data-mdl-last-price-ts");
      var label = el.querySelector("[data-mdl-last-price-label]");
      if (label) label.textContent = "";
    }
    if (canvas) {
      canvas.removeAttribute("data-mdl-last-price-close");
      canvas.removeAttribute("data-mdl-last-price-delta");
      canvas.removeAttribute("data-mdl-last-price-delta-pct");
      canvas.removeAttribute("data-mdl-last-price-y");
      canvas.removeAttribute("data-mdl-last-price-ts");
    }
  }

  function syncLastPriceMarker(canvas, bars, layout) {
    if (!canvas || !layout || !Array.isArray(bars) || !bars.length) {
      clearLastPriceMarker(canvas);
      return false;
    }
    var last = bars[bars.length - 1];
    var resolved = resolveLastPricePollDelta(
      lastPricePollClose,
      lastPricePollTs,
      last && last.close,
      last && last.ts
    );
    if (resolved.close === null) {
      clearLastPriceMarker(canvas);
      return false;
    }
    var yCss =
      layout.padT +
      (1 - (resolved.close - layout.minP) / layout.span) * layout.plotH;
    if (!Number.isFinite(yCss)) {
      clearLastPriceMarker(canvas);
      return false;
    }
    var el = ensureLastPriceMarkerEl();
    if (!el) return false;
    var stage = root.querySelector("[data-mdl-chart-stage]");
    if (!stage) return false;
    var canvasTop = canvas.offsetTop;
    var canvasLeft = canvas.offsetLeft;
    el.style.display = "block";
    el.style.top = canvasTop + yCss + "px";
    el.style.left = canvasLeft + layout.padL + "px";
    el.style.width = Math.max(1, layout.plotW) + "px";
    el.setAttribute("data-mdl-last-price-visible", "true");
    el.setAttribute("data-mdl-last-price-close", String(resolved.close));
    el.setAttribute("data-mdl-last-price-delta", String(resolved.delta));
    el.setAttribute(
      "data-mdl-last-price-delta-pct",
      resolved.deltaPct === null ? "" : String(resolved.deltaPct)
    );
    el.setAttribute("data-mdl-last-price-y", String(yCss));
    el.setAttribute("data-mdl-last-price-ts", resolved.ts);
    // No in-chart close/Δ text box — authentic values stay in the meta row.
    var label = el.querySelector("[data-mdl-last-price-label]");
    if (label) label.textContent = "";
    canvas.setAttribute("data-mdl-last-price-close", String(resolved.close));
    canvas.setAttribute("data-mdl-last-price-delta", String(resolved.delta));
    canvas.setAttribute(
      "data-mdl-last-price-delta-pct",
      resolved.deltaPct === null ? "" : String(resolved.deltaPct)
    );
    canvas.setAttribute("data-mdl-last-price-y", String(yCss));
    canvas.setAttribute("data-mdl-last-price-ts", resolved.ts);
    lastPricePollClose = resolved.close;
    lastPricePollTs = resolved.ts;
    return true;
  }

  function lastBarFromPayload(payload) {
    if (!payload || !Array.isArray(payload.bars) || !payload.bars.length) return null;
    return payload.bars[payload.bars.length - 1];
  }

  function updateMetaFromPayload(payload, availability, connectionState) {
    var intervalNode = root.querySelector('[data-mdl-field="ohlcv_interval"]');
    var latestNode = root.querySelector('[data-mdl-field="ohlcv_latest_candle_at"]');
    var capturedNode = root.querySelector('[data-mdl-field="ohlcv_captured_at"]');
    var markNode = root.querySelector('[data-mdl-field="ohlcv_live_mark"]');
    var revisionNode = root.querySelector('[data-mdl-field="ohlcv_revision"]');
    var openNode = root.querySelector('[data-mdl-field="ohlcv_open"]');
    var highNode = root.querySelector('[data-mdl-field="ohlcv_high"]');
    var lowNode = root.querySelector('[data-mdl-field="ohlcv_low"]');
    var closeNode = root.querySelector('[data-mdl-field="ohlcv_close"]');
    var changeNode = root.querySelector('[data-mdl-field="ohlcv_change"]');
    var volumeNode = root.querySelector('[data-mdl-field="ohlcv_volume"]');
    var availNode = root.querySelector("[data-mdl-chart-availability]");
    var last = lastBarFromPayload(payload);
    var tickSize = resolvePresentationTickSize(payload);
    if (intervalNode) {
      intervalNode.textContent = (payload && payload.interval) || "—";
    }
    if (latestNode) {
      latestNode.textContent = (payload && payload.last_timestamp) || "—";
    }
    if (capturedNode) {
      capturedNode.textContent =
        (payload && (payload.candle_captured_at || payload.captured_at)) || "—";
    }
    if (markNode) {
      // Absent optional mark → em dash. Never substitute candle close.
      if (
        payload &&
        payload.live_mark_price !== undefined &&
        payload.live_mark_price !== null
      ) {
        markNode.textContent = formatMarketPriceDisplay(payload.live_mark_price, tickSize);
      } else {
        markNode.textContent = "—";
      }
    }
    if (revisionNode) {
      revisionNode.textContent =
        (payload && payload.ohlcv_revision_kind) ||
        root.getAttribute("data-mdl-ohlcv-update-class") ||
        "—";
    }
    if (openNode) {
      openNode.textContent = last ? formatMarketPriceDisplay(last.open, tickSize) : "—";
    }
    if (highNode) {
      highNode.textContent = last ? formatMarketPriceDisplay(last.high, tickSize) : "—";
    }
    if (lowNode) {
      lowNode.textContent = last ? formatMarketPriceDisplay(last.low, tickSize) : "—";
    }
    if (closeNode) {
      closeNode.textContent = last ? formatMarketPriceDisplay(last.close, tickSize) : "—";
    }
    if (changeNode) {
      changeNode.textContent = last
        ? formatMarketChangePctDisplay(last.open, last.close)
        : "—";
    }
    if (volumeNode) {
      volumeNode.textContent = last ? formatMarketVolumeDisplay(last.volume) : "—";
    }
    if (availNode && availability) {
      availNode.textContent = availability;
      availNode.setAttribute("data-availability", availability);
    }
    if (connectionState) setConnectionState(connectionState);
  }

  function extractOhlcArrays(bars) {
    var opens = [];
    var highs = [];
    var lows = [];
    var closes = [];
    var i;
    for (i = 0; i < bars.length; i += 1) {
      var bar = bars[i];
      var o = Number(bar.open);
      var h = Number(bar.high);
      var l = Number(bar.low);
      var c = Number(bar.close);
      if (![o, h, l, c].every(function (v) { return Number.isFinite(v); })) {
        return null;
      }
      opens.push(o);
      highs.push(h);
      lows.push(l);
      closes.push(c);
    }
    return { opens: opens, highs: highs, lows: lows, closes: closes };
  }

  function resolveCssBox(canvas, stage) {
    // CSS owns layout size. Never write style.width/height from measured stage height
    // (that feedback loop caused cumulative vertical growth on each poll).
    var cssWidth = Math.max(
      1,
      Math.floor(
        (canvas.clientWidth > 0 && canvas.clientWidth) ||
          (stage && stage.clientWidth) ||
          640
      )
    );
    var cssHeight = Math.max(
      1,
      Math.floor(
        (canvas.clientHeight > 0 && canvas.clientHeight) ||
          (stage && stage.clientHeight) ||
          360
      )
    );
    return { cssWidth: cssWidth, cssHeight: cssHeight };
  }

  function syncBackingStore(canvas, cssWidth, cssHeight) {
    var dpr = window.devicePixelRatio || 1;
    var nextW = Math.floor(cssWidth * dpr);
    var nextH = Math.floor(cssHeight * dpr);
    var resized = canvas.width !== nextW || canvas.height !== nextH;
    if (resized) {
      canvas.width = nextW;
      canvas.height = nextH;
    }
    return { dpr: dpr, resized: resized };
  }

  function domainFor(highs, lows) {
    var minP = Math.min.apply(null, lows);
    var maxP = Math.max.apply(null, highs);
    if (!(Number.isFinite(minP) && Number.isFinite(maxP)) || maxP <= minP) {
      return null;
    }
    var span = maxP - minP;
    minP -= span * 0.04;
    maxP += span * 0.04;
    return { minP: minP, maxP: maxP, span: maxP - minP };
  }

  function paintFullSeries(canvas, payload, bars, arrays, forceResize) {
    var stage = canvas.parentElement;
    var box = resolveCssBox(canvas, stage);
    var cssWidth = box.cssWidth;
    var cssHeight = box.cssHeight;
    var store = syncBackingStore(canvas, cssWidth, cssHeight);
    var ctx = canvas.getContext("2d");
    if (!ctx) {
      markBlank(canvas, "no_2d_context");
      return false;
    }
    ctx.setTransform(store.dpr, 0, 0, store.dpr, 0, 0);
    ctx.clearRect(0, 0, cssWidth, cssHeight);
    root.setAttribute("data-mdl-full-series-clearrect", "true");

    var padL = 12;
    var padR = 12;
    var padT = 16;
    var padB = 28;
    var plotW = Math.max(1, cssWidth - padL - padR);
    var plotH = Math.max(1, cssHeight - padT - padB);
    var domain = domainFor(arrays.highs, arrays.lows);
    if (!domain) {
      markBlank(canvas, "degenerate_range");
      return false;
    }

    function yFor(price) {
      return padT + (1 - (price - domain.minP) / domain.span) * plotH;
    }

    var n = bars.length;
    var slot = plotW / n;
    var bodyW = Math.max(1, Math.min(8, slot * 0.62));
    var drawnPixels = 0;
    var i;

    ctx.lineWidth = 1;
    for (i = 0; i < n; i += 1) {
      var xCenter = padL + slot * (i + 0.5);
      var yO = yFor(arrays.opens[i]);
      var yH = yFor(arrays.highs[i]);
      var yL = yFor(arrays.lows[i]);
      var yC = yFor(arrays.closes[i]);
      var up = arrays.closes[i] >= arrays.opens[i];
      ctx.strokeStyle = up ? "#34d399" : "#f87171";
      ctx.fillStyle = up ? "#34d399" : "#f87171";
      ctx.beginPath();
      ctx.moveTo(xCenter, yH);
      ctx.lineTo(xCenter, yL);
      ctx.stroke();
      drawnPixels += Math.abs(yL - yH);
      var top = Math.min(yO, yC);
      var bodyH = Math.max(1, Math.abs(yC - yO));
      ctx.fillRect(xCenter - bodyW / 2, top, bodyW, bodyH);
      drawnPixels += bodyW * bodyH;
    }

    ctx.beginPath();
    ctx.strokeStyle = "#93c5fd";
    ctx.lineWidth = 1.25;
    for (i = 0; i < n; i += 1) {
      var x = padL + slot * (i + 0.5);
      var y = yFor(arrays.closes[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    drawnPixels += plotW;

    chartLayout = {
      cssWidth: cssWidth,
      cssHeight: cssHeight,
      padL: padL,
      padR: padR,
      padT: padT,
      padB: padB,
      plotW: plotW,
      plotH: plotH,
      minP: domain.minP,
      maxP: domain.maxP,
      span: domain.span,
      n: n,
      slot: slot,
      bodyW: bodyW,
      dpr: store.dpr,
      instanceId: chartInstanceId,
    };

    var geometryOk = drawnPixels > 0 && canvas.width > 0 && canvas.height > 0;
    finishCanvasAttrs(canvas, payload, bars, arrays.closes[n - 1], geometryOk, forceResize);
    if (geometryOk) {
      syncLastPriceMarker(canvas, bars, chartLayout);
    } else {
      clearLastPriceMarker(canvas);
    }
    return geometryOk;
  }

  function finishCanvasAttrs(canvas, payload, bars, renderedClose, geometryOk, fullClear) {
    var n = bars.length;
    canvas.setAttribute(
      "data-mdl-chart-geometry",
      geometryOk ? "nonzero" : "absent"
    );
    canvas.setAttribute("data-mdl-chart-blank", geometryOk ? "false" : "true");
    canvas.setAttribute("data-mdl-chart-bar-count", String(n));
    canvas.setAttribute("data-mdl-chart-first-ts", String(bars[0].ts || ""));
    canvas.setAttribute("data-mdl-chart-last-ts", String(bars[n - 1].ts || ""));
    canvas.setAttribute("data-mdl-chart-rendered-close", String(renderedClose));
    canvas.setAttribute(
      "data-mdl-chart-candle-close",
      String(bars[n - 1].close !== undefined ? bars[n - 1].close : "")
    );
    if (bars[n - 1].open !== undefined) {
      canvas.setAttribute("data-mdl-chart-candle-open", String(bars[n - 1].open));
    }
    if (bars[n - 1].high !== undefined) {
      canvas.setAttribute("data-mdl-chart-candle-high", String(bars[n - 1].high));
    }
    if (bars[n - 1].low !== undefined) {
      canvas.setAttribute("data-mdl-chart-candle-low", String(bars[n - 1].low));
    }
    if (bars[n - 1].volume !== undefined) {
      canvas.setAttribute("data-mdl-chart-candle-volume", String(bars[n - 1].volume));
    }
    canvas.setAttribute("data-mdl-chart-instance-id", chartInstanceId);
    canvas.setAttribute(
      "data-mdl-full-series-clearrect",
      fullClear ? "true" : "false"
    );
    if (payload.live_mark_price !== undefined && payload.live_mark_price !== null) {
      canvas.setAttribute(
        "data-mdl-chart-live-mark",
        String(payload.live_mark_price)
      );
    }
    if (payload.captured_at) {
      canvas.setAttribute("data-mdl-chart-captured-at", String(payload.captured_at));
    }
    var seriesDigest =
      payload.candle_series_digest || payload.chart_digest || "";
    if (seriesDigest) {
      canvas.setAttribute("data-mdl-chart-digest", String(seriesDigest));
      canvas.setAttribute("data-mdl-candle-series-digest", String(seriesDigest));
    }
    if (payload.metadata_digest) {
      canvas.setAttribute(
        "data-mdl-metadata-digest",
        String(payload.metadata_digest)
      );
    }
    if (payload.instrument_id) {
      canvas.setAttribute(
        "data-mdl-chart-instrument",
        String(payload.instrument_id)
      );
    }
    if (payload.venue) {
      canvas.setAttribute("data-mdl-chart-venue", String(payload.venue));
    }
    root.setAttribute(
      "data-mdl-chart-bound-without-geometry",
      geometryOk ? "false" : "true"
    );
    root.setAttribute("data-mdl-chart-rendered-close", String(renderedClose));
    root.setAttribute("data-mdl-chart-instance-id", chartInstanceId);
    root.setAttribute(
      "data-mdl-full-series-clearrect",
      fullClear ? "true" : "false"
    );
  }

  function paintLastCandleInPlace(canvas, payload, bars, arrays) {
    if (!chartLayout || chartLayout.n !== bars.length) {
      return paintFullSeries(canvas, payload, bars, arrays, true);
    }
    var last = bars.length - 1;
    var hi = arrays.highs[last];
    var lo = arrays.lows[last];
    if (hi > chartLayout.maxP || lo < chartLayout.minP) {
      setUpdateClass("SCALE_DOMAIN_ESCAPE");
      return paintFullSeries(canvas, payload, bars, arrays, true);
    }

    var ctx = canvas.getContext("2d");
    if (!ctx) {
      markBlank(canvas, "no_2d_context");
      return false;
    }
    var L = chartLayout;
    ctx.setTransform(L.dpr, 0, 0, L.dpr, 0, 0);

    function yFor(price) {
      return L.padT + (1 - (price - L.minP) / L.span) * L.plotH;
    }

    // Clear only the last candle slot (plus a small overlap), not the full series.
    var clearX = Math.max(0, L.padL + L.slot * (last - 0.15));
    var clearW = Math.min(L.cssWidth - clearX, L.slot * 1.3);
    ctx.clearRect(clearX, 0, clearW, L.cssHeight);
    root.setAttribute("data-mdl-full-series-clearrect", "false");

    var xCenter = L.padL + L.slot * (last + 0.5);
    var yO = yFor(arrays.opens[last]);
    var yH = yFor(arrays.highs[last]);
    var yL = yFor(arrays.lows[last]);
    var yC = yFor(arrays.closes[last]);
    var up = arrays.closes[last] >= arrays.opens[last];
    ctx.strokeStyle = up ? "#34d399" : "#f87171";
    ctx.fillStyle = up ? "#34d399" : "#f87171";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(xCenter, yH);
    ctx.lineTo(xCenter, yL);
    ctx.stroke();
    var top = Math.min(yO, yC);
    var bodyH = Math.max(1, Math.abs(yC - yO));
    ctx.fillRect(xCenter - L.bodyW / 2, top, L.bodyW, bodyH);

    // Redraw last polyline segment from previous close to new close.
    if (last > 0) {
      var xPrev = L.padL + L.slot * (last - 0.5);
      var yPrev = yFor(arrays.closes[last - 1]);
      ctx.beginPath();
      ctx.strokeStyle = "#93c5fd";
      ctx.lineWidth = 1.25;
      ctx.moveTo(xPrev, yPrev);
      ctx.lineTo(xCenter, yC);
      ctx.stroke();
    }

    finishCanvasAttrs(canvas, payload, bars, arrays.closes[last], true, false);
    syncLastPriceMarker(canvas, bars, L);
    return true;
  }

  function paintVolumeFullSeries(payload, bars, sharedLayout, fullClear) {
    var panel = root.querySelector("[data-mdl-volume-panel]");
    var canvas = root.querySelector("[data-mdl-volume-canvas]");
    if (!panel || !canvas || !sharedLayout) {
      markVolumeBlank("volume_panel_absent");
      return false;
    }
    var stateInfo = resolveVolumePanelState(payload, bars);
    setVolumePanelState(stateInfo.state, stateInfo.message);
    if (stateInfo.state === "MISSING_SOURCE" || stateInfo.state === "NOT_BOUND") {
      markVolumeBlank(stateInfo.state.toLowerCase());
      panel.setAttribute("data-mdl-volume-synced-with-chart", "false");
      return false;
    }

    var box = resolveCssBox(canvas, canvas.parentElement);
    var store = syncBackingStore(canvas, box.cssWidth, box.cssHeight);
    var ctx = canvas.getContext("2d");
    if (!ctx) {
      markVolumeBlank("no_2d_context");
      return false;
    }
    ctx.setTransform(store.dpr, 0, 0, store.dpr, 0, 0);
    ctx.clearRect(0, 0, box.cssWidth, box.cssHeight);

    var padL = sharedLayout.padL;
    var padR = sharedLayout.padR;
    var padT = 4;
    var padB = 4;
    var plotW = Math.max(1, box.cssWidth - padL - padR);
    var plotH = Math.max(1, box.cssHeight - padT - padB);
    var n = bars.length;
    var slot = plotW / n;
    var bodyW = sharedLayout.bodyW;
    var volumes = [];
    var directions = [];
    var maxV = 0;
    var i;
    for (i = 0; i < n; i += 1) {
      var vol = usableVolumeValue(bars[i].volume);
      volumes.push(vol);
      directions.push(
        classifyVolumeBarDirection(Number(bars[i].open), Number(bars[i].close))
      );
      if (vol !== null && vol > maxV) maxV = vol;
    }
    if (!(maxV > 0)) {
      // Authentic all-zero volume: sync geometry but draw no invented bars.
      maxV = 1;
    }

    for (i = 0; i < n; i += 1) {
      if (volumes[i] === null) continue;
      var xCenter = padL + slot * (i + 0.5);
      var barH = Math.max(volumes[i] > 0 ? 1 : 0, (volumes[i] / maxV) * plotH);
      var y = padT + plotH - barH;
      ctx.fillStyle = volumeDirectionColor(directions[i]);
      ctx.fillRect(xCenter - bodyW / 2, y, bodyW, Math.max(0, barH));
    }

    volumeLayout = {
      cssWidth: box.cssWidth,
      cssHeight: box.cssHeight,
      padL: padL,
      padR: padR,
      padT: padT,
      padB: padB,
      plotW: plotW,
      plotH: plotH,
      n: n,
      slot: slot,
      bodyW: bodyW,
      maxV: maxV,
      dpr: store.dpr,
      instanceId: sharedLayout.instanceId,
    };

    canvas.setAttribute("data-mdl-volume-geometry", "nonzero");
    canvas.setAttribute("data-mdl-volume-bar-count", String(n));
    canvas.setAttribute("data-mdl-volume-first-ts", String(bars[0].ts || ""));
    canvas.setAttribute("data-mdl-volume-last-ts", String(bars[n - 1].ts || ""));
    canvas.setAttribute("data-mdl-volume-slot", String(slot));
    canvas.setAttribute("data-mdl-volume-pad-l", String(padL));
    canvas.setAttribute("data-mdl-volume-pad-r", String(padR));
    canvas.setAttribute("data-mdl-volume-body-w", String(bodyW));
    canvas.setAttribute(
      "data-mdl-volume-full-series-clearrect",
      fullClear ? "true" : "false"
    );
    if (volumes[n - 1] !== null) {
      canvas.setAttribute("data-mdl-volume-last", String(volumes[n - 1]));
      canvas.setAttribute(
        "data-mdl-volume-last-direction",
        String(directions[n - 1])
      );
    } else {
      canvas.removeAttribute("data-mdl-volume-last");
      canvas.removeAttribute("data-mdl-volume-last-direction");
    }
    panel.setAttribute("data-mdl-volume-synced-with-chart", "true");
    panel.setAttribute("data-mdl-volume-bar-count", String(n));
    return true;
  }

  function paintLastVolumeBarInPlace(payload, bars, sharedLayout) {
    if (
      !volumeLayout ||
      !sharedLayout ||
      volumeLayout.n !== bars.length ||
      volumeLayout.n !== sharedLayout.n ||
      volumeLayout.slot !== sharedLayout.slot ||
      volumeLayout.padL !== sharedLayout.padL ||
      volumeLayout.bodyW !== sharedLayout.bodyW
    ) {
      return paintVolumeFullSeries(payload, bars, sharedLayout, true);
    }
    var canvas = root.querySelector("[data-mdl-volume-canvas]");
    if (!canvas) return false;
    var stateInfo = resolveVolumePanelState(payload, bars);
    setVolumePanelState(stateInfo.state, stateInfo.message);
    if (stateInfo.state === "MISSING_SOURCE" || stateInfo.state === "NOT_BOUND") {
      markVolumeBlank(stateInfo.state.toLowerCase());
      return false;
    }
    var last = bars.length - 1;
    var vol = usableVolumeValue(bars[last].volume);
    if (vol === null) {
      return paintVolumeFullSeries(payload, bars, sharedLayout, true);
    }
    if (vol > volumeLayout.maxV) {
      return paintVolumeFullSeries(payload, bars, sharedLayout, true);
    }
    var ctx = canvas.getContext("2d");
    if (!ctx) {
      markVolumeBlank("no_2d_context");
      return false;
    }
    var L = volumeLayout;
    ctx.setTransform(L.dpr, 0, 0, L.dpr, 0, 0);
    var clearX = Math.max(0, L.padL + L.slot * (last - 0.15));
    var clearW = Math.min(L.cssWidth - clearX, L.slot * 1.3);
    ctx.clearRect(clearX, 0, clearW, L.cssHeight);
    var xCenter = L.padL + L.slot * (last + 0.5);
    var barH = Math.max(vol > 0 ? 1 : 0, (vol / L.maxV) * L.plotH);
    var y = L.padT + L.plotH - barH;
    var direction = classifyVolumeBarDirection(
      Number(bars[last].open),
      Number(bars[last].close)
    );
    ctx.fillStyle = volumeDirectionColor(direction);
    ctx.fillRect(xCenter - L.bodyW / 2, y, L.bodyW, Math.max(0, barH));
    canvas.setAttribute("data-mdl-volume-last", String(vol));
    canvas.setAttribute("data-mdl-volume-last-direction", direction);
    canvas.setAttribute("data-mdl-volume-full-series-clearrect", "false");
    canvas.setAttribute("data-mdl-volume-bar-count", String(bars.length));
    canvas.setAttribute("data-mdl-volume-last-ts", String(bars[last].ts || ""));
    var panel = root.querySelector("[data-mdl-volume-panel]");
    if (panel) panel.setAttribute("data-mdl-volume-synced-with-chart", "true");
    return true;
  }

  function classifyUpdate(prevBars, nextBars, prevSeriesDigest, nextSeriesDigest, prevMark, nextMark, prevMeta, nextMeta) {
    if (!nextBars || !nextBars.length) return "NO_CHANGE";
    if (!prevBars || !prevBars.length) return "NEW_CANDLE_APPEND";
    if (prevSeriesDigest && nextSeriesDigest && prevSeriesDigest === nextSeriesDigest) {
      if (String(prevMark) !== String(nextMark) && nextMark !== undefined) {
        return "MARK_ONLY";
      }
      if (prevMeta !== nextMeta) return "METADATA_ONLY";
      return "NO_CHANGE";
    }
    if (prevBars.length === nextBars.length) {
      var last = nextBars.length - 1;
      var sameTs = String(prevBars[last].ts) === String(nextBars[last].ts);
      var histChanged = false;
      var i;
      for (i = 0; i < last; i += 1) {
        if (
          String(prevBars[i].ts) !== String(nextBars[i].ts) ||
          Number(prevBars[i].open) !== Number(nextBars[i].open) ||
          Number(prevBars[i].high) !== Number(nextBars[i].high) ||
          Number(prevBars[i].low) !== Number(nextBars[i].low) ||
          Number(prevBars[i].close) !== Number(nextBars[i].close) ||
          Number(prevBars[i].volume || 0) !== Number(nextBars[i].volume || 0)
        ) {
          histChanged = true;
          break;
        }
      }
      if (histChanged) return "HISTORICAL_SERIES_CHANGE";
      if (sameTs) return "SAME_TIMESTAMP_LAST_CANDLE_CHANGE";
      return "NEW_CANDLE_APPEND";
    }
    if (nextBars.length === prevBars.length + 1) return "NEW_CANDLE_APPEND";
    return "HISTORICAL_SERIES_CHANGE";
  }

  function renderOhlcvCanvas(optionalPayload, options) {
    options = options || {};
    var chart = root.querySelector("[data-mdl-chart]");
    var payloadNode = root.querySelector("[data-mdl-ohlcv-json]");
    var canvas = root.querySelector("[data-mdl-chart-canvas]");
    var message = root.querySelector("[data-mdl-chart-message]");
    if (!payloadNode || !canvas) {
      if (message && /chart bound/i.test(message.textContent || "")) {
        root.setAttribute("data-mdl-chart-bound-without-geometry", "true");
      }
      return;
    }

    var payload = optionalPayload;
    if (!payload) {
      try {
        payload = JSON.parse(payloadNode.textContent || "");
      } catch (err) {
        markBlank(canvas, "json_parse");
        return;
      }
    } else {
      payloadNode.textContent = JSON.stringify(payload);
    }

    updateMetaFromPayload(payload, chart && chart.getAttribute("data-availability"));

    var bars = payload && payload.bars;
    if (!Array.isArray(bars) || bars.length === 0) {
      markBlank(canvas, "empty_bars");
      return;
    }
    var arrays = extractOhlcArrays(bars);
    if (!arrays) {
      markBlank(canvas, "non_finite_ohlc");
      return;
    }

    var mode = options.mode || "FULL_SERIES";
    var ok;
    if (mode === "LAST_CANDLE_IN_PLACE") {
      ok = paintLastCandleInPlace(canvas, payload, bars, arrays);
      if (ok && chartLayout) {
        paintLastVolumeBarInPlace(payload, bars, chartLayout);
      }
    } else {
      ok = paintFullSeries(canvas, payload, bars, arrays, true);
      if (ok && chartLayout) {
        paintVolumeFullSeries(payload, bars, chartLayout, true);
      } else {
        markVolumeBlank(ok ? "missing_chart_layout" : "candle_paint_failed");
      }
    }
    if (ok) {
      lastBars = bars.map(function (b) {
        return {
          ts: b.ts,
          open: b.open,
          high: b.high,
          low: b.low,
          close: b.close,
          volume: b.volume,
          confirm: b.confirm,
        };
      });
      lastCandleSeriesDigest =
        payload.candle_series_digest || payload.chart_digest || "";
      lastMetadataDigest = payload.metadata_digest || "";
      lastMark =
        payload.live_mark_price !== undefined ? payload.live_mark_price : null;
    }
  }

  function applyPollPayload(body) {
    var chart = root.querySelector("[data-mdl-chart]");
    if (!chart) return;
    var availability = body.availability || "";
    if (availability) {
      chart.setAttribute("data-availability", availability);
    }
    // Fallback: payload → existing DOM → MISSING_SOURCE (never invent HEALTHY).
    var connectionState = resolveConnectionStateForPollPayload(body);
    // Fail-closed: never promote stale/disconnected/missing to HEALTHY.
    if (
      availability === "STALE" ||
      availability === "MISSING_SOURCE" ||
      connectionState === "STALE" ||
      connectionState === "DISCONNECTED" ||
      connectionState === "MISSING_SOURCE"
    ) {
      if (connectionState === "HEALTHY" || connectionState === "LIVE_DATA") {
        connectionState =
          availability === "MISSING_SOURCE" ? "MISSING_SOURCE" : "STALE";
      }
    }
    if (connectionState === "LIVE_DATA") connectionState = "HEALTHY";
    var payload = extractCanonicalOhlcvPayload(body);
    if (!payload || !payload.bars || !payload.bars.length) {
      updateMetaFromPayload(body, availability, connectionState);
      if (
        availability === "MISSING_SOURCE" ||
        connectionState === "MISSING_SOURCE" ||
        connectionState === "DISCONNECTED"
      ) {
        failVisible(connectionState || availability || "ohlcv_unavailable");
        setConnectionState(connectionState || "MISSING_SOURCE");
      } else {
        setConnectionState(connectionState);
        var volState =
          availability === "STALE" || connectionState === "STALE"
            ? "STALE"
            : availability === "NOT_BOUND"
              ? "NOT_BOUND"
              : "MISSING_SOURCE";
        setVolumePanelState(
          volState,
          volState === "STALE"
            ? "Volume STALE — canonical OHLCV freshness reports stale; no bars."
            : volState === "NOT_BOUND"
              ? "Volume NOT_BOUND — OHLCV present but not browser-serializable for volume."
              : "Volume MISSING_SOURCE — no OHLCV volume field in existing payload."
        );
        markVolumeBlank(volState.toLowerCase());
      }
      return;
    }
    clearFailVisible();

    var seriesDigest = payload.candle_series_digest || payload.chart_digest || "";
    var metaDigest = payload.metadata_digest || "";
    var mark = payload.live_mark_price;
    var kind = classifyUpdate(
      lastBars,
      payload.bars,
      lastCandleSeriesDigest,
      seriesDigest,
      lastMark,
      mark,
      lastMetadataDigest,
      metaDigest
    );
    setUpdateClass(kind);
    // Prefer client poll class for candle-motion events so sticky server NO_OP
    // cannot mask an authentic same-timestamp OHLCV change in the Revision field.
    if (
      kind === "SAME_TIMESTAMP_LAST_CANDLE_CHANGE" ||
      kind === "NEW_CANDLE_APPEND" ||
      kind === "HISTORICAL_SERIES_CHANGE"
    ) {
      payload.ohlcv_revision_kind = kind;
    } else {
      payload.ohlcv_revision_kind = payload.ohlcv_revision_kind || kind;
    }

    if (kind === "NO_CHANGE") {
      updateMetaFromPayload(payload, availability, connectionState);
      root.setAttribute("data-mdl-full-series-clearrect", "false");
      return;
    }
    if (kind === "METADATA_ONLY" || kind === "MARK_ONLY") {
      updateMetaFromPayload(payload, availability, connectionState);
      lastMetadataDigest = metaDigest;
      lastMark = mark;
      var canvas = root.querySelector("[data-mdl-chart-canvas]");
      if (canvas && mark !== undefined && mark !== null) {
        canvas.setAttribute("data-mdl-chart-live-mark", String(mark));
      }
      if (canvas && (payload.candle_captured_at || payload.captured_at)) {
        canvas.setAttribute(
          "data-mdl-chart-captured-at",
          String(payload.candle_captured_at || payload.captured_at)
        );
      }
      root.setAttribute("data-mdl-full-series-clearrect", "false");
      return;
    }
    if (kind === "SAME_TIMESTAMP_LAST_CANDLE_CHANGE") {
      updateMetaFromPayload(payload, availability, connectionState);
      renderOhlcvCanvas(payload, { mode: "LAST_CANDLE_IN_PLACE" });
      return;
    }
    // NEW_CANDLE_APPEND | HISTORICAL_SERIES_CHANGE | SCALE_DOMAIN_ESCAPE
    updateMetaFromPayload(payload, availability, connectionState);
    renderOhlcvCanvas(payload, { mode: "FULL_SERIES" });
  }

  function startOhlcvPolling() {
    var chart = root.querySelector("[data-mdl-chart]");
    if (!chart) return;
    var pollPath =
      chart.getAttribute("data-mdl-ohlcv-poll-path") ||
      root.getAttribute("data-canonical-ohlcv-path") ||
      "";
    var baseIntervalSeconds = Number(
      chart.getAttribute("data-mdl-ohlcv-poll-interval-seconds") || "0"
    );
    if (!pollPath || !(baseIntervalSeconds > 0)) return;
    // Only local canonical market API paths — never browser-direct OKX/network.
    if (pollPath.indexOf("/api/market/") !== 0) return;

    var inFlight = false;
    var timerId = null;
    var failStreak = 0;
    var backoffSeconds = 0;
    var MAX_BACKOFF_SECONDS = 15;
    var STALE_AFTER_FAILURES = 3;

    function nextDelaySeconds() {
      if (backoffSeconds > 0) return backoffSeconds;
      return baseIntervalSeconds;
    }

    function scheduleNext() {
      if (timerId !== null) window.clearTimeout(timerId);
      timerId = window.setTimeout(tick, nextDelaySeconds() * 1000);
    }

    function tick() {
      if (document.hidden) {
        scheduleNext();
        return;
      }
      if (inFlight) {
        scheduleNext();
        return;
      }
      inFlight = true;
      root.setAttribute("data-mdl-ohlcv-poll-in-flight", "true");
      if (failStreak > 0) setConnectionState("DEGRADED");
      fetch(pollPath, {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
      })
        .then(function (response) {
          if (!response.ok) throw new Error("poll_http_" + response.status);
          return response.json();
        })
        .then(function (body) {
          if (!body || typeof body !== "object") {
            throw new Error("poll_invalid_body");
          }
          if (body.direct_browser_okx) {
            throw new Error("poll_forbidden_direct_okx");
          }
          failStreak = 0;
          backoffSeconds = 0;
          applyPollPayload(body);
          root.setAttribute("data-mdl-ohlcv-poll-status", String(body.status || "OK"));
          root.setAttribute("data-mdl-ohlcv-poll-ok", "true");
          root.removeAttribute("data-mdl-ohlcv-poll-error");
        })
        .catch(function (err) {
          failStreak += 1;
          backoffSeconds = Math.min(
            MAX_BACKOFF_SECONDS,
            Math.max(1, Math.pow(2, Math.min(failStreak - 1, 3)))
          );
          root.setAttribute("data-mdl-ohlcv-poll-ok", "false");
          root.setAttribute(
            "data-mdl-ohlcv-poll-error",
            String((err && err.message) || "poll_failed")
          );
          root.setAttribute(
            "data-mdl-ohlcv-poll-backoff-seconds",
            String(backoffSeconds)
          );
          if (failStreak >= STALE_AFTER_FAILURES) {
            failVisible(String((err && err.message) || "poll_failed"));
            setConnectionState("DISCONNECTED");
          } else {
            setConnectionState("DEGRADED");
          }
        })
        .then(function () {
          inFlight = false;
          root.setAttribute("data-mdl-ohlcv-poll-in-flight", "false");
          scheduleNext();
        });
    }

    root.setAttribute("data-mdl-ohlcv-poll-armed", "true");
    // Preserve existing DOM connection truth; never invent HEALTHY from
    // data-availability, bootstrap success, or poll-timer arming alone.
    setConnectionState(readExistingConnectionState() || "MISSING_SOURCE");
    scheduleNext();
  }

  function isCanonicalHtmlShellHostDocument() {
    // Canonical Landscape shell serves HTML at GET /market. JSON-fetching that
    // document causes response.json() to fail and falsely paints
    // CANONICAL_DATA_UNAVAILABLE over working SSR/OHLCV presentation.
    var pathname =
      typeof window !== "undefined" && window.location
        ? String(window.location.pathname || "")
        : "";
    if (pathname === "/market") return true;
    // Non-supervised documents already carry SSR shell truth.
    return root.getAttribute("data-supervised-presentation-only") !== "true";
  }

  function bootstrapFromCanonicalMarket() {
    var marketPath = root.getAttribute("data-canonical-market-path") || "/market";
    if (marketPath !== "/market") {
      failVisible("forbidden_noncanonical_market_path");
      return Promise.resolve(false);
    }
    if (isCanonicalHtmlShellHostDocument()) {
      // Host contract: rely on SSR DOM + /api/market/landscape/ohlcv polling.
      // Do not presuppose a separate O2 JSON /market host.
      root.setAttribute("data-mdl-canonical-market-bound", "true");
      root.setAttribute("data-mdl-canonical-bootstrap-mode", "ssr_html_shell");
      return Promise.resolve(true);
    }
    // Optional supervised host only: JSON /market from a non-shell page.
    return fetch(marketPath, {
      method: "GET",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
      cache: "no-store",
    })
      .then(function (response) {
        if (!response.ok) throw new Error("market_http_" + response.status);
        var contentType = String(response.headers.get("content-type") || "");
        if (contentType.indexOf("application/json") === -1) {
          // Fail closed without JSON-parsing HTML; do not overwrite SSR truth.
          throw new Error("market_non_json_content_type");
        }
        return response.json();
      })
      .then(function (body) {
        if (!body || typeof body !== "object") {
          throw new Error("market_invalid_body");
        }
        if (body.direct_browser_okx) {
          throw new Error("market_forbidden_direct_okx");
        }
        if (body.trading_authority || body.orders) {
          throw new Error("market_forbidden_trading_authority");
        }
        bindCanonicalIdentityFromMarket(body);
        var rm = body.read_model || {};
        var bars =
          (rm.bars && rm.bars.length && rm.bars) ||
          (rm.ohlcv_projection && rm.ohlcv_projection.bars) ||
          null;
        if (bars && bars.length) {
          applyPollPayload({
            availability: body.connection_state || rm.connection_state || "",
            connection_state: body.connection_state || rm.connection_state || "",
            ohlcv: {
              bars: bars,
              bar_count: bars.length,
              interval: rm.interval,
              instrument_id: rm.instrument_id || rm.instrument,
              venue: rm.venue,
            },
            read_model: rm,
            repository_sha: rm.repository_sha,
            session_id: body.session_id,
            status: body.connection_state || "OK",
          });
        } else if (
          body.connection_state === "MISSING_SOURCE" ||
          rm.connection_state === "MISSING_SOURCE"
        ) {
          failVisible("MISSING_SOURCE");
        }
        root.setAttribute("data-mdl-canonical-market-bound", "true");
        root.setAttribute("data-mdl-canonical-bootstrap-mode", "optional_json_market");
        return true;
      })
      .catch(function (err) {
        failVisible(String((err && err.message) || "market_bootstrap_failed"));
        return false;
      });
  }

  function bootLandscapeClient() {
    renderOhlcvCanvas();
    bootstrapFromCanonicalMarket().then(function () {
      startOhlcvPolling();
    });
  }

  var resizeTimer = null;
  var resizeRaf1 = null;
  var resizeRaf2 = null;

  function paintAfterLayoutSettled() {
    // Double-rAF waits for CSS layout to settle after viewport/stage size changes
    // so backing-store width/height are derived from final CSS box × DPR once.
    if (resizeRaf1 !== null) window.cancelAnimationFrame(resizeRaf1);
    if (resizeRaf2 !== null) window.cancelAnimationFrame(resizeRaf2);
    resizeRaf1 = window.requestAnimationFrame(function () {
      resizeRaf1 = null;
      resizeRaf2 = window.requestAnimationFrame(function () {
        resizeRaf2 = null;
        if (!lastBars || !lastBars.length) {
          renderOhlcvCanvas();
          return;
        }
        setUpdateClass("VIEWPORT_RESIZE");
        renderOhlcvCanvas(null, { mode: "FULL_SERIES" });
      });
    });
  }

  function onViewportResize() {
    // True viewport/layout resize only — never from poll metadata updates.
    if (resizeTimer !== null) window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(function () {
      resizeTimer = null;
      paintAfterLayoutSettled();
    }, 50);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      bootLandscapeClient();
    });
  } else {
    bootLandscapeClient();
  }
  window.addEventListener("resize", onViewportResize);
  if (typeof ResizeObserver === "function") {
    var stageEl = root.querySelector("[data-mdl-chart-stage]");
    if (stageEl) {
      var lastObservedBox = { w: 0, h: 0 };
      var stageObserverReady = false;
      var ro = new ResizeObserver(function (entries) {
        var entry = entries && entries[0];
        if (!entry || !stageObserverReady) return;
        var box = entry.contentRect || {};
        var w = Math.floor(box.width || 0);
        var h = Math.floor(box.height || 0);
        if (w <= 0 || h <= 0) return;
        if (w === lastObservedBox.w && h === lastObservedBox.h) return;
        lastObservedBox = { w: w, h: h };
        if (!lastBars || !lastBars.length) return;
        onViewportResize();
      });
      // Seed after first paint so the initial RO callback does not re-render.
      window.requestAnimationFrame(function () {
        var r = stageEl.getBoundingClientRect();
        lastObservedBox = { w: Math.floor(r.width), h: Math.floor(r.height) };
        stageObserverReady = true;
        ro.observe(stageEl);
      });
    }
  }
})();
