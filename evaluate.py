# evaluate.py
import torch
from torchvision import models
from sklearn.metrics import confusion_matrix, classification_report
from dataset import test_loader, test_dataset

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Using device:", device)

    # ---- Final model (v3) load karo ----
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 2)
    model.load_state_dict(torch.load("model/deepfake_model_v3.pth", map_location=device))
    model = model.to(device)
    model.eval()

    class_names = test_dataset.classes  # ['fake', 'real']
    all_labels = []
    all_preds = []

    # ---- Test set par prediction ----
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            all_labels.extend(labels.tolist())
            all_preds.extend(predicted.cpu().tolist())

    # ---- Accuracy ----
    correct = sum(p == l for p, l in zip(all_preds, all_labels))
    total = len(all_labels)
    print(f"\nTest Images: {total}")
    print(f"Test Accuracy: {100 * correct / total:.2f}%")

    # ---- Confusion Matrix ----
    cm = confusion_matrix(all_labels, all_preds)
    print("\nConfusion Matrix (rows = Actual, columns = Predicted):")
    print(f"{'':>14}{'Pred ' + class_names[0]:>12}{'Pred ' + class_names[1]:>12}")
    for i, name in enumerate(class_names):
        print(f"{'Actual ' + name:>14}{cm[i][0]:>12}{cm[i][1]:>12}")

    # ---- Precision, Recall, F1 ----
    print("\nClassification Report:")
    print(classification_report(all_labels, all_preds, target_names=class_names, digits=4))

if __name__ == "__main__":
    main()