import torchmetrics
import torch
import torch.nn as nn


from preprocess import CloudCoverDataset, get_dataloaders
from torchvision import transforms as T
from torchvision.models import ResNet18_Weights
from config import Paths
from pathlib import Path


def train_model(model: nn.Module,
                loss_fn,
                optim,
                lr: float,
                train_dl,
                val_dl,
                num_classes: int,
                epochs: int = 20,
                device: str = "cuda",
                ) -> dict[str, list[float]]:
    
    train_f1 = torchmetrics.F1Score(
        task="multiclass",
        num_classes=num_classes,
        average="macro"
    ).to(device)

    val_f1 = torchmetrics.F1Score(
        task="multiclass",
        num_classes=num_classes,
        average="macro"
    ).to(device)


    history = {
        "train_loss": [],
        "train_acc": [],
        "train_f1": [],
        "val_loss": [],
        "val_acc": [],
        "val_f1": []
    }

    if optim is None:
        optim = torch.optim.Adam(params=model.parameters(), lr=lr)
    
    if loss_fn is None:
        loss_fn = nn.CrossEntropyLoss(label_smoothing=0.1)

    for epoch in range(epochs):
        model.train()

        train_loss = 0.0
        train_correct = 0
        train_samples = 0
        train_f1.reset()

        for images, labels in train_dl:
            images = images.to(device)
            labels = labels.to(device)

            preds = model(images)
            loss = loss_fn(preds, labels)

            optim.zero_grad()
            loss.backward()
            optim.step()

            train_loss += loss.item() * labels.size(0)
            train_correct += (preds.argmax(dim=1) == labels).sum().item()
            train_samples += labels.size(0)
            train_f1.update(preds, labels)

        train_loss /= train_samples
        train_acc = train_correct / train_samples
        train_f1_score = train_f1.compute().item()

        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_samples = 0
        val_f1.reset()

        with torch.inference_mode():
            for images, labels in val_dl:
                images = images.to(device)
                labels = labels.to(device)

                preds = model(images)
                loss = loss_fn(preds, labels)

                val_loss += loss.item() * labels.size(0)
                val_correct += (preds.argmax(dim=1) == labels).sum().item()
                val_samples += labels.size(0)
                val_f1.update(preds, labels)

            val_loss /= val_samples
            val_acc = val_correct / val_samples
            val_f1_score = val_f1.compute().item()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["train_f1"].append(train_f1_score)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["val_f1"].append(val_f1_score)

        print(
            f"Epoch [{epoch+1}/{epochs}] | "
            f"Train: loss={train_loss:.4f}, acc={train_acc:.4f}, f1={train_f1_score:.4f} | "
            f"Val: loss={val_loss:.4f}, acc={val_acc:.4f}, f1={val_f1_score:.4f}"
        )

    return history