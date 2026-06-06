# syntax=docker/dockerfile:1.7
#
# Image for the predictr postgres-backup sidecar. It is the official
# postgres image (so pg_dump matches the server version) with our backup
# loop script baked in. Baking the script in - rather than bind-mounting
# it from docker-compose.yml - means a remote daemon (e.g. deploying over
# an SSH Docker context) does not need a repo checkout on the daemon host
# to find the script; the build context carries it.
FROM postgres:16-alpine

COPY docker/backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

ENTRYPOINT ["/bin/sh", "/usr/local/bin/backup.sh"]
