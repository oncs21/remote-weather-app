import torch
from torchvision import models
import torch.nn as nn

class ResNet18_CustomHead(nn.Module):
    def __init__(self, 
                 num_classes: int, 
                 pretrained: bool = True,
                 freeze_backbone: bool = True
                 ) -> None:
        
        super().__init__()
        
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        backbone = models.resnet18(weights=weights)

        in_features = backbone.fc.in_features
        self.backbone = nn.Sequential(*list(backbone.children())[:-1])

        if freeze_backbone:
            self.freeze_backbone()

        self.head = nn.Sequential(
            nn.Flatten(1),
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def freeze_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = False

    def unfreeze_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = True

    def forward(self, x):
        x = self.backbone(x)
        return self.head(x)