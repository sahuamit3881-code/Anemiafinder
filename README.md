---
title: Multimodal Anemia Screening Portal
emoji: 🩸
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# Multimodal Anemia Screening Portal

A non-invasive, multimodal AI anemia screening prototype built for a 48-hour hackathon.
Estimates anemia risk from photos of the lower eyelid, fingernail beds, and tongue.

**This is an educational hackathon prototype — not a diagnostic medical device.**

## How the screening works

Each uploaded photo goes through:

1. **Segmentation** — a U-Net with a ResNet-34 encoder (`ml/segmentation.py`)
   isolates the relevant tissue (conjunctiva / nail bed / tongue surface).
   Until you drop a trained checkpoint into `weights/`, that region falls
   back to a classical color-threshold mask automatically, so the app
   keeps working while training is in progress.
2. **Redness measurement** — the mean LAB `a*` value inside the mask
   (`ml/redness.py`), a perceptual red/green axis measure.
3. **Fusion** — each region's redness maps to a 0-100 risk score via a
   calibrated linear formula, then the available regions are averaged
   into one final score (`ml/pipeline.py`, formula documented in its
   docstring). Calibration bounds are placeholders — tune them with your
   own reference photos.

See `weights/README.md` for the checkpoint naming convention.

## Local development

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:7860`.

## Docker

```bash
docker build -t anemia-screening-web .
docker run -p 7860:7860 anemia-screening-web
```

## Deploying to Hugging Face Spaces

1. Create a new Space and choose the **Docker** SDK.
2. Push this folder's contents to the Space's repo (this `README.md`'s
   front matter is what tells the Space to use Docker on port 7860).
3. The Space will build the `Dockerfile` and serve the app automatically.
