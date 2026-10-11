import requests
import os
import time
from PIL import Image
from io import BytesIO

SAVE_DIR = "dataset_finetune/train/fake"
NUM_IMAGES = 300

os.makedirs(SAVE_DIR, exist_ok=True)

url = "https://thispersondoesnotexist.com/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

saved = 0
attempts = 0

while saved < NUM_IMAGES and attempts < NUM_IMAGES * 2:
    attempts += 1
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Pehle verify karo ye asli image hai ya nahi
            img = Image.open(BytesIO(response.content))
            img.verify()

            filename = os.path.join(SAVE_DIR, f"tpdne_{saved+1}.jpg")
            with open(filename, "wb") as f:
                f.write(response.content)
            saved += 1
            print(f"[{saved}/{NUM_IMAGES}] Saved: {filename}")
        else:
            print(f"Attempt {attempts}: Failed — status {response.status_code}")
    except Exception as e:
        print(f"Attempt {attempts}: Skipped (invalid image) — {e}")

    time.sleep(3)

print(f"\nDone! Total saved: {saved}")