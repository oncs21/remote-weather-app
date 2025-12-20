import torch
import torchmetrics

from PIL import Image

def infer_on_test_data(test_dl,
          model,
          loss_fn,
          device):

    with torch.inference_mode():
        model.eval()

        test_loss = 0.0
        test_correct = 0
        test_samples = 0

        test_f1 = torchmetrics.F1Score(
                        task="multiclass",
                        num_classes=5,
                        average="macro"
                    ).to(device)

        for images, labels in test_dl:
            images = images.to(device)
            labels = images.to(device)

            preds = model(images)
            loss = loss_fn(preds, labels)


            test_loss += loss.item() * labels.size(0)
            test_correct += (preds.argmax(dim=1) == labels).sum().item()
            test_samples += labels.size(0)
            test_f1.update(preds, labels)

    test_loss /= test_samples
    test_acc = test_correct / test_samples
    test_f1_score = test_f1.compute().item()

    return test_acc, test_f1_score


def infer_on_unknown_data(images: list[Image.Image],
          model,
          device,
          transform
          ):
    
    pred_labels = []

    with torch.inference_mode():
        for image in images:
            if transform is None:
                raise ValueError("Transformations are required for test images")
            
            image = transform(image)
            image = image.unsqueeze(0).to(device)

            preds = model(image)
            pred_label = torch.argmax(preds, dim=1).item()
            pred_labels.append(pred_label)

    return pred_labels