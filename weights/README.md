# Trained segmentation checkpoints go here

`ml/segmentation.py` looks for these exact filenames at startup. If a file
is missing, that region automatically falls back to a classical
color-threshold mask instead of failing.

```
weights/
├── eyelid_unet_resnet34.pth
├── nail_unet_resnet34.pth
└── tongue_unet_resnet34.pth
```

Each file should be a PyTorch `state_dict()` for a
`smp.Unet(encoder_name="resnet34", encoder_weights="imagenet", in_channels=3, classes=1)`
saved with:

```python
torch.save(model.state_dict(), "weights/eyelid_unet_resnet34.pth")
```

No other code changes are needed — `RegionSegmenter` picks up a checkpoint
automatically the next time the app starts.
