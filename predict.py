import torch
import torch.nn.functional as F
from torchvision import models
from PIL import Image
from preprocess import transform

# ---- Setup ----
device = "cuda" if torch.cuda.is_available() else "cpu"

# ---- Load model architecture (same structure as training) ----
model = models.efficientnet_b0(weights=None)  # weights=None, kyunki humara apna trained model load karenge
model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 2)
model.load_state_dict(torch.load("model/deepfake_model_v3.pth", map_location=device))
model = model.to(device)
model.eval()  # evaluation mode — training nahi, sirf prediction

# ---- Class mapping (jo humne dataset.py se confirm kiya tha) ----
class_names = ["fake", "real"]  # index 0 = fake, index 1 = real

def predict_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)  # batch dimension add karo

    with torch.no_grad():
        outputs = model(image)
        probabilities = F.softmax(outputs, dim=1)
        confidence, predicted_class = torch.max(probabilities, 1)

    label = class_names[predicted_class.item()]
    confidence_percent = confidence.item() * 100

    print(f"Prediction: {label.upper()}")
    print(f"Confidence: {confidence_percent:.2f}%")

# ---- Test karo ----
if __name__ == "__main__":
    test_image_path = r"C:\Users\PRINCE\Desktop\Deepfake_project--runtime\dataset_finetune\valid\real\33296.jpg" # apna koi image path daalo
    predict_image(test_image_path)