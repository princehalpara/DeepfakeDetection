from flask import Flask, request, jsonify, render_template
import torch
import torch.nn.functional as F
from torchvision import models
from PIL import Image
from preprocess import transform
import io
import cv2
import numpy as np

app = Flask(__name__)


# ---- Setup (ye sirf EK BAAR chalega, server start hote hi) ----
device = "cuda" if torch.cuda.is_available() else "cpu"

model = models.efficientnet_b0(weights=None)
model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 2)
model.load_state_dict(torch.load("model/deepfake_model_v3.pth", map_location=device))
model = model.to(device)
model.eval()

class_names = ["fake", "real"]

# Haar Cascade face detector setup (alt2 has significantly fewer false positives on non-faces)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')

print("Model loaded successfully. Server starting...")
@app.route("/")
def home():
       return render_template("index.html")

# ---- Prediction route ----
@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    try:
        image = Image.open(io.BytesIO(file.read())).convert("RGB")
    except Exception:
        return jsonify({"error": "Invalid image file"}), 400

    # ---- Face Detection Check (BEFORE model prediction) ----
    image_np = np.array(image)
    image_gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    print(f"[DEBUG] Faces detected: {len(faces)}")

    if len(faces) == 0:
        return jsonify({"error": "No face detected in this image. Please upload a photo with a visible face."}), 400

    # Dataset jaisi image banao: 256x256 + JPEG compression
    image = image.resize((256, 256), Image.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, "JPEG", quality=90)
    buf.seek(0)
    image = Image.open(buf).convert("RGB")

    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        probabilities = F.softmax(outputs, dim=1)
        confidence, predicted_class = torch.max(probabilities, 1)

    label = class_names[predicted_class.item()]
    confidence_percent = round(confidence.item() * 100, 2)

    return jsonify({
        "result": label.upper(),
        "confidence": confidence_percent
    })

# ---- Run server ----
if __name__ == "__main__":
    app.run(debug=True)