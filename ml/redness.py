"""
Redness measurement — quantifies how "red/pink" the segmented tissue is,
as a visual proxy for local blood perfusion / hemoglobin level.
"""

import cv2
import numpy as np


def compute_redness_index(pil_image, mask: np.ndarray) -> float:
    """
    Mean LAB a* value over the masked region.

    The a* channel of LAB color space sits on a green(-)/red(+) axis,
    which is a more perceptually grounded redness measure than raw
    R-minus-G subtraction on RGB. In OpenCV's 8-bit LAB encoding, a* is
    stored on a 0-255 scale (~128 is neutral); higher values mean more
    red/magenta, lower values mean more green/pale.
    """
    img = np.array(pil_image.convert("RGB"))
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    a_channel = lab[:, :, 1].astype(np.float32)

    if mask.shape != a_channel.shape[:2]:
        mask = cv2.resize(
            mask, (a_channel.shape[1], a_channel.shape[0]), interpolation=cv2.INTER_NEAREST
        )

    masked_pixels = a_channel[mask.astype(bool)]
    if masked_pixels.size == 0:
        # Segmentation found nothing — fall back to the whole image so
        # the request still returns a number instead of failing.
        masked_pixels = a_channel.flatten()

    return float(masked_pixels.mean())
