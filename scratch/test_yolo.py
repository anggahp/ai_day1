from ultralytics import YOLO
import sys

model = YOLO("src/pelatihanindoprima/tools/model-yolo.pt")
image_path = "/home/anggahp/.gemini/antigravity/brain/ea122f37-8270-4de8-83b1-9fae5ad18f5e/test_helmet_detection_1778043508477.png"
results = model(image_path)

detected_objects = results[0].boxes.cls.tolist()
class_names = results[0].names

print(f"Detected objects: {detected_objects}")
print(f"Class names: {class_names}")

for obj in detected_objects:
    print(f"Found: {class_names[int(obj)]}")
