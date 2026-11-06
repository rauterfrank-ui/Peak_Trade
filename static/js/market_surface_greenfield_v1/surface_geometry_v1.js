(function () {
  "use strict";

  var scheduled = null;

  function syncChartMidpointToRanking() {
    var canvas = document.querySelector(".ots-ranking-canvas");
    var chartHost = document.getElementById("ots-chart");
    var viewportRow = document.querySelector(".ots-chart-viewport-row");
    if (!canvas || !chartHost || !viewportRow) return;

    viewportRow.style.transform = "";
    var canvasRect = canvas.getBoundingClientRect();
    var rankingMid = (canvasRect.top + canvasRect.bottom) / 2;
    var chartRect = chartHost.getBoundingClientRect();
    var chartMid = (chartRect.top + chartRect.bottom) / 2;
    var delta = rankingMid - chartMid;
    viewportRow.style.transform = "translateY(" + delta + "px)";
  }

  function schedule() {
    if (scheduled) cancelAnimationFrame(scheduled);
    scheduled = requestAnimationFrame(function () {
      scheduled = null;
      syncChartMidpointToRanking();
    });
  }

  window.PeakTradeSurfaceGeometryV1 = {
    sync: syncChartMidpointToRanking,
    schedule: schedule,
  };

  window.addEventListener("resize", schedule);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", schedule);
  } else {
    schedule();
  }
})();
