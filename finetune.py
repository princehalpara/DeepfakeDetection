# finetune.py
import torch
import torch.nn as nn
from torchvision import models
from dataset_finetune import train_loader_ft, valid_loader_ft

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Using device:", device)

    # ---- Purana trained model load karo (scratch se nahi) ----
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model.load_state_dict(torch.load("model/deepfake_model_v2.pth", map_location=device))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    # Chhoti learning rate — kyunki fine-tuning hai, poori training nahi
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)
    scaler = torch.amp.GradScaler("cuda")

    num_epochs = 3  # kam epochs, kyunki model already bahut kuch seekh chuka hai

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader_ft:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()

            with torch.amp.autocast("cuda"):
                outputs = model(images)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        train_acc = 100 * correct / total
        avg_loss = running_loss / len(train_loader_ft)

        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in valid_loader_ft:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()

        val_acc = 100 * val_correct / val_total

        print(f"Epoch [{epoch+1}/{num_epochs}] "
              f"Loss: {avg_loss:.4f} Train Acc: {train_acc:.2f}% Val Acc: {val_acc:.2f}%")

    # ---- Naya improved model ALAG naam se save karo (purana overwrite mat karo) ----
    torch.save(model.state_dict(), "model/deepfake_model_v3.pth")
    print("Fine-tuned model saved to model/deepfake_model_v3.pth")

if __name__ == "__main__":
    main()