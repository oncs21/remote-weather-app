import os
import shutil
import numpy as np
import pandas as pd
import torch

from torch.utils.data import random_split, Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms as T
from PIL import Image
from pathlib import Path
from collections import Counter
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import RandomOverSampler
from config import Paths, Splits


class CloudCoverDataset(Dataset):
    def __init__(self, 
                 root: Path = Paths.root, 
                 metadata_path: Path = Paths.mtdata, 
                 transformations=None
                 ) -> None:
        
        self.transformations = transformations
        self.root = root
        self.meta_data = pd.read_csv(metadata_path)
        self.fetch_metadata()
        self.encode_labels()


    def fetch_metadata(self) -> None:
        im_paths: list[str] = []
        im_lbls: list[str] = []

        for i in range(len(self.meta_data)):
            data = self.meta_data.iloc[i]
            im_path = data["image"]
            im_lbl = data["choice"]

            im_paths.append("data/"+im_path)
            im_lbls.append(im_lbl)
        
        self.im_paths = im_paths
        self.im_lbls = im_lbls

        counts = Counter(im_lbls)
        self.lbl_counts = len(counts.keys())


    def encode_labels(self) -> None:
        im_lbls = self.im_lbls
        label_encoder = LabelEncoder()

        self.encoded_labels = label_encoder.fit_transform(im_lbls)
        self.lbl_mapping = dict(zip(label_encoder.classes_, range(len(label_encoder.classes_))))


    def __len__(self) -> int:
        return len(self.im_paths)
    

    def __getitem__(self, 
                    idx: int
                    ) -> tuple[Image.Image, int]:
        img = Image.open(self.im_paths[idx]).convert("RGB")
        lbl = self.lbl_mapping[self.im_lbls[idx]]

        if self.transformations is not None:
            img = self.transformations(img)

        return img, lbl
    
     

def get_dataloaders(root: Path, 
                    transformations, 
                    dataset,
                    batch_size,
                    split: list = [Splits.train, Splits.test, Splits.val]
                    ) -> tuple[DataLoader, DataLoader, DataLoader]:
    
    total_len = len(dataset)
    train_len = int(total_len * split[0])
    val_len = int(total_len * split[2])
    test_len = total_len - train_len - val_len

    train_ds, val_ds, test_ds = random_split(dataset, lengths = [train_len, val_len, test_len])

    train_indices = train_ds.indices
    train_labels = [dataset.encoded_labels[i] for i in train_indices]

    counts = Counter(train_labels)
    num_samples = len(train_labels)
    class_weight = {c: num_samples / cnt for c, cnt in counts.items()}
    sample_weights = torch.Tensor([class_weight[y] for y in train_labels])

    sampler = WeightedRandomSampler(
        weights=sample_weights.tolist(),
        num_samples=len(sample_weights),
        replacement=True
    )

    train_dl = DataLoader(train_ds, batch_size=batch_size, sampler=sampler)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_dl = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    return train_dl, val_dl, test_dl