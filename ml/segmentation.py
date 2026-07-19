"""
Region segmentation — one U-Net (ResNet encoder) per anatomical site:
lower eyelid, fingernail bed, and tongue.

A NOTE ON THE ENCODER
----------------------
"ResNet-32" isn't one of the standard ImageNet backbone depths (the
standard family is 18 / 34 / 50 / 101 / 152), so there's no off-the-shelf
"resnet32" with pretrained ImageNet weights the way there is for those.
This module defaults to ResNet-34 — the closest standard depth, with
pretrained weights available through segmentation_models_pytorch. If you
specifically have a custom ResNet-32 (e.g. the CIFAR-style 3n+2-layer
variant from the original ResNet paper) you trained yourself, swap
ENCODER_NAME below and plug your architecture into build_model(); every
other part of this pipeline (mask -> redness -> fusion) is agnostic to
the exact encoder used.

TRAINING STATUS
----------------
Until a trained checkpoint exists for a region (see CHECKPOINT_PATHS),
RegionSegmenter falls back to a classical HSV color-threshold + largest-
contour mask for that region, so the rest of the app keeps working
end-to-end while the real models are being trained. Drop a fine-tuned
state_dict at the matching path in weights/ and it will be picked up
automatically on next start — no code changes needed.
"""

import os
import warnings

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch

ENCODER_NAME = "resnet34"
ENCODER_WEIGHTS = "imagenet"  # pretrained backbone; decoder is random until fine-tuned
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
INPUT_SIZE = 256  # network input resolution

WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "weights")
CHECKPOINT_PATHS = {
    "eyelid": os.path.join(WEIGHTS_DIR, "eyelid_unet_resnet34.pth"),
    "nail": os.path.join(WEIGHTS_DIR, "nail_unet_resnet34.pth"),
    "tongue": os.path.join(WEIGHTS_DIR, "tongue_unet_resnet34.pth"),
}


def build_model() -> smp.Unet:
    """Fresh U-Net with a ResNet-34 encoder and a single-channel mask head."""
    return smp.Unet(
        encoder_name=ENCODER_NAME,
        encoder_weights=ENCODER_WEIGHTS,
        in_channels=3,
        classes=1,
        activation=None,  # raw logits; sigmoid is applied at inference time
    )


class RegionSegmenter:
    """Wraps one U-Net-ResNet34 model for a single anatomical region."""

    def __init__(self, region: str):
        self.region = region
        self.model = build_model().to(DEVICE).eval()
        self.preprocess = smp.encoders.get_preprocessing_fn(ENCODER_NAME, ENCODER_WEIGHTS)
        self.trained = self._try_load_checkpoint()

    def _try_load_checkpoint(self) -> bool:
        path = CHECKPOINT_PATHS.get(self.region)
        if path and os.path.exists(path):
            state_dict = torch.load(path, map_location=DEVICE)
            self.model.load_state_dict(state_dict)
            return True
        warnings.warn(
            f"No trained checkpoint for '{self.region}' at {path} — "
            f"using a classical color-threshold fallback mask for now."
        )
        return False

    @torch.no_grad()
    def predict_mask(self, pil_image) -> np.ndarray:
        """Binary mask (H, W) uint8 {0,1}, same size as the input image."""
        if self.trained:
            return self._predict_with_model(pil_image)
        return heuristic_mask(pil_image, self.region)

    def _predict_with_model(self, pil_image) -> np.ndarray:
        orig_w, orig_h = pil_image.size
        img = np.array(pil_image.convert("RGB").resize((INPUT_SIZE, INPUT_SIZE)))
        img = self.preprocess(img).astype(np.float32)
        tensor = torch.from_numpy(img.transpose(2, 0, 1)).unsqueeze(0).to(DEVICE)

        logits = self.model(tensor)
        prob = torch.sigmoid(logits)[0, 0].cpu().numpy()
        mask = (prob > 0.5).astype(np.uint8)
        mask = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        return mask


def heuristic_mask(pil_image, region: str) -> np.ndarray:
    """
    Classical HSV color-threshold + largest-contour fallback mask, used
    only until a trained U-Net checkpoint exists for this region. This is
    a stand-in for the real segmentation model, not a substitute for it.
    """
    img = np.array(pil_image.convert("RGB"))
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    if region == "nail":
        lower, upper = np.array([0, 10, 120]), np.array([50, 120, 255])
    elif region == "tongue":
        lower, upper = np.array([0, 40, 60]), np.array([25, 255, 255])
    else:  # eyelid / conjunctiva
        lower, upper = np.array([0, 30, 60]), np.array([20, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        clean = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(clean, [largest], -1, 1, thickness=cv2.FILLED)
        return clean

    # Nothing detected by color thresholding — fall back to a centered
    # box so redness still gets measured from something representative
    # of the photo rather than failing outright.
    fallback = np.zeros((h, w), dtype=np.uint8)
    cy0, cy1 = int(h * 0.3), int(h * 0.7)
    cx0, cx1 = int(w * 0.3), int(w * 0.7)
    fallback[cy0:cy1, cx0:cx1] = 1
    return fallback


_SEGMENTER_CACHE: dict = {}


def get_segmenter(region: str) -> RegionSegmenter:
    """Lazily builds and caches one segmenter per region (module singleton)."""
    if region not in _SEGMENTER_CACHE:
        _SEGMENTER_CACHE[region] = RegionSegmenter(region)
    return _SEGMENTER_CACHE[region]
