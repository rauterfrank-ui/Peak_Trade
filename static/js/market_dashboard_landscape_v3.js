(function () {
  "use strict";
  const cfg = window.PEAK_TRADE_LANDSCAPE_V3 || {};
  const canvas = document.getElementById("v3-chart-canvas");
  const overlay = document.getElementById("v3-chart-overlay");
  const instrumentEl = document.getElementById("v3-instrument-id");
  const connectivity = document.getElementById("v3-connectivity");
  const freshnessEl = document.getElementById("v3-freshness");
  const markEl = document.getElementById("v3-mark");
  const systemStateEl = document.getElementById("v3-system-state");
  const blockersEl = document.getElementById("v3-blockers");
  const statusRail = document.getElementById("v3-status-rail");
  const bandsRoot = document.getElementById("v3-bands-root");
  const diagEl = document.getElementById("v3-diagnostics-json");
  const diagTransportEl = document.getElementById("v3-diagnostics-transport");
  const STATUS_RAIL_KEYS = [
    ["selection", "Selection"],
    ["decision", "Decision"],
    ["position", "Position"],
    ["account", "Account"],
    ["risk", "Risk"],
    ["quality", "Quality"],
  ];
  const ANALYTICAL_BANDS = [
    ["MARKET_INTELLIGENCE", "Market Intelligence"],
    ["REALIZED_BEHAVIOR", "Realized Behavior"],
    ["LEARNING", "Learning"],
    ["OPTIMIZATION", "Optimization"],
    ["META_LEARNING", "Meta-Learning"],
    ["MV2_DOUBLE_PLAY_ATTRIBUTION", "MV2 / Double Play Attribution"],
    ["CLOSED_CYCLE_HEALTH", "Closed-Cycle Health"],
  ];
  let candles = [];
  let ws = null;
  let reconnectTimer = null;
  function wsUrl() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return proto + "//" + window.location.host + cfg.streamPath;
  }
  function formatFieldDisplay(field) {
    if (!field || typeof field !== "object") return "UNKNOWN";
    const av = field.availability || "UNKNOWN";
    if (av === "AVAILABLE" && field.value != null) {
      if (typeof field.value === "object") {
        const compact = JSON.stringify(field.value);
        return av + " · " + (compact.length > 48 ? compact.slice(0, 45) + "…" : compact);
      }
      return av + " · " + String(field.value);
    }
    return av;
  }
  function availabilityClass(field) {
    return "v3-avail-" + (((field && field.availability) || "UNKNOWN").toLowerCase());
  }
  function setConnectivity(state) {
    const s = state || "DISCONNECTED";
    connectivity.textContent = s;
    connectivity.className = "v3-connectivity v3-state-" + s.toLowerCase().replace(/_/g, "-");
    if (s === "STALE" || s === "DISCONNECTED") {
      overlay.textContent = s;
      overlay.classList.remove("hidden");
    } else overlay.classList.add("hidden");
  }
  function drawChart() {
    if (!canvas || !canvas.getContext) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.fillStyle = "#161d26";
    ctx.fillRect(0, 0, w, h);
    if (!candles.length) {
      ctx.fillStyle = "#8b98a5";
      ctx.fillText("No candle data", 16, 24);
      return;
    }
    const slice = candles.slice(-120);
    let min = Math.min.apply(null, slice.map((c) => c.l));
    let max = Math.max.apply(null, slice.map((c) => c.h));
    if (min === max) { min -= 1; max += 1; }
    const pad = 24;
    const innerW = w - pad * 2;
    const innerH = h - pad * 2;
    const step = innerW / Math.max(slice.length - 1, 1);
    ctx.strokeStyle = "#3d9cf0";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    slice.forEach((c, i) => {
      const x = pad + i * step;
      const y = pad + innerH - ((c.c - min) / (max - min)) * innerH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    const last = slice[slice.length - 1];
    if (last && !last.finalized) {
      ctx.fillStyle = "#f5a623";
      const x = pad + (slice.length - 1) * step;
      const y = pad + innerH - ((last.c - min) / (max - min)) * innerH;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  function applyCandlePatch(candle) {
    if (!candle || candle.ts_ms == null) return;
    const idx = candles.findIndex((c) => c.ts_ms === candle.ts_ms);
    if (idx >= 0) candles[idx] = candle;
    else candles.push(candle);
    candles.sort((a, b) => a.ts_ms - b.ts_ms);
    drawChart();
  }
  function renderStatusRail(primary) {
    if (!statusRail) return;
    statusRail.innerHTML = "";
    STATUS_RAIL_KEYS.forEach(function (pair) {
      const field = (primary || {})[pair[0]];
      const cell = document.createElement("span");
      cell.className = "v3-rail-cell";
      const valueSpan = document.createElement("span");
      valueSpan.className = availabilityClass(field);
      valueSpan.textContent = formatFieldDisplay(field);
      cell.innerHTML = '<span class="v3-rail-label">' + pair[1] + "</span>";
      cell.appendChild(valueSpan);
      statusRail.appendChild(cell);
    });
  }
  function humanFieldLabel(name) {
    return name.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  }
  function renderAnalyticalBands(sections) {
    if (!bandsRoot) return;
    bandsRoot.innerHTML = "";
    ANALYTICAL_BANDS.forEach(function (pair) {
      const sec = (sections || {})[pair[0]];
      if (!sec) return;
      const band = document.createElement("section");
      band.className = "v3-band";
      const h = document.createElement("h2");
      h.className = "v3-band-title";
      h.textContent = pair[1];
      band.appendChild(h);
      const row = document.createElement("div");
      row.className = "v3-band-row";
      Object.keys(sec.fields || {}).forEach(function (fname) {
        const f = sec.fields[fname];
        const cell = document.createElement("span");
        cell.className = "v3-band-cell";
        const val = document.createElement("span");
        val.className = availabilityClass(f);
        val.textContent = formatFieldDisplay(f);
        cell.innerHTML = '<span class="v3-rail-label">' + humanFieldLabel(fname) + "</span> ";
        cell.appendChild(val);
        row.appendChild(cell);
      });
      band.appendChild(row);
      bandsRoot.appendChild(band);
    });
  }
  function applySnapshot(snap) {
    if (!snap) return;
    const primary = snap.primary || {};
    const transport = snap.transport || {};
    if (instrumentEl) {
      instrumentEl.textContent =
        (snap.instrument && snap.instrument.venue_native_id) || primary.instrument || "—";
    }
    setConnectivity(transport.state || primary.connectivity);
    if (freshnessEl) {
      freshnessEl.textContent = "Freshness " + (transport.freshness_state || primary.freshness || "—");
    }
    if (markEl) markEl.textContent = "Mark " + (primary.mark_px || "—");
    if (systemStateEl) {
      systemStateEl.textContent =
        "Transport " + (transport.state || "—") + " · seq " +
        (transport.sequence_cursor != null ? transport.sequence_cursor : "—");
    }
    if (blockersEl) blockersEl.textContent = (primary.blockers || []).join(" · ");
    if (snap.chart && Array.isArray(snap.chart.candles)) {
      candles = snap.chart.candles.slice();
      drawChart();
    }
    renderStatusRail(primary);
    renderAnalyticalBands(snap.sections || {});
    if (diagEl) diagEl.textContent = JSON.stringify(snap.diagnostics || {}, null, 2);
    if (diagTransportEl) {
      diagTransportEl.textContent = JSON.stringify({
        transport: snap.transport,
        field_counts: snap.field_counts,
        schema_version: snap.schema_version,
        presentation_schema: snap.presentation_schema,
      }, null, 2);
    }
  }
  function handleMessage(msg) {
    if (msg.type === "snapshot") { applySnapshot(msg); return; }
    if (msg.type === "incremental") {
      if (msg.transport) setConnectivity(msg.transport.state);
      (msg.chart_events || []).forEach((ev) => { if (ev.candle) applyCandlePatch(ev.candle); });
      if (msg.primary) {
        if (markEl) markEl.textContent = "Mark " + (msg.primary.mark_px || "—");
        renderStatusRail(msg.primary);
      }
    }
  }
  function connectWs() {
    if (ws) { try { ws.close(); } catch (_) {} }
    ws = new WebSocket(wsUrl());
    ws.onmessage = (ev) => { try { handleMessage(JSON.parse(ev.data)); } catch (_) {} };
    ws.onclose = () => {
      setConnectivity("DISCONNECTED");
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => { reconnectTimer = null; connectWs(); }, 2000);
      }
    };
  }
  fetch(cfg.snapshotPath).then((r) => r.json()).then((snap) => {
    applySnapshot(snap);
    connectWs();
  }).catch(() => { setConnectivity("DISCONNECTED"); connectWs(); });
})();
