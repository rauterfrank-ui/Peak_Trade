/**
 * Market Dashboard Landscape V2 — presentation-only client helpers.
 * No fetch mutation, no decision/risk/sizing logic, no write endpoints.
 * Renders materialized OHLCV from SSR/poll JSON only (never fabricates candles).
 * Polls the read-only /api/market/landscape/ohlcv snapshot endpoint; never calls OKX.
 * Chart redraw keys off chart_digest (market values), not captured_at alone.
 */
(function () {
  "use strict";
  var root = document.querySelector('[data-market-landscape-v2="true"]');
  if (!root) return;

  var engineering = root.querySelector("[data-mdl-engineering]");
  if (engineering) {
    engineering.addEventListener("toggle", function () {
      root.setAttribute(
        "data-mdl-engineering-open",
        engineering.open ? "true" : "false"
      );
    });
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
    var node = root.querySelector("[data-mdl-data-connection-state]");
    if (node) {
      node.textContent = state;
      node.setAttribute("data-connection-state", state);
    }
    root.setAttribute("data-mdl-data-connection-state", state);
  }

  function updateMetaFromPayload(payload, availability, connectionState) {
    var intervalNode = root.querySelector('[data-mdl-field="ohlcv_interval"]');
    var latestNode = root.querySelector('[data-mdl-field="ohlcv_latest_candle_at"]');
    var capturedNode = root.querySelector('[data-mdl-field="ohlcv_captured_at"]');
    var markNode = root.querySelector('[data-mdl-field="ohlcv_live_mark"]');
    var freshnessNode = root.querySelector('[data-mdl-field="ohlcv_freshness"]');
    var availNode = root.querySelector("[data-mdl-chart-availability]");
    if (intervalNode) {
      intervalNode.textContent = (payload && payload.interval) || "—";
    }
    if (latestNode) {
      latestNode.textContent = (payload && payload.last_timestamp) || "—";
    }
    if (capturedNode) {
      capturedNode.textContent = (payload && payload.captured_at) || "—";
    }
    if (markNode) {
      var mark =
        payload && payload.live_mark_price !== undefined && payload.live_mark_price !== null
          ? String(payload.live_mark_price)
          : "—";
      markNode.textContent = mark;
    }
    if (freshnessNode) {
      var fresh =
        (payload && payload.freshness_state && String(payload.freshness_state).toUpperCase()) ||
        availability ||
        "—";
      freshnessNode.textContent = fresh;
      if (availability) freshnessNode.setAttribute("data-availability", availability);
    }
    if (availNode && availability) {
      availNode.textContent = availability;
      availNode.setAttribute("data-availability", availability);
    }
    if (connectionState) setConnectionState(connectionState);
  }

  function renderOhlcvCanvas(optionalPayload) {
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

    var opens = [];
    var highs = [];
    var lows = [];
    var closes = [];
    var i;
    for (i = 0; i < bars.length; i += 1) {
      var bar = bars[i];
      var o = Number(bar.open);
      var h = Number(
        bar.display_high !== undefined && bar.display_high !== null
          ? bar.display_high
          : bar.high
      );
      var l = Number(
        bar.display_low !== undefined && bar.display_low !== null
          ? bar.display_low
          : bar.low
      );
      var c = Number(
        bar.display_close !== undefined && bar.display_close !== null
          ? bar.display_close
          : bar.close
      );
      if (![o, h, l, c].every(function (v) { return Number.isFinite(v); })) {
        markBlank(canvas, "non_finite_ohlc");
        return;
      }
      opens.push(o);
      highs.push(h);
      lows.push(l);
      closes.push(c);
    }

    var stage = canvas.parentElement;
    var cssWidth = Math.max(
      320,
      (stage && stage.clientWidth) || canvas.clientWidth || 640
    );
    var cssHeight = Math.max(
      220,
      (stage && stage.clientHeight) || 360
    );
    var dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(cssWidth * dpr);
    canvas.height = Math.floor(cssHeight * dpr);
    canvas.style.width = cssWidth + "px";
    canvas.style.height = cssHeight + "px";

    var ctx = canvas.getContext("2d");
    if (!ctx) {
      markBlank(canvas, "no_2d_context");
      return;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssWidth, cssHeight);

    var padL = 12;
    var padR = 12;
    var padT = 16;
    var padB = 28;
    var plotW = Math.max(1, cssWidth - padL - padR);
    var plotH = Math.max(1, cssHeight - padT - padB);
    var minP = Math.min.apply(null, lows);
    var maxP = Math.max.apply(null, highs);
    if (!(Number.isFinite(minP) && Number.isFinite(maxP)) || maxP <= minP) {
      markBlank(canvas, "degenerate_range");
      return;
    }
    var span = maxP - minP;
    minP -= span * 0.04;
    maxP += span * 0.04;
    span = maxP - minP;

    function yFor(price) {
      return padT + (1 - (price - minP) / span) * plotH;
    }

    var n = bars.length;
    var slot = plotW / n;
    var bodyW = Math.max(1, Math.min(8, slot * 0.62));
    var drawnPixels = 0;

    ctx.lineWidth = 1;
    for (i = 0; i < n; i += 1) {
      var xCenter = padL + slot * (i + 0.5);
      var yO = yFor(opens[i]);
      var yH = yFor(highs[i]);
      var yL = yFor(lows[i]);
      var yC = yFor(closes[i]);
      var up = closes[i] >= opens[i];
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

    // Close polyline overlay for continuous series geometry (uses display closes).
    ctx.beginPath();
    ctx.strokeStyle = "#93c5fd";
    ctx.lineWidth = 1.25;
    for (i = 0; i < n; i += 1) {
      var x = padL + slot * (i + 0.5);
      var y = yFor(closes[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    drawnPixels += plotW;

    var geometryOk = drawnPixels > 0 && canvas.width > 0 && canvas.height > 0;
    var lastBar = bars[n - 1];
    var renderedClose = closes[n - 1];
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
      String(lastBar && lastBar.close !== undefined ? lastBar.close : "")
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
    if (payload.chart_digest) {
      canvas.setAttribute("data-mdl-chart-digest", String(payload.chart_digest));
    } else if (payload.payload_digest) {
      canvas.setAttribute("data-mdl-chart-digest", String(payload.payload_digest));
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
    var lastChartDigest = "";
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
      if (failStreak > 0) {
        setConnectionState("RECONNECTING");
      }
      fetch(pollPath, {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("poll_http_" + response.status);
          }
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
          updateMetaFromPayload(
            body.browser_payload || body,
            availability,
            connectionState
          );
          var message = root.querySelector("[data-mdl-chart-message]");
          if (message && body.refresh && body.refresh.refresh_error) {
            message.setAttribute(
              "data-mdl-ohlcv-refresh-error",
              String(body.refresh.refresh_error)
            );
          } else if (message) {
            message.removeAttribute("data-mdl-ohlcv-refresh-error");
          }
          if (body.browser_payload && body.browser_payload.bars) {
            var digest =
              body.browser_payload.chart_digest ||
              body.browser_payload.payload_digest ||
              "";
            if (digest !== lastChartDigest) {
              lastChartDigest = digest;
              renderOhlcvCanvas(body.browser_payload);
            } else {
              updateMetaFromPayload(
                body.browser_payload,
                availability,
                connectionState
              );
            }
          } else if (
            availability === "MISSING_SOURCE" ||
            connectionState === "MISSING_SOURCE"
          ) {
            setConnectionState("MISSING_SOURCE");
          }
          root.setAttribute("data-mdl-ohlcv-poll-status", String(body.status || "OK"));
          root.setAttribute("data-mdl-ohlcv-poll-ok", "true");
          root.removeAttribute("data-mdl-ohlcv-poll-error");
        })
        .catch(function (err) {
          failStreak += 1;
          // Bounded exponential backoff: 1, 2, 4, … capped — no tight retry loop.
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
            setConnectionState("STALE");
          } else {
            setConnectionState("RECONNECTING");
          }
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      renderOhlcvCanvas();
      startOhlcvPolling();
    });
  } else {
    renderOhlcvCanvas();
    startOhlcvPolling();
  }
  window.addEventListener("resize", function () {
    renderOhlcvCanvas();
  });
})();
