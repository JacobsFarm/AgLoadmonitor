import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
from ultralytics import YOLO

# Load model
model = YOLO("yolo26m.pt")

# Train with augmentation added
model.train(
    data="dataset.yaml", 
    imgsz=640, 
    batch=8, 
    epochs=100,
    patience=20,
    # fraction=0.05, # Currently using 100% of the dataset. (0.8 would be 80%)
    save_period=10, 
    workers=0, 
    device=0,

    # Augmentation settings
    augment=True,      # General augmentation on/off
    degrees=30,        # Rotation up to 30 degrees
    translate=0.1,     # Translation up to 10%
    scale=0.5,         # Scaling between 0.5 and 1.5
    fliplr=0.0,        # Chance of horizontal flip (set to 0.0)
    hsv_h=0.015,       # Small hue variations
    hsv_s=0.7,         # Saturation variations
    hsv_v=0.4,         # Brightness variations
    # mosaic=1.0       # Mosaic augmentation (combines 4 images)
)
