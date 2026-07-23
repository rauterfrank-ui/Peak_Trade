/**
 * Market Dashboard Landscape V2 — presentation-only client helpers.
 * No fetch mutation, no decision/risk/sizing logic, no write endpoints.
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
    }
  });
})();
