# dataset_finetune.py
from torchvision import datasets
from torch.utils.data import DataLoader
from preprocess_finetune import train_transform_finetune, valid_transform_finetune

train_dir = "dataset_finetune/train"
valid_dir = "dataset_finetune/valid"

train_dataset_ft = datasets.ImageFolder(root=train_dir, transform=train_transform_finetune)
valid_dataset_ft = datasets.ImageFolder(root=valid_dir, transform=valid_transform_finetune)

train_loader_ft = DataLoader(train_dataset_ft, batch_size=8, shuffle=True, num_workers=0)
valid_loader_ft = DataLoader(valid_dataset_ft, batch_size=8, shuffle=False, num_workers=0)

if __name__ == "__main__":
    print("Classes:", train_dataset_ft.classes)
    print("Train images:", len(train_dataset_ft))
    print("Valid images:", len(valid_dataset_ft))