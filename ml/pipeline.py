"""
Fuses per-region segmentation + redness measurement into a single
estimated anemia risk score.

THE FORMULA
-----------
For each region i (eyelid, nail, tongue) with an uploaded image:

    mask_i  = UNet-ResNet34(image_i)                  # segmentation.py
    A_i     = mean LAB a* value inside mask_i          # redness.py

    Risk_i (%) = clip( (A_max_i - A_i) / (A_max_i - A_min_i) * 100, 0, 100 )

[A_min_i, A_max_i] is the expected a* range for that tissue type — a
higher a* means redder/healthier, so it maps to lower risk. THESE
BOUNDS ARE PLACEHOLDERS: calibrate them against your own reference
photos (known-healthy vs. known-anemic samples, or a color-card shot
alongside each photo) before treating the output as meaningful.

The final score is a weighted average over whichever regions were
actually provided:

    RiskScore = Σ(w_i * Risk_i) / Σ(w_i)     for i in available regions

Weights default to equal (1/3 each) — change WEIGHTS below if you
decide one site should count more than another.
"""

from . import redness, segmentation

# --- Calibration placeholders: TUNE THESE with real reference photos ---
REDNESS_CALIBRATION = {
    "eyelid": {"a_min": 128.0, "a_max": 165.0},
    "nail": {"a_min": 126.0, "a_max": 155.0},
    "tongue": {"a_min": 130.0, "a_max": 170.0},
}

# --- Fusion weights: how much each region counts toward the final score ---
WEIGHTS = {"eyelid": 1.0, "nail": 1.0, "tongue": 1.0}


def _risk_from_redness(region: str, a_value: float) -> float:
    bounds = REDNESS_CALIBRATION[region]
    a_min, a_max = bounds["a_min"], bounds["a_max"]
    normalized = (a_max - a_value) / (a_max - a_min)
    return float(max(0.0, min(100.0, normalized * 100.0)))


def analyze_physiological_markers(images_dict: dict) -> dict | None:
    """
    Drop-in replacement for the earlier placeholder of the same name —
    same input/output contract, now backed by real per-region U-Net
    segmentation + LAB redness measurement instead of a whole-image
    heuristic.

    images_dict = {"eyelid": PIL.Image|None, "nail": PIL.Image|None, "tongue": PIL.Image|None}

    Returns None if no images were provided, otherwise:
        {
            "risk_score": float,
            "confidence": float,
            "modality_scores": {region: float, ...}
        }
    """
    modality_scores = {}

    for region, image in images_dict.items():
        if image is None:
            continue
        segmenter = segmentation.get_segmenter(region)
        mask = segmenter.predict_mask(image)
        a_value = redness.compute_redness_index(image, mask)
        modality_scores[region] = round(_risk_from_redness(region, a_value), 1)

    if not modality_scores:
        return None

    weighted_sum = sum(modality_scores[r] * WEIGHTS.get(r, 1.0) for r in modality_scores)
    weight_total = sum(WEIGHTS.get(r, 1.0) for r in modality_scores)
    risk_score = round(weighted_sum / weight_total, 1)
    confidence = round((len(modality_scores) / 3) * 100, 1)

    return {
        "risk_score": risk_score,
        "confidence": confidence,
        "modality_scores": modality_scores,
    }
