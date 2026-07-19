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
# Anemiafinder
# Anemiafinder
