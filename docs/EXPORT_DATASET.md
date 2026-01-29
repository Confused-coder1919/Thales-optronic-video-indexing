# Dataset Exporter

This exporter turns existing pipeline outputs (frames + detections) into training‑ready datasets:

- **COCO** format (`instances_train.json`, `instances_val.json`, `instances_test.json`)
- **YOLO** format (`labels/{split}/*.txt`)
- **Train/val/test** split by **video** (prevents leakage)
- **Taxonomy files** (`labels.txt`, `labels.json`)
- **Manifest** (`dataset_manifest.json`) for lineage + params

---

## How it works

It reads detections from:
- `frames.json` if available (default)
- or falls back to DB adapter (future‑proof, currently uses frames.json)

---

## Usage

You can export from the UI via **Video Library → Export Dataset**.

```bash
python3 scripts/export_training_dataset.py \
  --output data/entity_indexing/datasets/run_001 \
  --train 0.7 --val 0.2 --test 0.1 \
  --min-confidence 0.3 \
  --sources yolo,clip
```

Optional:
- `--videos video_id1,video_id2` to export only specific videos
- `--adapter json|db|auto` (default: auto)
- `--annotated` to use annotated frames if available

---

## Output Layout

```
<output>/
├── images/
│   ├── train/*.jpg
│   ├── val/*.jpg
│   └── test/*.jpg
├── labels/
│   ├── train/*.txt
│   ├── val/*.txt
│   └── test/*.txt
├── annotations/
│   ├── instances_train.json
│   ├── instances_val.json
│   └── instances_test.json
├── labels.txt
├── labels.json
└── dataset_manifest.json
```

---

## Notes

- Only detections with **bounding boxes** are exported
- OCR/discovery detections without bounding boxes are ignored
- Bboxes are clipped to image bounds
