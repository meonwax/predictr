"""UI translations for predictr.

The catalogue maps dotted message keys to translated strings. Two languages
are supported today, English (``en``) and German (``de``); German is the
primary audience and therefore the application's default language.

Why a hand-rolled dict instead of gettext / Babel?

* The translation surface is small (~ 250 keys).
* No build step (``msgfmt``, ``.po``->``.mo``) is needed.
* The catalogue ships in one file so adding a new language is a literal
  copy-and-translate exercise reviewable in a single diff.

Templates resolve translations through the ``_`` Jinja global (wired in
``app/templating.py``), which reads ``current_user`` from the rendering
context and falls back to the configured default language for anonymous
visitors.

Scope
-----

Only strings rendered into the user-visible UI live here. **Technical**
messages - HTTP 404/500 details, log lines, exception ``args`` for the
service layer - stay in English regardless of the active language. Those
surfaces are seen by operators and API clients, not end users, so
translating them buys nothing and just doubles the diff. Routes catch
service-layer exceptions and re-emit user-visible errors as catalogue
keys (e.g. ``"error.bet.deadline_passed"``) which the template translates.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Final

LOGGER = logging.getLogger(__name__)

#: Languages the UI is fully translated to. Keep ordered for stable test output.
SUPPORTED_LANGUAGES: Final[tuple[str, ...]] = ("de", "en")

#: Site default. German because the primary audience is German-speaking.
DEFAULT_LANGUAGE: Final[str] = "de"


# ---------------------------------------------------------------------------
# English catalogue - also serves as the canonical key listing.
# Keys are dotted, namespaced by feature area. Curly-brace placeholders use
# ``str.format`` style and must match across languages.
# ---------------------------------------------------------------------------

EN: dict[str, str] = {
    # --- Brand / chrome --------------------------------------------------
    "brand.name": "Predictr",
    "brand.tagline": "football prediction game",
    "brand.emblem.alt": "FIFA World Cup 2026 emblem",
    "footer.all_times_utc": "All times shown in UTC.",
    "footer.all_times_in": "All times shown in {tz}.",
    "language.switcher_aria": "Change language",
    "language.label_de": "DE",
    "language.label_en": "EN",
    "language.switch_to_de": "Auf Deutsch wechseln",
    "language.switch_to_en": "Switch to English",
    "nav.breadcrumb_aria": "Breadcrumb",
    "common.close": "Close",
    "common.save": "Save",
    "common.send": "Send",
    "common.delete": "Delete",
    "common.cancel": "Cancel",
    "common.loading": "Loading…",
    "common.saved": "saved",
    "common.optional": "optional",
    "common.utc": "UTC",
    "common.tbd": "TBD",
    "common.you": "you",
    "common.admin": "Admin",
    "common.leader": "Leader",
    "common.dash": "-",
    # --- Navbar ----------------------------------------------------------
    "nav.home": "Home",
    "nav.games": "Games",
    "nav.info": "Info",
    "nav.bets": "My bets",
    "nav.ladder": "Ladder",
    "nav.questions": "Questions",
    "nav.shouts": "Shoutbox",
    "nav.admin": "Admin",
    "nav.settings_title": "Account settings",
    "nav.sign_in": "Sign in",
    "nav.sign_out": "Sign out",
    "nav.create_account": "Create account",
    "nav.toggle": "Toggle navigation",
    "nav.main_aria": "Main navigation",
    # --- Peek modal ------------------------------------------------------
    "peek.title": "Other players",
    # --- Home dashboard -------------------------------------------------
    "home.title": "Home",
    "home.hero.welcome": "Welcome, {name}!",
    "home.hero.anonymous": "Welcome to {brand}.",
    "home.hero.subtitle_anon": (
        "The office prediction game for the FIFA World Cup 2026. "
        "Sign in to place your bets or create a new account in seconds."
    ),
    "home.hero.subtitle_user": ("Here is what's happening in the tournament right now."),
    "home.cta.sign_in": "Sign in",
    "home.cta.create_account": "Create an account",
    "home.cta.read_rules": "Read the rules",
    "home.cta.place_bets": "Place your bets",
    "home.cta.answer_questions": "Answer the special questions",
    "home.important.heading": "Important",
    "home.live.heading": "Live now",
    "home.live.empty": "No live matches right now.",
    "home.live.indicator": "live",
    "home.upcoming.heading": "Upcoming matches",
    "home.upcoming.empty": "No more matches scheduled.",
    "home.upcoming.see_all": "See full schedule",
    "home.questions.heading": "Open questions",
    "home.questions.empty": "No open questions right now.",
    "home.questions.deadline": "Deadline {when}",
    "home.questions.unanswered_badge": "Not answered yet",
    "home.questions.see_all": "Open the questions page",
    "home.shouts.heading": "Recent shouts",
    "home.shouts.empty": "No shouts yet.",
    "home.shouts.see_all": "Open the shoutbox",
    "home.reminder.unanswered": ("You have open questions waiting for an answer."),
    "home.reminder.unbet": ("You have upcoming matches you haven't bet on yet."),
    # --- Games page -----------------------------------------------------
    "games.title": "Tournament schedule",
    "games.summary": "{matches} matches across {groups} groups",
    "games.col.kickoff": "Kickoff",
    "games.col.home": "Home",
    "games.col.score": "Score",
    "games.col.away": "Away",
    "games.col.venue": "Venue",
    "games.col.result": "Result",
    "games.placeholder.vs": "vs",
    "games.matches_count_one": "{count} match",
    "games.matches_count_many": "{count} matches",
    "games.empty_group": "No matches in this group yet.",
    "games.empty_tournament_html": (
        "No tournament data is loaded. Run "
        "<code>python -m app.seed seeds/wc2026.sql</code> to populate the database."
    ),
    # --- Bets page ------------------------------------------------------
    "bets.title": "My bets",
    "bets.subtitle": (
        "Predict the final score for each match. You can edit a bet any "
        "time before kickoff. Points are awarded once results are published."
    ),
    "bets.legend.result": "exact result",
    "bets.legend.spread": "correct goal difference",
    "bets.legend.tendency": "correct winner only",
    "bets.col.your_bet": "Your bet",
    "bets.col.points": "Pts",
    "bets.col.others": "Other players",
    "bets.col.others_title": "Other players' bets",
    "bets.no_bet_title": "No bet placed",
    "bets.awaiting_result": "Waiting for result",
    "bets.aria.home_score": "Home score for game {id}",
    "bets.aria.away_score": "Away score for game {id}",
    "bets.aria.peek_others": "See other players' bets for match {id}",
    # --- Questions (user-facing) ----------------------------------------
    "questions.title": "Special questions",
    "questions.subtitle": (
        "Free-text predictions outside the match schedule. Each has its own "
        "deadline and is worth its own number of points; the correct answer "
        "is revealed once the deadline passes."
    ),
    "questions.col.question": "Question",
    "questions.col.deadline": "Deadline",
    "questions.col.your_answer": "Your answer",
    "questions.col.correct_answer": "Correct answer",
    "questions.col.worth": "Worth",
    "questions.col.points_short": "Pts",
    "questions.col.others": "Other players",
    "questions.col.others_title": "Other players' answers",
    "questions.awaiting_correct": "Deadline passed; awaiting correct answer",
    "questions.awaiting_correct_short": "Waiting for the correct answer",
    "questions.no_answer_title": "No answer submitted before the deadline",
    "questions.empty": "No special questions have been published yet.",
    "questions.aria.answer": "Answer for question {id}",
    "questions.aria.save_answer": "Save answer for question {id}",
    "questions.aria.peek_others": "See other players' answers for question {id}",
    # --- Other players' bets / answers (modal bodies) -------------------
    "others.bets.locked": ("Other players' bets are revealed after kickoff ({kickoff})."),
    "others.bets.empty": "Nobody else placed a bet on this match.",
    "others.answers.locked": ("Other players' answers are revealed after the deadline."),
    "others.answers.empty": "Nobody else answered this question.",
    "others.match_label": "Match #{id}",
    "others.result_label": "Result {home} : {away}",
    "others.awaiting_result": "Awaiting result",
    "others.deadline_label": "Deadline {when}",
    "others.correct_label": "Correct",
    "others.col.player": "Player",
    "others.col.bet": "Bet",
    "others.col.answer": "Answer",
    "others.col.points": "Pts",
    # --- Ladder ---------------------------------------------------------
    "ladder.title": "Ladder",
    "ladder.subtitle": ("Live standings - updated as soon as match results are recorded."),
    "ladder.col.player": "Player",
    "ladder.col.points": "Points",
    "ladder.abbr.exact": "Exact result | {pts} pts",
    "ladder.abbr.spread": "Correct goal difference | {pts} pts",
    "ladder.abbr.tendency": "Correct winner only | {pts} pts",
    "ladder.abbr.miss": "Missed (0 pts)",
    "ladder.abbr.placed": "Bets placed",
    "ladder.breakdown.bets": "bets",
    "ladder.breakdown.questions": "q",
    "ladder.pending_title": "Awaiting results",
    "ladder.upcoming_title": "Upcoming",
    "ladder.empty_html": (
        'No players yet. Be the first to <a href="/register">create an account</a>.'
    ),
    # --- Shoutbox -------------------------------------------------------
    "shouts.title": "Shoutbox",
    "shouts.subtitle": "Banter, hot takes, and post-match grudges. Be excellent to each other.",
    "shouts.placeholder": "Say something to your fellow predictors…",
    "shouts.aria.message": "Shout message",
    "shouts.empty": "No shouts yet - be the first to say hello.",
    "shouts.admin_badge": "admin",
    # --- Info page chrome (rules Markdown is sourced from config) -------
    "info.title": "About this game",
    "info.subtitle": "Rules, scoring, and how to play.",
    "info.legend.result": "exact result",
    "info.legend.spread": "correct goal difference",
    "info.legend.tendency": "correct winner only",
    "info.cta.create_account": "Create account",
    "info.cta.sign_in": "Sign in",
    "info.cta.hint": "Sign up to start placing bets.",
    # --- Error pages (401 / 403 / 404 / 500) ---------------------------
    "error.401.title": "Please sign in",
    "error.401.message": "You need to sign in to view this page.",
    "error.403.title": "Forbidden",
    "error.403.message": (
        "You don't have permission to view this page. If you think this is a mistake, ask an admin."
    ),
    "error.404.title": "Page not found",
    "error.404.message": (
        "We couldn't find what you were looking for. The page may have moved or never existed."
    ),
    "error.500.title": "Something went wrong",
    "error.500.message": (
        "An unexpected error has been logged. Please try again in a moment; "
        "if it keeps happening, let an admin know."
    ),
    "error.cta.home": "Go to the home page",
    "error.cta.sign_in": "Sign in",
    "error.cta.back": "Go back",
    # --- Auth: Login ----------------------------------------------------
    "auth.login.page_title": "Sign in",
    "auth.login.heading": "Sign in",
    "auth.login.registered_alert": "Your account is ready. Sign in below.",
    "auth.login.email": "Email",
    "auth.login.password": "Password",
    "auth.login.remember_me": "Remember me",
    "auth.login.submit": "Sign in",
    "auth.login.forgot": "Forgot your password?",
    "auth.login.create_account": "Create an account",
    # --- Auth: Register -------------------------------------------------
    "auth.register.page_title": "Create your account",
    "auth.register.heading": "Create your account",
    "auth.register.name": "Display name",
    "auth.register.email": "Email",
    "auth.register.password": "Password",
    "auth.register.password_hint": "At least {min} characters.",
    "auth.register.submit": "Create account",
    "auth.register.have_account": "Already have an account?",
    # --- Auth: Lost password -------------------------------------------
    "auth.lostpwd.page_title": "Reset your password",
    "auth.lostpwd.heading": "Reset your password",
    "auth.lostpwd.sent": (
        "If an account exists for that email, we've just sent it a link to "
        "reset the password. The link is valid for 24 hours."
    ),
    "auth.lostpwd.intro": (
        "Enter the email address you registered with. We'll send you a link "
        "to choose a new password."
    ),
    "auth.lostpwd.email": "Email",
    "auth.lostpwd.submit": "Send reset link",
    "auth.lostpwd.back": "Back to sign in",
    # --- Outbound email: password reset --------------------------------
    # Body is plain text. Placeholders: name, url, ttl_hours, brand.
    "mail.reset.subject": "{brand}: password reset",
    "mail.reset.body": (
        "Hi {name},\n"
        "\n"
        "A password reset was requested for your account on {brand}.\n"
        "Follow the link below to choose a new password:\n"
        "\n"
        "  {url}\n"
        "\n"
        "The link expires in {ttl_hours} hours.\n"
        "If you didn't request this, you can safely ignore this email.\n"
        "\n"
        "-- {brand}\n"
    ),
    # --- Auth: Reset password ------------------------------------------
    "auth.reset.page_title": "Reset your password",
    "auth.reset.heading": "Choose a new password",
    "auth.reset.request_new": "Request a new reset link",
    "auth.reset.password": "New password",
    "auth.reset.password_hint": "At least {min} characters.",
    "auth.reset.confirm": "Confirm new password",
    "auth.reset.submit": "Set new password",
    # --- Auth: errors --------------------------------------------------
    "error.auth.invalid_credentials": "Invalid email or password.",
    "error.auth.name_too_short": "Please choose a name with at least 2 characters.",
    "error.auth.password_too_short": "Please choose a password with at least {min} characters.",
    "error.auth.invalid_email": "That doesn't look like a valid email address.",
    "error.auth.email_taken": "That email is already registered.",
    "error.auth.password_mismatch": "The two passwords don't match.",
    "error.auth.reset_invalid_unknown": (
        "This reset link is no longer valid. It may have been used already or never existed."
    ),
    "error.auth.reset_invalid_expired": ("This reset link has expired. Please request a new one."),
    # --- Settings page -------------------------------------------------
    "settings.page_title": "Settings",
    "settings.heading": "Account settings",
    "settings.saved.profile": "Profile updated.",
    "settings.saved.password": "Password changed.",
    "settings.saved.avatar": "Avatar updated.",
    "settings.saved.avatar_deleted": "Avatar removed.",
    "settings.section.profile": "Profile",
    "settings.section.avatar": "Avatar",
    "settings.section.password": "Password",
    "settings.profile.error": (
        "Please pick a display name with at least 2 characters and a supported language."
    ),
    "settings.profile.name": "Display name",
    "settings.profile.language": "Preferred language",
    "settings.profile.lang.en": "English",
    "settings.profile.lang.de": "Deutsch",
    "settings.profile.timezone": "Timezone",
    "settings.profile.timezone_hint": (
        "Used for displaying kickoff times and other dates. Stored timestamps "
        "stay in UTC; this only affects what you see. The site default is {default}."
    ),
    "settings.profile.signed_in_html": (
        "Signed in as <code>{email}</code>. Account created {created}."
    ),
    "settings.profile.submit": "Save profile",
    "settings.avatar.current": "Your current avatar.",
    "settings.avatar.none": "No avatar set - a generic icon is shown for now.",
    "settings.avatar.upload_label": "Upload a new avatar",
    "settings.avatar.upload_hint": "PNG or JPEG, <= 200 KiB. Resized to 128x128.",
    "settings.avatar.upload_submit": "Upload",
    "settings.avatar.remove": "Remove current avatar",
    "settings.avatar.error.empty": "Please choose a file to upload.",
    "settings.avatar.error.too_large": "Image is too large. Maximum size is 200 KiB.",
    "settings.avatar.error.bad_type": "Only PNG and JPEG images are accepted.",
    "settings.avatar.error.corrupt": "That file doesn't look like a valid image.",
    "settings.password.current": "Current password",
    "settings.password.new": "New password",
    "settings.password.new_hint": "At least {min} characters.",
    "settings.password.confirm": "Confirm new password",
    "settings.password.submit": "Change password",
    "settings.password.error.mismatch": "The two new-password fields don't match.",
    "settings.password.error.too_short": "New password must be at least {min} characters.",
    "settings.password.error.wrong_current": "Your current password is incorrect.",
    # --- Admin dashboard ------------------------------------------------
    "admin.crumb.root": "Admin",
    "admin.crumb.games": "Match results",
    "admin.crumb.questions": "Special questions",
    "admin.dash.title": "Admin dashboard",
    "admin.dash.subtitle": (
        "Quick view of what needs attention. More controls live under each section."
    ),
    "admin.dash.users": "Users",
    "admin.dash.users_summary_one": "{admin} admin, {bets} bet placed",
    "admin.dash.users_summary_few": "{admin} admin, {bets} bets placed",
    "admin.dash.users_summary_many": "{admin} admins, {bets} bets placed",
    "admin.dash.matches": "Matches",
    "admin.dash.matches_upcoming": "{count} still upcoming",
    "admin.dash.pending": "Pending results",
    "admin.dash.pending_more": "matches kicked off without a result >",
    "admin.dash.pending_done": "all caught up - enter results >",
    "admin.dash.manage": "Manage",
    "admin.dash.manage_results": "Enter / edit match results",
    "admin.dash.manage_questions": "Special questions",
    # --- Admin games ---------------------------------------------------
    "admin.games.title": "Match results",
    "admin.games.subtitle": (
        "Enter the final score for each match. Leave both fields blank to "
        'clear a result. Optional notes (e.g. "AET", "5-3 pen") show '
        "below the score on the games page."
    ),
    "admin.games.col.notes": "Notes",
    "admin.games.col.save": "Save",
    "admin.games.notes.placeholder": "AET, pen",
    "admin.games.aria.home_score": "Home score for game {id}",
    "admin.games.aria.away_score": "Away score for game {id}",
    "admin.games.aria.home_team": "Home team for game {id}",
    "admin.games.aria.away_team": "Away team for game {id}",
    "admin.games.aria.notes": "Notes for game {id}",
    "admin.games.aria.save": "Save row for game {id}",
    "admin.games.save_row": "Save score, notes, and teams",
    # --- Admin questions -----------------------------------------------
    "admin.questions.title": "Special questions",
    "admin.questions.subtitle_html": (
        "Free-text predictions outside the match schedule. Each row has its "
        "own deadline (UTC) and point value. Once the deadline passes, set "
        "the correct answer to score it; comma-separate alternative "
        "spellings (e.g. <code>Mbappe,Mbappé,Kylian Mbappe</code>) - case is "
        "ignored and contains-match is used."
    ),
    "admin.questions.saved_html": "Saved - {what}.",
    "admin.questions.saved.created": "created",
    "admin.questions.saved.updated": "updated",
    "admin.questions.saved.deleted": "deleted",
    "admin.questions.new": "New question",
    "admin.questions.field.question": "Question",
    "admin.questions.field.deadline": "Deadline (UTC)",
    "admin.questions.field.points": "Pts",
    "admin.questions.field.correct_optional": "Correct answer (optional now)",
    "admin.questions.field.correct": "Correct answer",
    "admin.questions.placeholder.correct": "comma-separated variants",
    "admin.questions.submit_new": "Create question",
    "admin.questions.col.deadline": "Deadline",
    "admin.questions.col.points": "Pts",
    "admin.questions.col.answers_count_title": "Number of users who have answered",
    "admin.questions.empty": "No questions yet. Use the form above to create the first one.",
    "admin.questions.confirm_delete": "Delete this question and all answers given so far?",
    "admin.questions.aria.question": "Question text for question {id}",
    "admin.questions.aria.deadline": "Deadline for question {id}",
    "admin.questions.aria.points": "Points for question {id}",
    "admin.questions.aria.correct": "Correct answer for question {id}",
    "admin.questions.aria.save": "Save question {id}",
    "admin.questions.aria.delete": "Delete question {id}",
    # --- User-facing validation errors (surfaced into templates as the
    # `error` context variable). Technical HTTP 404/500 messages and
    # service-layer exception text remain English.
    "error.bet.deadline_passed": "Kickoff has already passed.",
    "error.question.deadline_passed": "Deadline has already passed.",
    "error.score.not_int": "{field} must be a whole number.",
    "error.score.range": "{field} must be between {min} and {max}.",
    "error.score.home": "Home score",
    "error.score.away": "Away score",
    "error.score.invalid": "Please enter whole numbers for both scores.",
    "error.score.partial": "Please fill in both scores, or clear both to remove the bet.",
    "error.question.text_too_short": "Question text must be at least {min} characters.",
    "error.question.text_too_long": "Question text must be at most {max} characters.",
    "error.question.points_not_int": "Points must be a whole number.",
    "error.question.points_required": "Points is required.",
    "error.question.points_range": "Points must be between {min} and {max}.",
    "error.question.correct_too_long": "Correct answer must be at most {max} characters.",
    "error.question.answer_empty": "Answer must not be empty.",
    "error.question.answer_too_long": "Answer must be at most {max} characters.",
    "error.question.deadline_required": "Deadline is required.",
    "error.question.deadline_invalid": ("Invalid deadline. Please use the date/time picker."),
    "error.shout.empty": "Message must not be empty.",
    "error.shout.too_long": "Message must be at most {max} characters.",
    "error.admin.notes_too_long": "Notes must be at most {max} characters.",
    "error.team.unknown": "Unknown team.",
    "error.team.same": "Home and away teams must differ.",
    "error.team.not_knockout": "Teams for group-stage games cannot be edited.",
    # --- Date helpers (day/month names, used by the `kickoff` filter) --
    "date.day.0": "Mon",
    "date.day.1": "Tue",
    "date.day.2": "Wed",
    "date.day.3": "Thu",
    "date.day.4": "Fri",
    "date.day.5": "Sat",
    "date.day.6": "Sun",
    "date.month.1": "Jan",
    "date.month.2": "Feb",
    "date.month.3": "Mar",
    "date.month.4": "Apr",
    "date.month.5": "May",
    "date.month.6": "Jun",
    "date.month.7": "Jul",
    "date.month.8": "Aug",
    "date.month.9": "Sep",
    "date.month.10": "Oct",
    "date.month.11": "Nov",
    "date.month.12": "Dec",
}


# ---------------------------------------------------------------------------
# German catalogue. Same keys, German wording.
# ---------------------------------------------------------------------------

DE: dict[str, str] = {
    # --- Brand / chrome --------------------------------------------------
    "brand.name": "Predictr",
    "brand.tagline": "Tippspiel für die Fußball-WM",
    "brand.emblem.alt": "FIFA Fußball-Weltmeisterschaft 2026 - Emblem",
    "footer.all_times_utc": "Alle Zeiten in UTC.",
    "footer.all_times_in": "Alle Zeiten in {tz}.",
    "language.switcher_aria": "Sprache wechseln",
    "language.label_de": "DE",
    "language.label_en": "EN",
    "language.switch_to_de": "Auf Deutsch wechseln",
    "language.switch_to_en": "Switch to English",
    "nav.breadcrumb_aria": "Navigationspfad",
    "common.close": "Schließen",
    "common.save": "Speichern",
    "common.send": "Senden",
    "common.delete": "Löschen",
    "common.cancel": "Abbrechen",
    "common.loading": "Wird geladen …",
    "common.saved": "gespeichert",
    "common.optional": "optional",
    "common.utc": "UTC",
    "common.tbd": "noch offen",
    "common.you": "du",
    "common.admin": "Admin",
    "common.leader": "Tabellenführer",
    "common.dash": "-",
    # --- Navbar ----------------------------------------------------------
    "nav.home": "Startseite",
    "nav.games": "Spiele",
    "nav.info": "Info",
    "nav.bets": "Meine Tipps",
    "nav.ladder": "Rangliste",
    "nav.questions": "Fragen",
    "nav.shouts": "Shoutbox",
    "nav.admin": "Admin",
    "nav.settings_title": "Konto-Einstellungen",
    "nav.sign_in": "Anmelden",
    "nav.sign_out": "Abmelden",
    "nav.create_account": "Registrieren",
    "nav.toggle": "Navigation umschalten",
    "nav.main_aria": "Hauptnavigation",
    # --- Peek modal ------------------------------------------------------
    "peek.title": "Andere Spieler",
    # --- Home dashboard -------------------------------------------------
    "home.title": "Startseite",
    "home.hero.welcome": "Willkommen, {name}!",
    "home.hero.anonymous": "Willkommen bei {brand}.",
    "home.hero.subtitle_anon": (
        "Das Tippspiel zur FIFA Fussball-Weltmeisterschaft 2026. "
        "Melde dich an, um Tipps abzugeben, oder lege in wenigen Sekunden "
        "ein neues Konto an."
    ),
    "home.hero.subtitle_user": ("Hier siehst du, was gerade im Turnier los ist."),
    "home.cta.sign_in": "Anmelden",
    "home.cta.create_account": "Konto anlegen",
    "home.cta.read_rules": "Spielregeln lesen",
    "home.cta.place_bets": "Tipps abgeben",
    "home.cta.answer_questions": "Sonderfragen beantworten",
    "home.important.heading": "Wichtig",
    "home.live.heading": "Aktuell live",
    "home.live.empty": "Aktuell keine laufenden Spiele.",
    "home.live.indicator": "live",
    "home.upcoming.heading": "Kommende Spiele",
    "home.upcoming.empty": "Keine weiteren Spiele angesetzt.",
    "home.upcoming.see_all": "Kompletten Spielplan ansehen",
    "home.questions.heading": "Offene Fragen",
    "home.questions.empty": "Aktuell keine offenen Fragen.",
    "home.questions.deadline": "Deadline {when}",
    "home.questions.unanswered_badge": "Noch nicht beantwortet",
    "home.questions.see_all": "Zur Fragenseite",
    "home.shouts.heading": "Letzte Shouts",
    "home.shouts.empty": "Noch keine Shouts.",
    "home.shouts.see_all": "Zum Shoutbox",
    "home.reminder.unanswered": ("Du hast noch offene Sonderfragen, die auf eine Antwort warten."),
    "home.reminder.unbet": ("Du hast anstehende Spiele, auf die du noch nicht getippt hast."),
    # --- Games page -----------------------------------------------------
    "games.title": "Spielplan",
    "games.summary": "{matches} Spiele in {groups} Gruppen",
    "games.col.kickoff": "Anstoß",
    "games.col.home": "Heim",
    "games.col.score": "Ergebnis",
    "games.col.away": "Auswärts",
    "games.col.venue": "Spielort",
    "games.col.result": "Ergebnis",
    "games.placeholder.vs": "gegen",
    "games.matches_count_one": "{count} Spiel",
    "games.matches_count_many": "{count} Spiele",
    "games.empty_group": "Noch keine Spiele in dieser Gruppe.",
    "games.empty_tournament_html": (
        "Es sind keine Turnierdaten geladen. Mit "
        "<code>python -m app.seed seeds/wc2026.sql</code> die Datenbank befüllen."
    ),
    # --- Bets page ------------------------------------------------------
    "bets.title": "Meine Tipps",
    "bets.subtitle": (
        "Tippe das Endergebnis jedes Spiels. Bis zum Anpfiff kannst du "
        "den Tipp jederzeit ändern. Punkte gibt es, sobald das Ergebnis "
        "eingetragen ist."
    ),
    "bets.legend.result": "exaktes Ergebnis",
    "bets.legend.spread": "richtige Tordifferenz",
    "bets.legend.tendency": "nur richtiger Sieger",
    "bets.col.your_bet": "Dein Tipp",
    "bets.col.points": "Pkt.",
    "bets.col.others": "Andere Spieler",
    "bets.col.others_title": "Tipps der anderen Spieler",
    "bets.no_bet_title": "Kein Tipp abgegeben",
    "bets.awaiting_result": "Ergebnis ausstehend",
    "bets.aria.home_score": "Heimtor für Spiel {id}",
    "bets.aria.away_score": "Auswärtstor für Spiel {id}",
    "bets.aria.peek_others": "Tipps der anderen für Spiel {id} ansehen",
    # --- Questions (user-facing) ----------------------------------------
    "questions.title": "Sonderfragen",
    "questions.subtitle": (
        "Tipps abseits des Spielplans. Jede Frage hat ihren eigenen Stichtag "
        "und eine eigene Punktzahl; die richtige Antwort wird nach Ablauf "
        "des Stichtags eingetragen."
    ),
    "questions.col.question": "Frage",
    "questions.col.deadline": "Stichtag",
    "questions.col.your_answer": "Deine Antwort",
    "questions.col.correct_answer": "Richtige Antwort",
    "questions.col.worth": "Wert",
    "questions.col.points_short": "Pkt.",
    "questions.col.others": "Andere Spieler",
    "questions.col.others_title": "Antworten der anderen Spieler",
    "questions.awaiting_correct": "Stichtag vorbei; richtige Antwort folgt",
    "questions.awaiting_correct_short": "Warte auf die richtige Antwort",
    "questions.no_answer_title": "Bis zum Stichtag keine Antwort abgegeben",
    "questions.empty": "Es wurden noch keine Sonderfragen veröffentlicht.",
    "questions.aria.answer": "Antwort zur Frage {id}",
    "questions.aria.save_answer": "Antwort zur Frage {id} speichern",
    "questions.aria.peek_others": "Antworten der anderen zur Frage {id} ansehen",
    # --- Other players' bets / answers (modal bodies) -------------------
    "others.bets.locked": (
        "Tipps der anderen Spieler werden nach dem Anpfiff sichtbar ({kickoff})."
    ),
    "others.bets.empty": "Niemand sonst hat auf dieses Spiel getippt.",
    "others.answers.locked": ("Antworten der anderen Spieler werden nach dem Stichtag sichtbar."),
    "others.answers.empty": "Niemand sonst hat diese Frage beantwortet.",
    "others.match_label": "Spiel Nr. {id}",
    "others.result_label": "Ergebnis {home} : {away}",
    "others.awaiting_result": "Ergebnis ausstehend",
    "others.deadline_label": "Stichtag {when}",
    "others.correct_label": "Richtig",
    "others.col.player": "Spieler",
    "others.col.bet": "Tipp",
    "others.col.answer": "Antwort",
    "others.col.points": "Pkt.",
    # --- Ladder ---------------------------------------------------------
    "ladder.title": "Rangliste",
    "ladder.subtitle": ("Aktueller Stand - wird mit jedem eingetragenen Ergebnis aktualisiert."),
    "ladder.col.player": "Spieler",
    "ladder.col.points": "Punkte",
    "ladder.abbr.exact": "Exaktes Ergebnis | {pts} Pkt.",
    "ladder.abbr.spread": "Richtige Tordifferenz | {pts} Pkt.",
    "ladder.abbr.tendency": "Nur richtiger Sieger | {pts} Pkt.",
    "ladder.abbr.miss": "Daneben (0 Pkt.)",
    "ladder.abbr.placed": "Abgegebene Tipps",
    "ladder.breakdown.bets": "Tipps",
    "ladder.breakdown.questions": "F",
    "ladder.pending_title": "Ergebnisse ausstehend",
    "ladder.upcoming_title": "Anstehend",
    "ladder.empty_html": (
        'Noch keine Spieler. Werde der erste - <a href="/register">jetzt ein Konto anlegen</a>.'
    ),
    # --- Shoutbox -------------------------------------------------------
    "shouts.title": "Shoutbox",
    "shouts.subtitle": "Sprüche, heiße Wetten und Nachspielzeit. Bleibt fair zueinander.",
    "shouts.placeholder": "Sag etwas zu deinen Mitspielern …",
    "shouts.aria.message": "Shout-Nachricht",
    "shouts.empty": "Noch keine Shouts - sag du als erstes Hallo.",
    "shouts.admin_badge": "Admin",
    # --- Info page chrome -----------------------------------------------
    "info.title": "Über dieses Spiel",
    "info.subtitle": "Regeln, Punktevergabe und Spielablauf.",
    "info.legend.result": "exaktes Ergebnis",
    "info.legend.spread": "richtige Tordifferenz",
    "info.legend.tendency": "nur richtiger Sieger",
    "info.cta.create_account": "Registrieren",
    "info.cta.sign_in": "Anmelden",
    "info.cta.hint": "Registriere dich, um Tipps abzugeben.",
    # --- Error pages (401 / 403 / 404 / 500) ---------------------------
    "error.401.title": "Bitte anmelden",
    "error.401.message": "Diese Seite ist nur für angemeldete Nutzer sichtbar.",
    "error.403.title": "Nicht erlaubt",
    "error.403.message": (
        "Du hast keine Berechtigung für diese Seite. "
        "Falls das ein Fehler ist, melde dich beim Admin."
    ),
    "error.404.title": "Seite nicht gefunden",
    "error.404.message": (
        "Was du suchst, ist nicht hier. Vielleicht wurde es verschoben oder es gab es nie."
    ),
    "error.500.title": "Da ist etwas schiefgelaufen",
    "error.500.message": (
        "Ein unerwarteter Fehler wurde protokolliert. Versuche es gleich "
        "noch einmal; bleibt es so, gib dem Admin Bescheid."
    ),
    "error.cta.home": "Zur Startseite",
    "error.cta.sign_in": "Anmelden",
    "error.cta.back": "Zurück",
    # --- Auth: Login ----------------------------------------------------
    "auth.login.page_title": "Anmelden",
    "auth.login.heading": "Anmelden",
    "auth.login.registered_alert": "Dein Konto ist eingerichtet. Melde dich unten an.",
    "auth.login.email": "E-Mail",
    "auth.login.password": "Passwort",
    "auth.login.remember_me": "Angemeldet bleiben",
    "auth.login.submit": "Anmelden",
    "auth.login.forgot": "Passwort vergessen?",
    "auth.login.create_account": "Konto anlegen",
    # --- Auth: Register -------------------------------------------------
    "auth.register.page_title": "Konto anlegen",
    "auth.register.heading": "Konto anlegen",
    "auth.register.name": "Anzeigename",
    "auth.register.email": "E-Mail",
    "auth.register.password": "Passwort",
    "auth.register.password_hint": "Mindestens {min} Zeichen.",
    "auth.register.submit": "Konto anlegen",
    "auth.register.have_account": "Schon ein Konto?",
    # --- Auth: Lost password -------------------------------------------
    "auth.lostpwd.page_title": "Passwort zurücksetzen",
    "auth.lostpwd.heading": "Passwort zurücksetzen",
    "auth.lostpwd.sent": (
        "Falls für diese E-Mail ein Konto existiert, haben wir gerade einen "
        "Link zum Zurücksetzen des Passworts verschickt. Der Link ist 24 "
        "Stunden gültig."
    ),
    "auth.lostpwd.intro": (
        "Trage die E-Mail-Adresse ein, mit der du dich registriert hast. Wir "
        "schicken dir einen Link, um ein neues Passwort zu wählen."
    ),
    "auth.lostpwd.email": "E-Mail",
    "auth.lostpwd.submit": "Link senden",
    "auth.lostpwd.back": "Zurück zur Anmeldung",
    # --- Outbound email: password reset --------------------------------
    "mail.reset.subject": "{brand}: Passwort zurücksetzen",
    "mail.reset.body": (
        "Hallo {name},\n"
        "\n"
        "für dein Konto bei {brand} wurde ein Zurücksetzen des Passworts "
        "angefordert.\n"
        "Folge dem folgenden Link, um ein neues Passwort zu wählen:\n"
        "\n"
        "  {url}\n"
        "\n"
        "Der Link ist {ttl_hours} Stunden gültig.\n"
        "Solltest du das nicht angefordert haben, kannst du diese E-Mail "
        "einfach ignorieren.\n"
        "\n"
        "-- {brand}\n"
    ),
    # --- Auth: Reset password ------------------------------------------
    "auth.reset.page_title": "Passwort zurücksetzen",
    "auth.reset.heading": "Neues Passwort wählen",
    "auth.reset.request_new": "Neuen Reset-Link anfordern",
    "auth.reset.password": "Neues Passwort",
    "auth.reset.password_hint": "Mindestens {min} Zeichen.",
    "auth.reset.confirm": "Neues Passwort bestätigen",
    "auth.reset.submit": "Neues Passwort setzen",
    # --- Auth: errors --------------------------------------------------
    "error.auth.invalid_credentials": "E-Mail oder Passwort sind falsch.",
    "error.auth.name_too_short": "Bitte wähle einen Namen mit mindestens 2 Zeichen.",
    "error.auth.password_too_short": "Bitte wähle ein Passwort mit mindestens {min} Zeichen.",
    "error.auth.invalid_email": "Das sieht nicht nach einer gültigen E-Mail-Adresse aus.",
    "error.auth.email_taken": "Diese E-Mail ist bereits registriert.",
    "error.auth.password_mismatch": "Die beiden Passwörter stimmen nicht überein.",
    "error.auth.reset_invalid_unknown": (
        "Dieser Reset-Link ist nicht mehr gültig. "
        "Möglicherweise wurde er bereits verwendet oder existierte nie."
    ),
    "error.auth.reset_invalid_expired": (
        "Dieser Reset-Link ist abgelaufen. Bitte fordere einen neuen an."
    ),
    # --- Settings page -------------------------------------------------
    "settings.page_title": "Einstellungen",
    "settings.heading": "Konto-Einstellungen",
    "settings.saved.profile": "Profil aktualisiert.",
    "settings.saved.password": "Passwort geändert.",
    "settings.saved.avatar": "Avatar aktualisiert.",
    "settings.saved.avatar_deleted": "Avatar entfernt.",
    "settings.section.profile": "Profil",
    "settings.section.avatar": "Avatar",
    "settings.section.password": "Passwort",
    "settings.profile.error": (
        "Bitte wähle einen Anzeigenamen mit mindestens 2 Zeichen und eine unterstützte Sprache."
    ),
    "settings.profile.name": "Anzeigename",
    "settings.profile.language": "Bevorzugte Sprache",
    "settings.profile.lang.en": "English",
    "settings.profile.lang.de": "Deutsch",
    "settings.profile.timezone": "Zeitzone",
    "settings.profile.timezone_hint": (
        "Wird für die Anzeige von Anstoßzeiten und anderen Daten verwendet. "
        "Die gespeicherten Zeiten bleiben in UTC; diese Einstellung beeinflusst "
        "nur die Anzeige. Standard der Seite: {default}."
    ),
    "settings.profile.signed_in_html": (
        "Angemeldet als <code>{email}</code>. Konto angelegt am {created}."
    ),
    "settings.profile.submit": "Profil speichern",
    "settings.avatar.current": "Dein aktueller Avatar.",
    "settings.avatar.none": "Kein Avatar gesetzt - ein Platzhalter wird angezeigt.",
    "settings.avatar.upload_label": "Neuen Avatar hochladen",
    "settings.avatar.upload_hint": "PNG oder JPEG, <= 200 KiB. Wird auf 128x128 verkleinert.",
    "settings.avatar.upload_submit": "Hochladen",
    "settings.avatar.remove": "Aktuellen Avatar entfernen",
    "settings.avatar.error.empty": "Bitte wähle eine Datei zum Hochladen.",
    "settings.avatar.error.too_large": "Das Bild ist zu groß. Maximal 200 KiB.",
    "settings.avatar.error.bad_type": "Nur PNG- und JPEG-Bilder werden akzeptiert.",
    "settings.avatar.error.corrupt": "Diese Datei sieht nicht wie ein gültiges Bild aus.",
    "settings.password.current": "Aktuelles Passwort",
    "settings.password.new": "Neues Passwort",
    "settings.password.new_hint": "Mindestens {min} Zeichen.",
    "settings.password.confirm": "Neues Passwort bestätigen",
    "settings.password.submit": "Passwort ändern",
    "settings.password.error.mismatch": "Die beiden Felder für das neue Passwort stimmen nicht überein.",
    "settings.password.error.too_short": "Das neue Passwort muss mindestens {min} Zeichen lang sein.",
    "settings.password.error.wrong_current": "Das aktuelle Passwort ist falsch.",
    # --- Admin dashboard ------------------------------------------------
    "admin.crumb.root": "Admin",
    "admin.crumb.games": "Spielergebnisse",
    "admin.crumb.questions": "Sonderfragen",
    "admin.dash.title": "Admin-Dashboard",
    "admin.dash.subtitle": (
        "Schnellüberblick über offene Aufgaben. Detaillierte Bedienung pro Bereich darunter."
    ),
    "admin.dash.users": "Spieler",
    "admin.dash.users_summary_one": "{admin} Admin, {bets} Tipp abgegeben",
    "admin.dash.users_summary_few": "{admin} Admin, {bets} Tipps abgegeben",
    "admin.dash.users_summary_many": "{admin} Admins, {bets} Tipps abgegeben",
    "admin.dash.matches": "Spiele",
    "admin.dash.matches_upcoming": "{count} noch ausstehend",
    "admin.dash.pending": "Offene Ergebnisse",
    "admin.dash.pending_more": "Spiele angepfiffen, aber noch kein Ergebnis >",
    "admin.dash.pending_done": "alles erledigt - Ergebnisse eintragen >",
    "admin.dash.manage": "Verwaltung",
    "admin.dash.manage_results": "Spielergebnisse eintragen / ändern",
    "admin.dash.manage_questions": "Sonderfragen",
    # --- Admin games ---------------------------------------------------
    "admin.games.title": "Spielergebnisse",
    "admin.games.subtitle": (
        "Trage das Endergebnis pro Spiel ein. Beide Felder leer lassen, um "
        'ein Ergebnis zu löschen. Optionale Anmerkungen (z. B. "n. V.", '
        '"5:3 i. E.") erscheinen unter dem Ergebnis auf der Spielplan-Seite.'
    ),
    "admin.games.col.notes": "Anmerkungen",
    "admin.games.col.save": "Speichern",
    "admin.games.notes.placeholder": "n. V., i. E.",
    "admin.games.aria.home_score": "Heimtor für Spiel {id}",
    "admin.games.aria.away_score": "Auswärtstor für Spiel {id}",
    "admin.games.aria.home_team": "Heimmannschaft für Spiel {id}",
    "admin.games.aria.away_team": "Auswärtsmannschaft für Spiel {id}",
    "admin.games.aria.notes": "Anmerkungen für Spiel {id}",
    "admin.games.aria.save": "Zeile für Spiel {id} speichern",
    "admin.games.save_row": "Ergebnis, Anmerkungen und Mannschaften speichern",
    # --- Admin questions -----------------------------------------------
    "admin.questions.title": "Sonderfragen",
    "admin.questions.subtitle_html": (
        "Tipps abseits des Spielplans. Jede Zeile hat einen eigenen Stichtag "
        "(UTC) und einen eigenen Punktwert. Nach Ablauf des Stichtags wird "
        "die richtige Antwort eingetragen; alternative Schreibweisen mit "
        "Komma trennen (z. B. <code>Mbappe,Mbappé,Kylian Mbappe</code>) - "
        "Groß-/Kleinschreibung ist egal, es zählt enthalten-sein."
    ),
    "admin.questions.saved_html": "Gespeichert - {what}.",
    "admin.questions.saved.created": "erstellt",
    "admin.questions.saved.updated": "aktualisiert",
    "admin.questions.saved.deleted": "gelöscht",
    "admin.questions.new": "Neue Frage",
    "admin.questions.field.question": "Frage",
    "admin.questions.field.deadline": "Stichtag (UTC)",
    "admin.questions.field.points": "Pkt.",
    "admin.questions.field.correct_optional": "Richtige Antwort (jetzt noch optional)",
    "admin.questions.field.correct": "Richtige Antwort",
    "admin.questions.placeholder.correct": "Varianten kommagetrennt",
    "admin.questions.submit_new": "Frage anlegen",
    "admin.questions.col.deadline": "Stichtag",
    "admin.questions.col.points": "Pkt.",
    "admin.questions.col.answers_count_title": "Anzahl Spieler, die geantwortet haben",
    "admin.questions.empty": "Noch keine Fragen. Mit dem Formular oben die erste anlegen.",
    "admin.questions.confirm_delete": "Diese Frage und alle bisher abgegebenen Antworten löschen?",
    "admin.questions.aria.question": "Fragetext für Frage {id}",
    "admin.questions.aria.deadline": "Stichtag für Frage {id}",
    "admin.questions.aria.points": "Punkte für Frage {id}",
    "admin.questions.aria.correct": "Richtige Antwort für Frage {id}",
    "admin.questions.aria.save": "Frage {id} speichern",
    "admin.questions.aria.delete": "Frage {id} löschen",
    # --- User-facing validation errors ---------------------------------
    "error.bet.deadline_passed": "Das Spiel wurde bereits angepfiffen.",
    "error.question.deadline_passed": "Der Stichtag ist bereits abgelaufen.",
    "error.score.not_int": "{field} muss eine ganze Zahl sein.",
    "error.score.range": "{field} muss zwischen {min} und {max} liegen.",
    "error.score.home": "Heimtor",
    "error.score.away": "Auswärtstor",
    "error.score.invalid": "Bitte ganze Zahlen für beide Tore eingeben.",
    "error.score.partial": "Bitte beide Tore eintragen oder beide leeren, um den Tipp zu löschen.",
    "error.question.text_too_short": "Der Fragetext muss mindestens {min} Zeichen lang sein.",
    "error.question.text_too_long": "Der Fragetext darf höchstens {max} Zeichen lang sein.",
    "error.question.points_not_int": "Punkte müssen eine ganze Zahl sein.",
    "error.question.points_required": "Punkte sind erforderlich.",
    "error.question.points_range": "Punkte müssen zwischen {min} und {max} liegen.",
    "error.question.correct_too_long": "Die richtige Antwort darf höchstens {max} Zeichen lang sein.",
    "error.question.answer_empty": "Die Antwort darf nicht leer sein.",
    "error.question.answer_too_long": "Die Antwort darf höchstens {max} Zeichen lang sein.",
    "error.question.deadline_required": "Stichtag ist erforderlich.",
    "error.question.deadline_invalid": (
        "Ungültiger Stichtag. Bitte nutze die Datums-/Uhrzeitauswahl."
    ),
    "error.shout.empty": "Die Nachricht darf nicht leer sein.",
    "error.shout.too_long": "Die Nachricht darf höchstens {max} Zeichen lang sein.",
    "error.admin.notes_too_long": "Anmerkungen dürfen höchstens {max} Zeichen lang sein.",
    "error.team.unknown": "Unbekannte Mannschaft.",
    "error.team.same": "Heim- und Auswärtsmannschaft müssen sich unterscheiden.",
    "error.team.not_knockout": "Mannschaften der Gruppenspiele sind nicht editierbar.",
    # --- Date helpers --------------------------------------------------
    "date.day.0": "Mo",
    "date.day.1": "Di",
    "date.day.2": "Mi",
    "date.day.3": "Do",
    "date.day.4": "Fr",
    "date.day.5": "Sa",
    "date.day.6": "So",
    "date.month.1": "Jan",
    "date.month.2": "Feb",
    "date.month.3": "Mär",
    "date.month.4": "Apr",
    "date.month.5": "Mai",
    "date.month.6": "Jun",
    "date.month.7": "Jul",
    "date.month.8": "Aug",
    "date.month.9": "Sep",
    "date.month.10": "Okt",
    "date.month.11": "Nov",
    "date.month.12": "Dez",
}


TRANSLATIONS: Final[Mapping[str, Mapping[str, str]]] = {
    "en": EN,
    "de": DE,
}


# ---------------------------------------------------------------------------
# Lookup API
# ---------------------------------------------------------------------------


def resolve_language(user_language: str | None, *, default: str = DEFAULT_LANGUAGE) -> str:
    """Pick the language code we'll serve for *user_language*.

    Returns *default* for ``None`` or any unsupported code, so anonymous
    visitors and users with stale preferences never blow up rendering.
    """
    if user_language is None:
        return default
    code = user_language.strip().lower()
    if code in TRANSLATIONS:
        return code
    return default


def parse_accept_language(header: str | None) -> list[str]:
    """Parse an HTTP ``Accept-Language`` header into a ranked code list.

    Behaviour matches the relevant parts of RFC 9110 §12.5.4 closely
    enough for our two-language catalogue:

    * Tokens are split on commas and tagged with their ``q`` value
      (defaulting to 1.0 if absent).
    * Sub-tags are stripped (``de-DE`` -> ``de``, ``en-US`` -> ``en``).
    * The wildcard ``*`` and items with ``q=0`` are dropped.
    * Items are sorted by descending quality, then by original order
      to keep parsing stable for items at the same priority.
    * Only supported language codes are returned, and duplicates are
      collapsed to the first occurrence.

    Returns an empty list for ``None`` / empty input. The caller decides
    what to do when nothing matches (typically: fall back to the site
    default).
    """
    if not header:
        return []

    parsed: list[tuple[float, int, str]] = []
    for index, raw_item in enumerate(header.split(",")):
        parts = raw_item.strip().split(";")
        tag = parts[0].strip().lower()
        if not tag or tag == "*":
            continue
        primary = tag.split("-")[0]
        if primary not in TRANSLATIONS:
            continue
        quality = 1.0
        for param in parts[1:]:
            param = param.strip()
            if param.startswith("q="):
                try:
                    quality = float(param[2:])
                except ValueError:
                    quality = 0.0
                break
        if quality <= 0:
            continue
        parsed.append((quality, index, primary))

    parsed.sort(key=lambda item: (-item[0], item[1]))
    seen: set[str] = set()
    ordered: list[str] = []
    for _, _, code in parsed:
        if code in seen:
            continue
        seen.add(code)
        ordered.append(code)
    return ordered


def gettext(key: str, language: str = DEFAULT_LANGUAGE, /, **kwargs: object) -> str:
    """Return the translated message for *key* in *language*.

    Lookup chain:

    1. The requested-language catalogue.
    2. The English catalogue (since that is the authoritative key list).
    3. The key itself, so missing translations show up obviously rather
       than as an empty span.

    ``**kwargs`` get applied with :py:meth:`str.format` after lookup; this
    keeps placeholders consistent across languages without forcing every
    call site to know how to render a particular value.
    """
    catalog = TRANSLATIONS.get(language) or EN
    template = catalog.get(key)
    if template is None:
        template = EN.get(key)
    if template is None:
        LOGGER.debug("Missing translation key %r for language %r", key, language)
        return key
    if not kwargs:
        return template
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        LOGGER.warning("Bad format args for %r (%s): %r", key, language, kwargs)
        return template


__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "TRANSLATIONS",
    "EN",
    "DE",
    "gettext",
    "parse_accept_language",
    "resolve_language",
]
