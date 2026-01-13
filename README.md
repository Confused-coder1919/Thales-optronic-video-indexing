# Thales Optronic Video Indexing Pipeline

This project implements an end-to-end pipeline to generate **time-aligned metadata** from optronic videos, combining:
- **Speech-to-Text (STT)** analysis of audio commentary
- **Image-to-Text (ITT / Vision)** analysis of video frames
- **Fusion** of speech and vision events along a common timeline

The goal is to prepare clean, structured data suitable for **AI model training, indexing, and dataset enrichment**, as required in the Thales context.

## Data folder

Place your input videos in the `data/` directory (e.g., `data/video_1.mp4`).

> Note: `data/` contents are intentionally ignored by Git to avoid committing large files.

---

## 1. Prerequisites

### Operating System
- macOS (Intel or Apple Silicon)
- Linux should also work (not tested here)

### System Dependencies

#### FFmpeg (mandatory)
FFmpeg is required to extract audio from videos and for Whisper-based STT.

Install with Homebrew:
```bash
brew install ffmpeg
```

Verify installation:
```bash
ffmpeg -version
```

---

## 2. Python Environment Setup

### Python version
- **Python 3.11 is REQUIRED**
- Python 3.13 is **not compatible** with PyTorch

Check your version:
```bash
python --version
```

### Create and activate a virtual environment

From the project root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Upgrade pip:
```bash
pip install --upgrade pip
```

### Install Python dependencies
```bash
pip install -r requirements.txt
```

---

## 3. Environment Variables (.env)

This project uses the **Mistral API** (Pixtral vision model).  
You must provide your own API key.

### Create a `.env` file at the project root:
```env
MISTRAL_API_KEY=your_mistral_api_key_here
```

This file is ignored by Git (via `.gitignore`) and must **not** be committed.

### Optional (recommended for macOS Intel)
To avoid OpenMP crashes:
```env
KMP_DUPLICATE_LIB_OK=TRUE
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

---

## 4. Project Structure (Simplified)

```text
data/
  video_1.mp4               # Input video(s)

backend/
  data/input/               # Extracted audio for STT
  data/output/              # STT outputs (segments.csv, sitrep.json)
  config/settings.yaml      # STT config
  src/                      # STT core + FastAPI entrypoint

reports/
  video_1_report.json       # Vision report
  summary_report.json       # Global summary
  thales_metadata.csv       # Thales CSV export (optional)
  pivot/
    video_1_speech.jsonl    # Speech events
    video_1_vision.jsonl    # Vision events
    video_1_merged.jsonl    # Fused timeline

thales/
  cli.py                    # Main pipeline entrypoint
  entity_detector.py        # Vision pipeline
  entity_extractor.py       # LLM entity extraction
  pivot.py                  # Pivot + normalization
  fusion.py                 # Speech/Vision fusion logic
  export_thales_csv.py      # CSV export helper

ui/
  app.py                    # Streamlit UI entrypoint
  utils.py                  # UI helpers
  requirements-ui.txt       # UI deps
```

---

## 5. Running the Pipeline

### Input requirement
Videos must be named:
```text
video_<number>.<ext>
```
Supported extensions: `.mp4`, `.mkv`, `.avi`, `.mov`

Example:
```text
data/video_1.mp4
```

### Run the full pipeline
From the project root:
```bash
python -m thales -d data -i 5 -o reports
```

Optional (CSV export):
```bash
python -m thales -d data -i 5 -o reports --export-csv
```

Arguments:
- `-d data` → input directory containing videos
- `-i 5` → frame sampling interval (seconds)
- `-o reports` → output directory

---

## 6. Outputs

### Speech (STT)
- Audio extracted automatically
- Whisper produces timestamped segments
- Speech pivot is split into sentence-level events with:
  - `t_start`, `t_end`, `t`
  - `event = "mention"`

### Vision (ITT)
- Frames extracted every N seconds
- Pixtral detects entities
- Vision pivot produces:
  - `appear` / `disappear` events
  - timestamped `t`

### Fusion
Speech and vision are fused into a single timeline:
```json
{
  "t": 5.0,
  "source": "vision",
  "event": "appear",
  "targets": ["military truck"],
  "speech_context": {
    "t_start": 0.0,
    "t_end": 20.5,
    "text": "Man walks on tank."
  }
}
```

This fused file is the **basis for metadata CSV generation**.

---

## 7. UI (Streamlit)

Run the pipeline with a lightweight web UI.

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -r ui/requirements-ui.txt

export MISTRAL_API_KEY=your_mistral_api_key_here  # or set it in .env
streamlit run ui/app.py
```

Notes:
- The UI expects `voice_*.txt` + `video_*.mp4` pairs in `data/`, or uploads.
- Turn on Demo mode in the UI to skip external API calls.
- Discovery mode (vision-first proposals) is optional. Enable in the UI or set `THALES_DISCOVERY_MODE=1`
  to add per-entity `source` and `discovered_only` fields in reports.

---

## 8. Next Steps (Not Implemented Yet)

- Time-range consolidation (appear → disappear → presence interval)
- Metadata CSV export (Thales format)
- Multi-video batch processing
- Optional language normalization and entity filtering

---

## 9. Notes

- STT always outputs **English**, regardless of audio language
- Fusion logic is deterministic and explainable
- Pipeline is modular and easily extensible

---

## 10. Contact / Context

Project developed in the context of:
> **Génération de métadonnées pour l’indexation de vidéos optroniques destinées à l’entraînement de modèles IA**  
> Thales LAS / OME
