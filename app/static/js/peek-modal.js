/* peek-modal.js - reset the shared "other players" modal body to its
 * spinner placeholder whenever the modal is hidden, so the next opening
 * doesn't briefly flash the previous fragment before HTMX overwrites it.
 *
 * Activated by base.html. Idempotent and silent if the modal isn't on
 * the page (e.g., on /login).
 */
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    var modal = document.getElementById("peek-modal");
    if (!modal) return;
    var body = document.getElementById("peek-modal-body");
    if (!body) return;
    var placeholder = body.innerHTML;
    modal.addEventListener("hidden.bs.modal", function () {
      body.innerHTML = placeholder;
    });
  });
})();
