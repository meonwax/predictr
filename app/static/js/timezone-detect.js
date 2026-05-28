/* timezone-detect.js - push the browser's detected IANA timezone to the
 * server once per browser session so anonymous visitors (and signed-in
 * users who never opened /settings) see kickoff times in their local
 * zone.
 *
 * Posted to /timezone via fetch(); the server validates against the
 * curated SUPPORTED_TIMEZONES allow-list and silently rejects anything
 * it doesn't recognise.
 *
 * We only post when:
 *   - the browser exposes Intl.DateTimeFormat().resolvedOptions().timeZone,
 *   - the detected zone differs from the one already in the predictr_tz
 *     cookie (idempotency - no need to set the same cookie every page),
 *   - sessionStorage doesn't already hold a "posted-this-session" flag,
 *     so we don't pin the cookie inside a single tab session.
 *
 * Activated by base.html.
 */
(function () {
  "use strict";

  function getCookie(name) {
    var parts = ("; " + document.cookie).split("; " + name + "=");
    if (parts.length < 2) return null;
    return decodeURIComponent(parts.pop().split(";").shift());
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (typeof Intl === "undefined" || typeof Intl.DateTimeFormat !== "function") {
      return;
    }
    var detected;
    try {
      detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (_) {
      return;
    }
    if (!detected) return;

    var cookieTz = getCookie("predictr_tz");
    if (cookieTz === detected) return;

    var sessionKey = "predictr_tz_posted";
    try {
      if (sessionStorage.getItem(sessionKey) === detected) return;
      sessionStorage.setItem(sessionKey, detected);
    } catch (_) {
      /* sessionStorage unavailable (private mode, locked down site) -
       * proceed without the optimisation; the cookie check still avoids
       * redundant posts. */
    }

    var body = new FormData();
    body.append("timezone", detected);
    fetch("/timezone", {
      method: "POST",
      body: body,
      credentials: "same-origin",
      keepalive: true,
    }).catch(function () {
      /* network failures shouldn't break the page; the server-side
       * default (Europe/Berlin) is a perfectly fine fallback. */
    });
  });
})();
