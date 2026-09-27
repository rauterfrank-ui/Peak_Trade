(function () {
  "use strict";

  const cfg = window.PEAK_TRADE_LANDSCAPE_V3 || {};
  const canvas = document.getElementById("v3-chart-canvas");
  const overlay = document.getElementById("v3-chart-overlay");
  const connectivity = document.getElementById("v3-connectivity");
  const freshnessEl = document.getElementById("v3-freshness");
  const markEl = document.getElementById("v3-mark");
  const blockersEl = document.getElementById("v3-blockers");
  const sectionsRoot = document.getElementById("v3-sections-root");
  const diagEl = document.getElementById("v3-diagnostics-json");

  /** @type {{ts_ms:number,o:number,h:number,l:number,c:number,finalized:boolean}[]} */
  let candles = [];
  let ws = null;
  let reconnectTimer = null;

  function wsUrl() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return proto + "//" + window.location.host + cfg.streamPath;
  }

  function setConnectivity(state) {
    connectivity.textContent = state || "DISCONNECTED";
    connectivity.className = "v3-badge v3-badge-" + (state || "disconnected").toLowerCase();
    if (state === "STALE" || state === "DISCONNECTED") {
      overlay.textContent = state;
      overlay.classList.remove("hidden");
    } else {
      overlay.classList.add("hidden");
    }
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
    const lows = slice.map((c) => c.l);
    const highs = slice.map((c) => c.h);
    let min = Math.min.apply(null, lows);
    let max = Math.max.apply(null, highs);
    if (min === max) {
      min -= 1;
      max += 1;
    }
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

  function applySnapshot(snap) {
    if (!snap) return;
    const primary = snap.primary || {};
    setConnectivity((snap.transport && snap.transport.state) || primary.connectivity);
    freshnessEl.textContent = "freshness: " + ((snap.transport && snap.transport.freshness_state) || primary.freshness || "—");
    markEl.textContent = "mark: " + (primary.mark_px || "—");
    blockersEl.textContent = (primary.blockers || []).join(" · ");
    if (snap.chart && Array.isArray(snap.chart.candles)) {
      candles = snap.chart.candles.slice();
      drawChart();
    }
    renderSections(snap.sections || {});
    diagEl.textContent = JSON.stringify(snap.diagnostics || {}, null, 2);
  }

  function renderSections(sections) {
    sectionsRoot.innerHTML = "";
    Object.keys(sections).forEach((key) => {
      const sec = sections[key];
      const div = document.createElement("div");
      div.className = "v3-section";
      const title = document.createElement("h3");
      title.textContent = sec.section_id || key;
      div.appendChild(title);
      const fields = sec.fields || {};
      Object.keys(fields).forEach((fname) => {
        const f = fields[fname] || {};
        const row = document.createElement("div");
        row.className = "v3-field";
        row.innerHTML = "<span>" + fname + "</span><span class=\"v3-field-state\">" + (f.availability || "—") + "</span>";
        div.appendChild(row);
      });
      sectionsRoot.appendChild(div);
    });
  }

  function handleMessage(msg) {
    if (msg.type === "snapshot") {
      applySnapshot(msg);
      return;
    }
    if (msg.type === "incremental") {
      if (msg.transport) setConnectivity(msg.transport.state);
      (msg.chart_events || []).forEach((ev) => {
        if (ev.candle) applyCandlePatch(ev.candle);
      });
      if (msg.primary) {
        markEl.textContent = "mark: " + (msg.primary.mark_px || "—");
      }
    }
  }

  function connectWs() {
    if (ws) {
      try { ws.close(); } catch (_) { /* ignore */ }
    }
    ws = new WebSocket(wsUrl());
    ws.onmessage = (ev) => {
      try {
        handleMessage(JSON.parse(ev.data));
      } catch (_) { /* ignore */ }
    };
    ws.onclose = () => {
      setConnectivity("DISCONNECTED");
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          connectWs();
        }, 2000);
      }
    };
  }

  fetch(cfg.snapshotPath)
    .then((r) => r.json())
    .then((snap) => {
      applySnapshot(snap);
      connectWs();
    })
    .catch(() => {
      setConnectivity("DISCONNECTED");
      connectWs();
    });
})();
