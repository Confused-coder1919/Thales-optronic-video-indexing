#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.airgap.yml"
RUNTIME_COMPOSE_FILE="$ROOT_DIR/docker-compose.airgap.runtime.yml"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-thales-optronic-video-indexing}"
OUTPUT_DIR="$ROOT_DIR/airgap-bundle"
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Create an air-gap transfer bundle containing:
- prebuilt Docker images for the runtime stack
- exported named volumes (entity-data, hf-cache, ollama-models)
- runtime-only compose file and import helper

Options:
  --compose-file PATH    Source compose file used to resolve image names
                         Default: $COMPOSE_FILE
  --project-name NAME    Compose project name used for named volumes
                         Default: $PROJECT_NAME
  --output-dir PATH      Bundle output directory
                         Default: $OUTPUT_DIR
  --dry-run              Print what would be exported without writing files
  -h, --help             Show this help
EOF
}

log() {
  printf '[airgap-export] %s\n' "$*"
}

die() {
  printf '[airgap-export] ERROR: %s\n' "$*" >&2
  exit 1
}

resolve_volume_name() {
  local logical_name="$1"
  if docker volume inspect "$logical_name" >/dev/null 2>&1; then
    printf '%s' "$logical_name"
    return 0
  fi
  if docker volume inspect "${PROJECT_NAME}_${logical_name}" >/dev/null 2>&1; then
    printf '%s' "${PROJECT_NAME}_${logical_name}"
    return 0
  fi
  return 1
}

volume_entry_count() {
  local actual_name="$1"
  docker run --rm -v "${actual_name}:/from:ro" redis:7-alpine sh -lc \
    'find /from -mindepth 1 | wc -l'
}

while (($#)); do
  case "$1" in
    --compose-file)
      COMPOSE_FILE="$2"
      shift 2
      ;;
    --project-name)
      PROJECT_NAME="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
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

cd "$ROOT_DIR"

command -v docker >/dev/null 2>&1 || die "docker is required"
docker version >/dev/null 2>&1 || die "Docker daemon is not reachable"
[[ -f "$COMPOSE_FILE" ]] || die "Compose file not found: $COMPOSE_FILE"
[[ -f "$RUNTIME_COMPOSE_FILE" ]] || die "Runtime compose file not found: $RUNTIME_COMPOSE_FILE"

IMAGES=()
while IFS= read -r image_name; do
  [[ -n "$image_name" ]] || continue
  IMAGES+=("$image_name")
done < <(docker compose -f "$COMPOSE_FILE" config --images | sort -u)
[[ ${#IMAGES[@]} -gt 0 ]] || die "No images resolved from compose file"

LOGICAL_VOLUMES=("entity-data" "hf-cache" "ollama-models")
ACTUAL_VOLUMES=()

for logical_name in "${LOGICAL_VOLUMES[@]}"; do
  actual_name="$(resolve_volume_name "$logical_name" || true)"
  [[ -n "$actual_name" ]] || die "Required volume not found: $logical_name (project=$PROJECT_NAME)"
  ACTUAL_VOLUMES+=("$actual_name")
done

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BUNDLE_DIR="${OUTPUT_DIR%/}/thales-airgap-bundle-${TIMESTAMP}"

log "Project name: $PROJECT_NAME"
log "Source compose: $COMPOSE_FILE"
log "Runtime compose: $RUNTIME_COMPOSE_FILE"
log "Output bundle: $BUNDLE_DIR"
log "Images:"
for image in "${IMAGES[@]}"; do
  log "  - $image"
done
log "Volumes:"
for logical_name in "${LOGICAL_VOLUMES[@]}"; do
  index=0
  for candidate in "${LOGICAL_VOLUMES[@]}"; do
    [[ "$candidate" == "$logical_name" ]] && break
    index=$((index + 1))
  done
  actual_name="${ACTUAL_VOLUMES[$index]}"
  entry_count="$(volume_entry_count "$actual_name" | tr -d '[:space:]')"
  log "  - $logical_name -> $actual_name (${entry_count:-0} entries)"
done

if [[ "$DRY_RUN" == "1" ]]; then
  log "Dry run only. No files were written."
  exit 0
fi

mkdir -p "$BUNDLE_DIR/images" "$BUNDLE_DIR/volumes"
cp "$RUNTIME_COMPOSE_FILE" "$BUNDLE_DIR/docker-compose.airgap.runtime.yml"
cp "$ROOT_DIR/.env.example" "$BUNDLE_DIR/.env.example"
cp "$ROOT_DIR/scripts/import_airgap_bundle.sh" "$BUNDLE_DIR/import_airgap_bundle.sh"
chmod +x "$BUNDLE_DIR/import_airgap_bundle.sh"

log "Saving Docker images..."
docker save -o "$BUNDLE_DIR/images/docker-images.tar" "${IMAGES[@]}"

log "Exporting named volumes..."
for logical_name in "${LOGICAL_VOLUMES[@]}"; do
  index=0
  for candidate in "${LOGICAL_VOLUMES[@]}"; do
    [[ "$candidate" == "$logical_name" ]] && break
    index=$((index + 1))
  done
  actual_name="${ACTUAL_VOLUMES[$index]}"
  docker run --rm \
    -v "${actual_name}:/from:ro" \
    -v "$BUNDLE_DIR/volumes:/to" \
    redis:7-alpine \
    sh -lc "tar -C /from -czf /to/${logical_name}.tar.gz ."
done

cat >"$BUNDLE_DIR/manifest.txt" <<EOF
bundle_created_utc=${TIMESTAMP}
project_name=${PROJECT_NAME}
source_compose=$(basename "$COMPOSE_FILE")
runtime_compose=docker-compose.airgap.runtime.yml

[images]
$(printf '%s\n' "${IMAGES[@]}")

[volumes]
$(for i in "${!LOGICAL_VOLUMES[@]}"; do printf '%s=%s\n' "${LOGICAL_VOLUMES[$i]}" "${ACTUAL_VOLUMES[$i]}"; done)
EOF

(
  cd "$BUNDLE_DIR"
  shasum -a 256 images/docker-images.tar volumes/*.tar.gz docker-compose.airgap.runtime.yml .env.example import_airgap_bundle.sh manifest.txt > SHA256SUMS
)

log "Bundle created: $BUNDLE_DIR"
log "Transfer this directory to the air-gapped environment, then run:"
log "  ./import_airgap_bundle.sh --bundle-dir . --start"
