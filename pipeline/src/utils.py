import torch
import torchmetrics
import os

from pathlib import Path
from PIL import Image
from torchvision import transforms as T
from torchvision.models import ResNet18_Weights
from django.conf import settings

def load_images_from_path(root: Path = Path(settings.BASE_DIR) / "pipeline" / "temp_data"
                          ) -> list[Image.Image]:
    
    loaded_images = []

    for filename in os.listdir(root):
        image_path = os.path.join(root, filename)
        img = Image.open(image_path)
        loaded_images.append(img)

    return loaded_images


def get_default_test_transforms(weights = ResNet18_Weights.DEFAULT):
    
    return T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(
            mean=weights.transforms().mean,
            std=weights.transforms().std
        ),
    ])