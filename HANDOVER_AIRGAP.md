# Thales Video Indexing: Air-Gap Handover

## Purpose

This document is the handover note for deploying the Thales video indexing project
into an air-gapped environment.

The required question was:

> Would it be possible (as mentioned during the presentation) to have all of it
> in Docker? So that we can run it on our air gap infra (including MISTRAL VLM
> etc...). We cannot call the MISTRAL API from our infra.

## Short Answer

Yes, the full platform can be run in Docker on air-gapped infrastructure without
calling the Mistral API.

The delivered Dockerized stack includes:

- frontend UI
- backend API
- background worker
- Redis
- local model service

## Important Clarification

The current offline deployment does **not** run a self-hosted Mistral / Pixtral
model.

Instead, the local offline path uses:

- local Hugging Face models for the active backend stack
  - Whisper / faster-whisper
  - CLIP
  - BLIP
  - sentence-transformers embeddings
- local Ollama-hosted models for the LLM / VLM replacement path
  - `llama3.1`
  - `llava:7b`

So the correct statement is:

- `YES`: the project can run fully in Docker in an air-gapped environment
- `YES`: it can run without calling the Mistral API
- `NO`: the current implementation is not a packaged local Mistral/Pixtral runtime

If strict self-hosted Mistral / Pixtral is required, that is a separate model
integration task and is not what is currently delivered.

## What Is Delivered

### Source Project

The full source repository, including:

- backend code
- frontend code
- Docker files
- air-gap compose files
- export/import helper scripts
- README and environment template

### Air-Gap Runtime Artifacts

The air-gap deployment path uses these runtime files:

- `docker-compose.airgap.yml`
  - build-and-preload compose file for a connected staging machine
- `docker-compose.airgap.runtime.yml`
  - runtime-only compose file for the disconnected target machine
- `scripts/export_airgap_bundle.sh`
  - creates the transfer bundle
- `scripts/import_airgap_bundle.sh`
  - imports the transfer bundle into the target environment

## Expected Bundle Contents

The export process creates a bundle directory containing:

```text
thales-airgap-bundle-<timestamp>/
  docker-compose.airgap.runtime.yml
  .env.example
  import_airgap_bundle.sh
  manifest.txt
  SHA256SUMS
  images/docker-images.tar
  volumes/entity-data.tar.gz
  volumes/hf-cache.tar.gz
  volumes/ollama-models.tar.gz
```

## Deployment Model

### Connected Staging Machine

This machine is used to:

- build Docker images
- preload Ollama models
- warm Hugging Face caches
- export the final transfer bundle

### Air-Gapped Target Machine

This machine is used to:

- import Docker images
- restore named volumes
- start the full runtime stack

## Required Models

### Ollama

- `llama3.1`
- `llava:7b`

### Hugging Face / Local Runtime Cache

The backend runtime also depends on locally cached model assets for:

- Whisper / faster-whisper
- CLIP
- BLIP
- sentence-transformers embeddings

These are stored in the exported named volume:

- `hf-cache`

## Connected-Machine Preparation

From the project root:

```bash
docker compose -f docker-compose.airgap.yml up -d --build
docker compose -f docker-compose.airgap.yml exec ollama ollama pull llama3.1
docker compose -f docker-compose.airgap.yml exec ollama ollama pull llava:7b
```

Then run at least one real indexing job so the Hugging Face cache is populated.

After the cache is warm:

```bash
./scripts/export_airgap_bundle.sh --output-dir ./dist
```

## Air-Gapped Target Import

On the air-gapped target machine:

```bash
cd /path/to/thales-airgap-bundle-<timestamp>
chmod +x import_airgap_bundle.sh
./import_airgap_bundle.sh --bundle-dir . --start
```

## Runtime Verification

After import and startup:

```bash
docker compose -f docker-compose.airgap.runtime.yml ps
curl http://localhost:8010/health
curl http://localhost:8010/api/system/llm-status
```

Expected services:

- frontend on `5173`
- backend on `8010`
- ollama on `11434`
- redis on `6379`
- worker running in background

## Volumes Used

The air-gap runtime uses named Docker volumes only:

- `entity-data`
- `hf-cache`
- `ollama-models`

The runtime compose does not require a source checkout bind-mount.

## Project Scope Statement

The delivered project supports:

- Dockerized deployment
- air-gapped runtime
- no Mistral API dependency in offline mode
- local text + vision model execution
- full UI / API / worker workflow
- searchable indexed video reports

The delivered project does not currently support:

- self-hosted proprietary Mistral / Pixtral runtime
- local packaged Mistral VLM binaries

## Operational Notes

- The worker is configured for stable one-at-a-time processing to avoid queue
  saturation on heavy inference.
- Transcript-only mentions are separated from frame-confirmed detections in the
  report path.
- Search still includes transcript mentions, but the UI distinguishes them from
  frame-confirmed detections.

## Handover Statement

This project can be handed over as a Dockerized air-gap-capable deployment,
provided that:

1. the Docker images are exported from the connected staging machine
2. the Ollama model volume is preloaded
3. the Hugging Face cache volume is preloaded
4. the transfer bundle is imported on the target air-gapped machine

Under those conditions, the project runs without calling the Mistral API.

## Included Files To Share

At minimum, hand over:

- the source repository
- this document: `HANDOVER_AIRGAP.md`
- the generated air-gap bundle from `export_airgap_bundle.sh`

## Final Accuracy Note

The offline/local deployment path is operationally equivalent for the project’s
workflow, but it is not using the exact same remote Mistral/Pixtral backend.
It uses local replacements.

That should be stated explicitly during handover to avoid ambiguity.
