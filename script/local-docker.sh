#!/usr/bin/env bash
# Start a local mc_bd container stack (Postgres + Redis + API) for development testing.
#
# Usage:
#   ./script/local-docker.sh up          # build (if needed) and start
#   ./script/local-docker.sh build       # build mc_bd image only
#   ./script/local-docker.sh down        # stop and remove containers
#   ./script/local-docker.sh logs        # follow mc_bd logs
#   ./script/local-docker.sh smoke       # verify backend import + HTTP
#   ./script/local-docker.sh init-db     # create DATABASE_SCHEMA (mc) on existing Postgres
#
# Environment overrides (optional):
#   BUILD_FROM=ghcr.io/.../base-python:tag
#   MC_BD_HOST_PORT=8001
#   DOCKER_POSTGRES_MAP_PORT=15432
#   DOCKER_REDIS_MAP_PORT=16379

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="${ROOT}/deploy/backend/docker-compose"
COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.local.yml"
IMAGE_NAME="${MC_BD_IMAGE:-mc_bd:local}"
BUILD_FROM="${BUILD_FROM:-ghcr.io/muthur-command/base-python:3.14-alpine3.23-2026.06.2}"
MC_BD_HOST_PORT="${MC_BD_HOST_PORT:-8001}"

export BUILD_FROM MC_BD_HOST_PORT DOCKER_POSTGRES_MAP_PORT DOCKER_REDIS_MAP_PORT

usage() {
  sed -n '3,16p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
}

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "${COMPOSE_FILE}" "$@"
  else
    echo "error: docker compose (v2) or docker-compose is required" >&2
    exit 1
  fi
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "error: docker is not installed or not in PATH" >&2
    exit 1
  fi
}

build_image() {
  require_docker
  echo "==> Building ${IMAGE_NAME} (BUILD_FROM=${BUILD_FROM})"
  if docker buildx version >/dev/null 2>&1; then
    DOCKER_BUILDKIT=1 docker build \
      --build-arg "BUILD_FROM=${BUILD_FROM}" \
      -t "${IMAGE_NAME}" \
      "${ROOT}"
  else
    echo "warning: buildx not found; trying legacy docker build (Dockerfile uses BuildKit cache mounts)" >&2
    DOCKER_BUILDKIT=1 docker build \
      --build-arg "BUILD_FROM=${BUILD_FROM}" \
      -t "${IMAGE_NAME}" \
      "${ROOT}" || {
        echo "error: build failed. Install docker-buildx-plugin or enable BuildKit." >&2
        exit 1
      }
  fi
}

cmd_init_db() {
  require_docker
  local pg_container="${MC_BD_PG_CONTAINER:-mc_bd_local_postgres}"
  local db_name="${DATABASE_SCHEMA:-mc}"
  if ! docker inspect "${pg_container}" >/dev/null 2>&1; then
    echo "error: postgres container '${pg_container}' is not running" >&2
    exit 1
  fi
  echo "==> Ensuring PostgreSQL database '${db_name}' exists"
  docker exec "${pg_container}" psql -U postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname = '${db_name}'" | grep -q 1 \
    || docker exec "${pg_container}" psql -U postgres -c "CREATE DATABASE ${db_name};"
  echo "OK: database '${db_name}' is ready"
}

cmd_up() {
  require_docker
  cd "${COMPOSE_DIR}"
  compose_cmd up -d --build mc_postgres mc_redis
  cmd_init_db
  compose_cmd up -d mc_bd
  echo
  echo "mc_bd local stack is starting."
  echo "  API:      http://127.0.0.1:${MC_BD_HOST_PORT}/docs"
  echo "  Postgres: 127.0.0.1:${DOCKER_POSTGRES_MAP_PORT:-15432}"
  echo "  Redis:    127.0.0.1:${DOCKER_REDIS_MAP_PORT:-16379}"
  echo
  echo "Logs: ${0} logs"
}

cmd_down() {
  require_docker
  cd "${COMPOSE_DIR}"
  compose_cmd down
}

cmd_down_purge() {
  require_docker
  cd "${COMPOSE_DIR}"
  compose_cmd down -v
}

cmd_logs() {
  require_docker
  cd "${COMPOSE_DIR}"
  compose_cmd logs -f "${1:-mc_bd}"
}

cmd_ps() {
  require_docker
  cd "${COMPOSE_DIR}"
  compose_cmd ps
}

cmd_smoke() {
  require_docker
  echo "==> Checking backend package in image"
  docker run --rm --entrypoint python3 "${IMAGE_NAME}" \
    -c "import backend; print('backend:', backend.__file__)"

  echo "==> Waiting for http://127.0.0.1:${MC_BD_HOST_PORT}/docs"
  for _ in $(seq 1 60); do
    if curl -fsS -o /dev/null "http://127.0.0.1:${MC_BD_HOST_PORT}/docs"; then
      echo "OK: /docs responded"
      exit 0
    fi
    sleep 2
  done
  echo "error: mc_bd did not become ready within 120s" >&2
  echo "hint: run '${0} logs' for details" >&2
  exit 1
}

cmd_shell() {
  require_docker
  docker run --rm -it --entrypoint sh "${IMAGE_NAME}"
}

cmd_restart() {
  require_docker
  cd "${COMPOSE_DIR}"
  compose_cmd restart mc_bd
}

main() {
  local cmd="${1:-up}"
  shift || true

  case "${cmd}" in
    -h|--help|help)
      usage
      ;;
    build)
      build_image
      ;;
    up|start)
      cmd_up "$@"
      ;;
    down|stop)
      cmd_down "$@"
      ;;
    purge|down-v)
      cmd_down_purge "$@"
      ;;
    logs)
      cmd_logs "$@"
      ;;
    ps|status)
      cmd_ps "$@"
      ;;
    smoke)
      cmd_smoke "$@"
      ;;
    shell)
      cmd_shell "$@"
      ;;
    restart)
      cmd_restart "$@"
      ;;
    init-db)
      cmd_init_db "$@"
      ;;
    *)
      echo "unknown command: ${cmd}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
