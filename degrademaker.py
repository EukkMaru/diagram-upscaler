import os
import shutil
import random
import csv
import io
from pathlib import Path
from PIL import Image

input_dir = "images"
output_original_dir = "original"
output_bbox_dir = "bboxes"
output_degraded_dir = "degraded"
degrade_log_path = "degrade_log.csv"

os.makedirs(output_original_dir, exist_ok=True)
os.makedirs(output_bbox_dir, exist_ok=True)
os.makedirs(output_degraded_dir, exist_ok=True)

degrade_log = []

for file_name in os.listdir(input_dir):
    ext = file_name.lower().split(".")[-1]
    name_stem = Path(file_name).stem
    input_path = os.path.join(input_dir, file_name)

    if ext == "png":
        shutil.copy(input_path, os.path.join(output_original_dir, file_name))

        degrade_rounds = random.randint(1, 3)
        degrade_quality = random.randint(20, 30)

        image = Image.open(input_path).convert("RGB")

        for _ in range(degrade_rounds):
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=degrade_quality)
            buffer.seek(0)
            image = Image.open(buffer)

            w, h = image.size
            image = image.resize((w // 2, h // 2), Image.NEAREST)
            image = image.resize((w, h), Image.NEAREST)

        output_path = os.path.join(output_degraded_dir, file_name)
        image.save(output_path, format="PNG")

        degrade_log.append({
            "filename": file_name,
            "rounds": degrade_rounds,
            "jpeg_quality": degrade_quality
        })

    elif ext == "json":
        shutil.copy(input_path, os.path.join(output_bbox_dir, file_name))

with open(degrade_log_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["filename", "rounds", "jpeg_quality"])
    writer.writeheader()
    writer.writerows(degrade_log)

print(f"Processed {len(degrade_log)} images.")