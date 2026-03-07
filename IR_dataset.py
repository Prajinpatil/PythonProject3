import json
import os
import shutil

# Dataset paths
thermal_dir = "images_thermal_train/data"
annotation_file = "images_thermal_train/coco.json"

# Output dataset
output_intruder = "ir_dataset/intruder"
output_non = "ir_dataset/non_intruder"

os.makedirs(output_intruder, exist_ok=True)
os.makedirs(output_non, exist_ok=True)

# Load JSON
with open(annotation_file, "r") as f:
    coco = json.load(f)

# Find the correct category ID for "person"
person_id = None
for cat in coco["categories"]:
    if cat["name"] == "person":
        person_id = cat["id"]
        break

print("Person category ID:", person_id)

# Map image_id → filename
image_map = {img["id"]: img["file_name"] for img in coco["images"]}

# Store images that contain person
intruder_images = set()
# ← IMPORTANT: define it before using
intruder_ids = {1,15,16,17,18,19,20,21,22,23,24,25,65}

for ann in coco["annotations"]:
    if ann["category_id"] in intruder_ids:
        intruder_images.add(ann["image_id"])

print("Images containing intruders:", len(intruder_images))

for img_id, filename in image_map.items():

    src = os.path.join("images_thermal_train", filename)

    if not os.path.exists(src):
        continue

    clean_name = os.path.basename(filename)

    if img_id in intruder_images:
        dst = os.path.join(output_intruder, clean_name)
    else:
        dst = os.path.join(output_non, clean_name)

    shutil.copy(src, dst)

print("Dataset preparation complete.")
