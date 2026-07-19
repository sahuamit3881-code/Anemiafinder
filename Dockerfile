FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# OpenCV (even the "headless" wheel) needs these system libs at import time
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only torch/torchvision first — this Space has no GPU, and
# the default PyPI wheels pull in ~2GB of CUDA libraries it will never
# use. Installing these first means the later `-r requirements.txt`
# install just sees the version constraints already satisfied and
# skips reinstalling them from the (much larger) default index.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download & bake the ImageNet-pretrained encoder weights into the
# image so the first real request doesn't stall on a cold download.
RUN python -c "import segmentation_models_pytorch as smp; smp.Unet(encoder_name='resnet34', encoder_weights='imagenet')"

# Hugging Face Spaces (Docker SDK) runs containers as a non-root user,
# and expects the app to listen on port 7860 by default.
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "app:app"]
