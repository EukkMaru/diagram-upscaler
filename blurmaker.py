# just realized blur != compressed

import os
import shutil
import random
import csv
from pathlib import Path
from PIL import Image, ImageFilter

input_dir = "images"
output_original_dir = "originals"
output_bbox_dir = "bboxes"
output_blur_dir = "blurred"
blur_log_path = "blur_log.csv"

os.makedirs(output_original_dir, exist_ok=True)
os.makedirs(output_bbox_dir, exist_ok=True)
os.makedirs(output_blur_dir, exist_ok=True)

blur_log = []

for file_name in os.listdir(input_dir):
    ext = file_name.lower().split(".")[-1]
    name_stem = Path(file_name).stem
    input_path = os.path.join(input_dir, file_name)

    if ext in ("png"): #, "jpg", "jpeg"
        shutil.copy(input_path, os.path.join(output_original_dir, file_name))
        image = Image.open(input_path)
        blur_radius = round(random.uniform(1.5, 3.0), 4)
        blurred = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        blurred.save(os.path.join(output_blur_dir, file_name))
        blur_log.append({"filename": file_name, "blur_radius": blur_radius})

    elif ext == "json":
        shutil.copy(input_path, os.path.join(output_bbox_dir, file_name))

with open(blur_log_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["filename", "blur_radius"])
    writer.writeheader()
    writer.writerows(blur_log)

print(f"Processed {len(blur_log)} images.")