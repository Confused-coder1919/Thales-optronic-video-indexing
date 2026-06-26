#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR=""
COMPOSE_FILE=""
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-thales-optronic-video-indexing}"
DRY_RUN=0
START_STACK=0
OVERWRITE_VOLUMES=0

usage() {
  cat <<EOF
Usage: $(basename "$0") --bundle-dir PATH [options]

Load a pre-exported air-gap bundle:
- docker load runtime images
- restore entity-data / hf-cache / ollama-models named volumes
- optionally start the runtime stack with docker-compose.airgap.runtime.yml

Options:
  --bundle-dir PATH      Extracted bundle directory created by export_airgap_bundle.sh
  --compose-file PATH    Runtime compose file to start after import
                         Default: <bundle-dir>/docker-compose.airgap.runtime.yml
  --project-name NAME    Compose project name used for named volumes
                         Default: $PROJECT_NAME
  --overwrite-volumes    Replace existing destination volumes
  --start                Start the runtime stack after import
  --dry-run              Print what would be done without making changes
  -h, --help             Show this help
EOF
}

log() {
  printf '[airgap-import] %s\n' "$*"
}

die() {
  printf '[airgap-import] ERROR: %s\n' "$*" >&2
  exit 1
}

restore_volume() {
  local logical_name="$1"
  local archive_path="$2"
  local actual_name="${PROJECT_NAME}_${logical_name}"

  if docker volume inspect "$actual_name" >/dev/null 2>&1; then
    if [[ "$OVERWRITE_VOLUMES" != "1" ]]; then
      die "Destination volume already exists: $actual_name (use --overwrite-volumes)"
    fi
    docker volume rm -f "$actual_name" >/dev/null
  fi

  docker volume create "$actual_name" >/dev/null
  docker run --rm \
    -v "${actual_name}:/to" \
    -v "$(dirname "$archive_path"):/from:ro" \
    redis:7-alpine \
    sh -lc "find /to -mindepth 1 -delete && tar -C /to -xzf /from/$(basename "$archive_path")"
}

while (($#)); do
  case "$1" in
    --bundle-dir)
      BUNDLE_DIR="$2"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="$2"
      shift 2
      ;;
    --project-name)
      PROJECT_NAME="$2"
      shift 2
      ;;
    --overwrite-volumes)
      OVERWRITE_VOLUMES=1
      shift
      ;;
    --start)
      START_STACK=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

[[ -n "$BUNDLE_DIR" ]] || { usage; exit 1; }

BUNDLE_DIR="$(cd "$BUNDLE_DIR" && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$BUNDLE_DIR/docker-compose.airgap.runtime.yml}"

command -v docker >/dev/null 2>&1 || die "docker is required"
docker version >/dev/null 2>&1 || die "Docker daemon is not reachable"
[[ -d "$BUNDLE_DIR" ]] || die "Bundle directory not found: $BUNDLE_DIR"
[[ -f "$BUNDLE_DIR/images/docker-images.tar" ]] || die "Missing images/docker-images.tar in bundle"
[[ -f "$COMPOSE_FILE" ]] || die "Runtime compose file not found: $COMPOSE_FILE"

LOGICAL_VOLUMES=("entity-data" "hf-cache" "ollama-models")

log "Bundle dir: $BUNDLE_DIR"
log "Compose file: $COMPOSE_FILE"
log "Project name: $PROJECT_NAME"
for logical_name in "${LOGICAL_VOLUMES[@]}"; do
  [[ -f "$BUNDLE_DIR/volumes/${logical_name}.tar.gz" ]] || die "Missing volume archive: ${logical_name}.tar.gz"
done

if [[ -f "$BUNDLE_DIR/SHA256SUMS" ]]; then
  log "Verifying bundle checksums..."
  (
    cd "$BUNDLE_DIR"
    shasum -a 256 -c SHA256SUMS
  )
fi

if [[ "$DRY_RUN" == "1" ]]; then
  log "Would load images from: $BUNDLE_DIR/images/docker-images.tar"
  for logical_name in "${LOGICAL_VOLUMES[@]}"; do
    log "Would restore volume: ${PROJECT_NAME}_${logical_name} from $BUNDLE_DIR/volumes/${logical_name}.tar.gz"
  done
  if [[ "$START_STACK" == "1" ]]; then
    log "Would start stack: docker compose -f $COMPOSE_FILE up -d"
  fi
  exit 0
fi

log "Loading Docker images..."
docker load -i "$BUNDLE_DIR/images/docker-images.tar"

log "Restoring named volumes..."
for logical_name in "${LOGICAL_VOLUMES[@]}"; do
  restore_volume "$logical_name" "$BUNDLE_DIR/volumes/${logical_name}.tar.gz"
done

if [[ "$START_STACK" == "1" ]]; then
  log "Starting runtime stack..."
  docker compose -f "$COMPOSE_FILE" up -d
fi

log "Import complete."
