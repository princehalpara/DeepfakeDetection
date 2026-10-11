import os
from PIL import Image

FOLDERS_TO_CHECK = [
    "dataset_finetune/train/fake",
    "dataset_finetune/train/real",
    "dataset_finetune/valid/fake",
    "dataset_finetune/valid/real",
]

removed_count = 0

for folder in FOLDERS_TO_CHECK:
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        try:
            img = Image.open(filepath)
            img.verify()  # check karo image valid hai ya nahi
        except Exception:
            print(f"Corrupt/invalid file removed: {filepath}")
            os.remove(filepath)
            removed_count += 1

print(f"\nTotal removed: {removed_count}")
print("Cleaning complete!")