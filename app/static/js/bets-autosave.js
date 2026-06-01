/* bets-autosave.js - auto-save a player's bet without a visible save button.
 *
 * Wires the score inputs inside every ``.bet-form`` on /bets to submit the
 * form via HTMX when both fields are in a "ready to persist" state. The
 * underlying form still has ``hx-post`` / ``hx-target`` / ``hx-swap``
 * attributes, so submission goes through HTMX exactly like the old explicit
 * save button did; this file only decides *when* to trigger that submit.
 *
 * Trigger sources:
 *   1. ``change`` event on either score input (fires on blur when the value
 *      actually changed, on desktop and mobile alike).
 *   2. Enter key in either input (browsers don't auto-submit a multi-input
 *      form without a submit button, so we do it explicitly).
 *   3. ``visibilitychange`` to hidden and ``pagehide`` - safety net for the
 *      "user puts phone down mid-edit" case so a fully-typed bet doesn't
 *      get lost on tab switch / app switch / navigation.
 *
 * Save rule (kept identical to the previous button-driven flow so the
 * backend doesn't have to change):
 *   - both inputs non-empty             -> POST (upsert)
 *   - both inputs empty AND a prior bet existed at last render -> POST (delete)
 *   - anything else (partial input, or both empty with no prior bet) -> noop
 *
 * Dirty check: we compare the current ``input.value`` to ``input.defaultValue``
 * (which the browser sets to the server-rendered ``value`` attribute and
 * keeps fixed across user edits). After an HTMX swap the form is re-rendered
 * with the freshly persisted state, so defaultValue automatically becomes
 * the new baseline. No need to track state in JS.
 *
 * Event delegation on document means this works for the initial page render
 * AND for cells that HTMX swaps in after a save, without re-attaching
 * listeners. Activated by bets.html.
 */
(function () {
  "use strict";

  function inputsOf(form) {
    return {
      home: form.querySelector('input[name="score_home"]'),
      away: form.querySelector('input[name="score_away"]'),
    };
  }

  function isFilled(input) {
    return input && input.value.trim() !== "";
  }

  function hadPriorBet(home, away) {
    // defaultValue reflects the server-rendered value="..." attribute,
    // i.e. whether a bet existed at last render. If either side had a
    // value the user had a bet they may now be clearing.
    return (
      (home && home.defaultValue !== "") || (away && away.defaultValue !== "")
    );
  }

  function isDirty(home, away) {
    return (
      (home && home.value !== home.defaultValue) ||
      (away && away.value !== away.defaultValue)
    );
  }

  function shouldSave(form) {
    var io = inputsOf(form);
    if (!io.home || !io.away) return false;
    if (!isDirty(io.home, io.away)) return false;
    var bothFilled = isFilled(io.home) && isFilled(io.away);
    var bothEmpty = !isFilled(io.home) && !isFilled(io.away);
    if (bothFilled) return true;
    if (bothEmpty && hadPriorBet(io.home, io.away)) return true;
    return false;
  }

  function submitIfReady(form) {
    if (!form || !form.classList.contains("bet-form")) return;
    if (!shouldSave(form)) return;
    // requestSubmit fires the "submit" event that HTMX listens for; with
    // no submit button this still works and lets HTMX do the swap.
    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
    } else {
      form.submit();
    }
  }

  function handleChange(event) {
    var target = event.target;
    if (!target || target.tagName !== "INPUT") return;
    if (!target.classList.contains("bet-score")) return;
    var form = target.closest(".bet-form");
    submitIfReady(form);
  }

  function handleKeyDown(event) {
    if (event.key !== "Enter") return;
    var target = event.target;
    if (!target || !target.classList.contains("bet-score")) return;
    // Browsers don't implicitly submit two-input forms without a submit
    // button. Mirror the change-event behaviour so Enter still feels like
    // "save this bet".
    event.preventDefault();
    target.blur();
    submitIfReady(target.closest(".bet-form"));
  }

  function flushAll() {
    var forms = document.querySelectorAll(".bet-form");
    for (var i = 0; i < forms.length; i++) {
      submitIfReady(forms[i]);
    }
  }

  function handleVisibilityChange() {
    if (document.visibilityState === "hidden") flushAll();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.addEventListener("change", handleChange);
    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("pagehide", flushAll);
  });
})();
