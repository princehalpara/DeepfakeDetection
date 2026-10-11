import torch
import torch.nn as nn
from torchvision import models
from dataset import train_loader, valid_loader

def main():
    # ---- Setup ----
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Using device:", device)

  

    # ---- Model ----
    model = models.efficientnet_b0(weights="IMAGENET1K_V1")
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model = model.to(device)

    # ---- Loss and Optimizer ----
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

    # ---- Mixed precision ----
    scaler = torch.amp.GradScaler("cuda")

    # ---- Training settings ----
    num_epochs = 5  # test ke liye

    # ---- Training loop ----
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
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
        avg_loss = running_loss / len(train_loader)

        # ---- Validation ----
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in valid_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()

        val_acc = 100 * val_correct / val_total

        print(f"Epoch [{epoch+1}/{num_epochs}] "
              f"Loss: {avg_loss:.4f} "
              f"Train Acc: {train_acc:.2f}% "
              f"Val Acc: {val_acc:.2f}%")

    # ---- Save model ----
    torch.save(model.state_dict(), "model/deepfake_model.pth")
    print("Model saved to model/deepfake_model.pth")


if __name__ == "__main__":
    main()