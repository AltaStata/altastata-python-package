#!/usr/bin/env bash
# Canonical launcher for the local Jupyter stack (repo root .env + optional HPCS override).
#
# Why this exists:
#   `docker compose -f containers/jupyter/docker-compose.yml --project-directory .`
#   loads ARCH/VERSION from the root .env, but then:
#     - relative volume paths (../../examples) resolve incorrectly
#     - containers/jupyter/docker-compose.override.yml is NOT auto-merged
#   so HPCS mounts (grep11 YAML + privkey blob) silently disappear.
#
# This script always:
#   1. Uses containers/jupyter as the Compose project directory (correct ../../ paths)
#   2. Passes the repo-root .env for ARCH / VERSION
#   3. Explicitly includes docker-compose.override.yml when present
#
# Usage (from repo root or anywhere):
#   ./containers/jupyter/up.sh              # → up -d
#   ./containers/jupyter/up.sh up -d --force-recreate
#   ./containers/jupyter/up.sh logs -f
#   ./containers/jupyter/up.sh down

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_DIR="${SCRIPT_DIR}"
ENV_FILE="${REPO_ROOT}/.env"
OVERRIDE_FILE="${COMPOSE_DIR}/docker-compose.override.yml"
EXAMPLE_OVERRIDE="${COMPOSE_DIR}/docker-compose.override.example.yml"

if [[ ! -f "${COMPOSE_DIR}/docker-compose.yml" ]]; then
  echo "ERROR: ${COMPOSE_DIR}/docker-compose.yml not found" >&2
  exit 1
fi

ARGS=(--project-directory "${COMPOSE_DIR}" -f "${COMPOSE_DIR}/docker-compose.yml")

if [[ -f "${ENV_FILE}" ]]; then
  ARGS+=(--env-file "${ENV_FILE}")
else
  echo "WARNING: ${ENV_FILE} missing — ARCH defaults to amd64, VERSION may be empty." >&2
  echo "         Copy or create .env (see version.sh / update-version.sh)." >&2
fi

if [[ -f "${OVERRIDE_FILE}" ]]; then
  ARGS+=(-f "${OVERRIDE_FILE}")
  echo "Including local override: ${OVERRIDE_FILE}"
else
  echo "NOTE: no ${OVERRIDE_FILE}"
  echo "      For HPCS notebooks, copy the example and edit host paths:"
  echo "        cp ${EXAMPLE_OVERRIDE} ${OVERRIDE_FILE}"
fi

if [[ $# -eq 0 ]]; then
  set -- up -d
fi

echo "Running: docker compose ${ARGS[*]} $*"
exec docker compose "${ARGS[@]}" "$@"
