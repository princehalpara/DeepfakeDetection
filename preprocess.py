from torchvision import transforms



transform = transforms.Compose([
    transforms.Resize((224, 224)),     
    transforms.ToTensor(),               # Image to PyTorch tensor me convert  (0-1 range)
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],      # ImageNet  standard mean values
        std=[0.229, 0.224, 0.225]        # ImageNet standard std values
    )
])