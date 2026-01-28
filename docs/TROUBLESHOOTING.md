# Troubleshooting

## URL Upload fails with 403
- Use cookies file (`cookies.txt`) in the Upload UI
- Or set `ENTITY_INDEXING_YTDLP_COOKIES_FROM_BROWSER=chrome` for local runs

## Frames not showing
- Ensure the Celery worker is running
- If using Docker: `docker-compose ps` should show worker running

## Transcript missing or empty
- Some videos have no speech (music/noise only)
- Check transcript section → audio analysis

## webrtcvad fails to install (local)
- Install build tools:
  - macOS: `xcode-select --install`
  - Linux: `sudo apt-get install build-essential python3-dev`

## Docker build fails on webrtcvad
- Use the provided `backend/Dockerfile` (includes build tools)

## UI loads but backend errors
- Confirm backend is up: `http://localhost:8010/health`
- Verify frontend env: `VITE_API_BASE=http://localhost:8010`

## Share link not loading
- Ensure the video report exists
- Share token stored in DB (`share_links` table)

