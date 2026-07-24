/**
 * Market Dashboard Landscape V2 — presentation-only client helpers.
 * No fetch mutation, no decision/risk/sizing logic, no write endpoints.
 * Renders materialized OHLCV from SSR JSON only (never fabricates candles).
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

  function renderOhlcvCanvas() {
    var payloadNode = root.querySelector("[data-mdl-ohlcv-json]");
    var canvas = root.querySelector("[data-mdl-chart-canvas]");
    var message = root.querySelector("[data-mdl-chart-message]");
    if (!payloadNode || !canvas) {
      if (message && /chart bound/i.test(message.textContent || "")) {
        root.setAttribute("data-mdl-chart-bound-without-geometry", "true");
      }
      return;
    }

    var payload;
    try {
      payload = JSON.parse(payloadNode.textContent || "");
    } catch (err) {
      markBlank(canvas, "json_parse");
      return;
    }
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
      var h = Number(bar.high);
      var l = Number(bar.low);
      var c = Number(bar.close);
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

    // Close polyline overlay for continuous series geometry.
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
    canvas.setAttribute(
      "data-mdl-chart-geometry",
      geometryOk ? "nonzero" : "absent"
    );
    canvas.setAttribute("data-mdl-chart-blank", geometryOk ? "false" : "true");
    canvas.setAttribute("data-mdl-chart-bar-count", String(n));
    canvas.setAttribute("data-mdl-chart-first-ts", String(bars[0].ts || ""));
    canvas.setAttribute("data-mdl-chart-last-ts", String(bars[n - 1].ts || ""));
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderOhlcvCanvas);
  } else {
    renderOhlcvCanvas();
  }
  window.addEventListener("resize", renderOhlcvCanvas);
})();
