#!/bin/bash
set -eu
cleanup() {
  docker compose -f docker-compose-database.yml rm -fsv
}
trap cleanup EXIT
docker compose -f docker-compose-database.yml up
