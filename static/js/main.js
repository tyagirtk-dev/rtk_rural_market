(function () {
  "use strict";

  // ---- Dark / light mode ----
  var root = document.documentElement;
  var THEME_KEY = "rtk-theme"; // stored in cookie, not localStorage, per app conventions

  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? match[2] : null;
  }
  function setCookie(name, value, days) {
    var expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = name + "=" + value + "; expires=" + expires + "; path=/; SameSite=Lax";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    document.querySelectorAll("[data-theme-icon]").forEach(function (el) {
      el.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
    });
  }

  var savedTheme = getCookie(THEME_KEY) || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  applyTheme(savedTheme);

  document.addEventListener("click", function (e) {
    var toggle = e.target.closest("[data-theme-toggle]");
    if (!toggle) return;
    var current = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(current);
    setCookie(THEME_KEY, current, 365);
  });

  // ---- Notification badge polling (lightweight) ----
  var badge = document.querySelector("[data-notification-badge]");
  if (badge && badge.dataset.pollUrl) {
    function poll() {
      fetch(badge.dataset.pollUrl, { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data) return;
          if (data.count > 0) {
            badge.textContent = data.count > 99 ? "99+" : data.count;
            badge.classList.remove("d-none");
          } else {
            badge.classList.add("d-none");
          }
        })
        .catch(function () {});
    }
    poll();
    setInterval(poll, 30000);
  }

  // ---- Cookie consent banner ----
  var CONSENT_KEY = "rtk-cookie-consent";
  var banner = document.getElementById("rtk-cookie-banner");
  if (banner && !getCookie(CONSENT_KEY)) {
    banner.classList.remove("d-none");
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-cookie-accept]")) {
      setCookie(CONSENT_KEY, "accepted", 365);
      banner.classList.add("d-none");
    }
    if (e.target.closest("[data-cookie-reject]")) {
      setCookie(CONSENT_KEY, "rejected", 365);
      banner.classList.add("d-none");
    }
  });

  // ---- Quantity steppers (cart / product detail) ----
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-qty-step]");
    if (!btn) return;
    var input = document.querySelector(btn.getAttribute("data-target"));
    if (!input) return;
    var step = parseInt(btn.getAttribute("data-qty-step"), 10);
    var min = parseInt(input.min || "1", 10);
    var max = input.max ? parseInt(input.max, 10) : Infinity;
    var val = parseInt(input.value || "1", 10) + step;
    input.value = Math.max(min, Math.min(max, val));
  });

  // ---- PWA service worker ----
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/service-worker.js").catch(function () {});
    });
  }
})();
