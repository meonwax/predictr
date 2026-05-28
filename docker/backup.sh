#!/bin/sh
# Daily Postgres backup loop for predictr.
#
# Runs `pg_dump -Fc` once a day at $SCHEDULE_HOUR_UTC (default 04:00 UTC,
# which equals 06:00 CEST during the WC 2026 tournament window). Output
# files land in $BACKUP_DIR (default /backups, bind-mounted from the host
# in docker-compose.yml).
#
# Why a sleep loop and not crond? Busybox crond's foreground mode is fiddly
# inside containers (PID 1, signal handling, mail spool), and a hand-rolled
# sleep loop is ~30 lines we fully understand. Logs go to stdout so
# `docker compose logs postgres-backup` shows the last few dumps.
#
# No retention: predictr only runs during the WC tournament, so the total
# number of dumps is bounded (~40-50 days). Operators who want retention
# can add a `find ... -mtime +N -delete` line below the call to run_backup.
#
# Environment:
#   PGHOST              postgres service name              (default: postgres)
#   PGUSER              role used by pg_dump               (default: predictr)
#   PGDATABASE          database to dump                   (default: predictr)
#   PGPASSWORD          role password                      (required)
#   BACKUP_DIR          where to write *.pgdump files      (default: /backups)
#   SCHEDULE_HOUR_UTC   hour (0-23) UTC to run backup at   (default: 4)
#   BACKUP_ON_STARTUP   if "1", run one immediate backup   (default: 0)
#                       on container start (useful for ops
#                       sanity-checking after a deploy).
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
SCHEDULE_HOUR_UTC="${SCHEDULE_HOUR_UTC:-4}"
PGHOST="${PGHOST:-postgres}"
PGUSER="${PGUSER:-predictr}"
PGDATABASE="${PGDATABASE:-predictr}"
export PGHOST PGUSER PGDATABASE
# PGPASSWORD is left in the inherited environment as-is - exporting it
# here is redundant and would also surface in `env` dumps on debug.

log() {
    printf '%s [predictr-backup] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

if [ ! -d "$BACKUP_DIR" ]; then
    log "creating backup directory $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Validate the schedule hour early so a typo doesn't silently sleep for 24h.
case "$SCHEDULE_HOUR_UTC" in
    ''|*[!0-9]*) log "FATAL: SCHEDULE_HOUR_UTC=$SCHEDULE_HOUR_UTC is not an integer"; exit 2 ;;
esac
if [ "$SCHEDULE_HOUR_UTC" -lt 0 ] || [ "$SCHEDULE_HOUR_UTC" -gt 23 ]; then
    log "FATAL: SCHEDULE_HOUR_UTC=$SCHEDULE_HOUR_UTC out of range 0..23"
    exit 2
fi

run_backup() {
    out="$BACKUP_DIR/predictr-$(date -u '+%Y-%m-%dT%H-%M-%SZ').pgdump"
    log "starting pg_dump -> $out"
    if pg_dump -Fc -f "$out"; then
        size="$(wc -c < "$out" 2>/dev/null || echo 0)"
        log "finished, $size bytes"
    else
        rc=$?
        log "FAILED with exit $rc; removing partial file"
        rm -f "$out"
        return $rc
    fi
}

seconds_until_next_run() {
    # Pure-arithmetic calculation; portable across busybox/GNU date.
    h=$(date -u '+%H'); h="${h#0}"; h="${h:-0}"
    m=$(date -u '+%M'); m="${m#0}"; m="${m:-0}"
    s=$(date -u '+%S'); s="${s#0}"; s="${s:-0}"
    now_in_day=$(( h * 3600 + m * 60 + s ))
    target_in_day=$(( SCHEDULE_HOUR_UTC * 3600 ))
    if [ "$now_in_day" -lt "$target_in_day" ]; then
        echo $(( target_in_day - now_in_day ))
    else
        # Already past today's slot - sleep till tomorrow's.
        echo $(( 86400 - now_in_day + target_in_day ))
    fi
}

log "starting backup loop, schedule: ${SCHEDULE_HOUR_UTC}:00 UTC daily, dir: $BACKUP_DIR"

if [ "${BACKUP_ON_STARTUP:-0}" = "1" ]; then
    log "BACKUP_ON_STARTUP=1, running an immediate backup"
    run_backup || log "startup backup failed - continuing into the schedule loop"
fi

while true; do
    sleep_s="$(seconds_until_next_run)"
    log "sleeping ${sleep_s}s until next run"
    # `sleep` is interruptible by SIGTERM, so `docker compose down`
    # exits the script promptly instead of waiting up to a day.
    sleep "$sleep_s"
    run_backup || log "scheduled backup failed - will retry tomorrow"
done
