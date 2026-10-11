from torchvision import datasets
from torch.utils.data import DataLoader
from preprocess import transform

# Dataset paths
train_dir = "dataset/train"
valid_dir = "dataset/valid"
test_dir = "dataset/test"

# ImageFolder automatically reads subfolder names (real/fake) as labels
train_dataset = datasets.ImageFolder(root=train_dir, transform=transform)
valid_dataset = datasets.ImageFolder(root=valid_dir, transform=transform)
test_dataset = datasets.ImageFolder(root=test_dir, transform=transform)

# DataLoaders — batch_size=16 and low num_workers to stay safe on 8GB RAM
train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, num_workers=0)
valid_loader = DataLoader(valid_dataset, batch_size=8, shuffle=False, num_workers=0)
test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False, num_workers=0)

# Sanity check — run this file directly to confirm everything loads correctly
if __name__ == "__main__":
    print("Classes found:", train_dataset.classes)
    print("Class to index mapping:", train_dataset.class_to_idx)
    print("Train images:", len(train_dataset))
    print("Valid images:", len(valid_dataset))
    print("Test images:", len(test_dataset))

    # Check one batch
    images, labels = next(iter(train_loader))
    print("One batch shape:", images.shape)
    print("One batch labels:", labels)