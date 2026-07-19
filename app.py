"""
Multimodal Anemia Screening Portal — Flask backend
------------------------------------------------------------------
Serves the HTML/CSS/JS frontend and exposes a small JSON API that
fuses uploaded eyelid / nail / tongue photos into an estimated
anemia risk score.

Local run:
    pip install -r requirements.txt
    python app.py            # dev server on http://localhost:7860

Docker / Hugging Face Spaces run gunicorn instead (see Dockerfile).
------------------------------------------------------------------
"""

from flask import Flask, jsonify, render_template, request
from PIL import Image

from ml.pipeline import analyze_physiological_markers

app = Flask(__name__)

REGION_KEYS = ["eyelid", "nail", "tongue"]

# analyze_physiological_markers now runs three U-Net-ResNet34 segmentation
# models (one per region) + a LAB-redness fusion formula — see ml/pipeline.py
# for the math and ml/segmentation.py for the models and encoder note.


# ============================================================
# ROUTES
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    images = {}
    for key in REGION_KEYS:
        file = request.files.get(key)
        if file and file.filename:
            try:
                images[key] = Image.open(file.stream)
            except Exception:
                images[key] = None
        else:
            images[key] = None

    result = analyze_physiological_markers(images)
    if result is None:
        return (
            jsonify(
                {
                    "error": "no_images",
                    "message": "Please upload at least one image (eyelid, nail, or tongue) before running the screening.",
                }
            ),
            400,
        )

    return jsonify(result)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Local dev server. In Docker/HF Spaces, gunicorn serves the app instead.
    app.run(host="0.0.0.0", port=7860, debug=False)
