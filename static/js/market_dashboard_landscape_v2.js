/**
 * Market Dashboard Landscape V2 — presentation-only client helpers.
 * No fetch mutation, no decision/risk/sizing logic, no write endpoints.
 * Renders materialized OHLCV from SSR/poll JSON only (never fabricates candles).
 * Polls local /api/market/landscape/ohlcv only; never calls OKX.
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
  var lastBars = null;
  var lastCandleSeriesDigest = "";
  var lastMetadataDigest = "";
  var lastMark = null;
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
  }

  function setConnectionState(state) {
    var node = root.querySelector(".mdl-v2-chart__chrome [data-mdl-data-connection-state]");
    if (node) {
      node.textContent = state;
      node.setAttribute("data-connection-state", state);
    }
    root.setAttribute("data-mdl-data-connection-state", state);
  }

  function setUpdateClass(kind) {
    root.setAttribute("data-mdl-ohlcv-update-class", kind);
  }

  function formatMetaNumber(value) {
    if (value === undefined || value === null || value === "") return "—";
    var n = Number(value);
    if (!Number.isFinite(n)) return String(value);
    if (Math.abs(n) > 0 && Math.abs(n) < 1e-4) return n.toExponential(3);
    return String(n);
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
    var volumeNode = root.querySelector('[data-mdl-field="ohlcv_volume"]');
    var availNode = root.querySelector("[data-mdl-chart-availability]");
    var last = lastBarFromPayload(payload);
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
      var mark =
        payload && payload.live_mark_price !== undefined && payload.live_mark_price !== null
          ? String(payload.live_mark_price)
          : "—";
      markNode.textContent = mark;
    }
    if (revisionNode) {
      revisionNode.textContent =
        (payload && payload.ohlcv_revision_kind) ||
        root.getAttribute("data-mdl-ohlcv-update-class") ||
        "—";
    }
    if (openNode) openNode.textContent = last ? formatMetaNumber(last.open) : "—";
    if (highNode) highNode.textContent = last ? formatMetaNumber(last.high) : "—";
    if (lowNode) lowNode.textContent = last ? formatMetaNumber(last.low) : "—";
    if (closeNode) closeNode.textContent = last ? formatMetaNumber(last.close) : "—";
    if (volumeNode) volumeNode.textContent = last ? formatMetaNumber(last.volume) : "—";
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
    } else {
      ok = paintFullSeries(canvas, payload, bars, arrays, true);
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
    var connectionState =
      body.data_connection_state ||
      (availability === "MISSING_SOURCE"
        ? "MISSING_SOURCE"
        : availability === "STALE"
          ? "STALE"
          : "LIVE_DATA");
    var payload = body.browser_payload;
    if (!payload || !payload.bars) {
      updateMetaFromPayload(body, availability, connectionState);
      if (availability === "MISSING_SOURCE") setConnectionState("MISSING_SOURCE");
      return;
    }

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
    // Expose poll classification as revision label (metadata-only ≠ candle motion).
    payload.ohlcv_revision_kind = payload.ohlcv_revision_kind || kind;

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
    var pollPath = chart.getAttribute("data-mdl-ohlcv-poll-path") || "";
    var baseIntervalSeconds = Number(
      chart.getAttribute("data-mdl-ohlcv-poll-interval-seconds") || "0"
    );
    if (!pollPath || !(baseIntervalSeconds > 0)) return;
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
      if (failStreak > 0) setConnectionState("RECONNECTING");
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
          setConnectionState(
            failStreak >= STALE_AFTER_FAILURES ? "STALE" : "RECONNECTING"
          );
        })
        .then(function () {
          inFlight = false;
          root.setAttribute("data-mdl-ohlcv-poll-in-flight", "false");
          scheduleNext();
        });
    }

    root.setAttribute("data-mdl-ohlcv-poll-armed", "true");
    setConnectionState(
      chart.getAttribute("data-availability") === "MISSING_SOURCE"
        ? "MISSING_SOURCE"
        : chart.getAttribute("data-availability") === "STALE"
          ? "STALE"
          : "LIVE_DATA"
    );
    scheduleNext();
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
      renderOhlcvCanvas();
      startOhlcvPolling();
    });
  } else {
    renderOhlcvCanvas();
    startOhlcvPolling();
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
