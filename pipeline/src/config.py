from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Paths:
    root: Path = Path("")
    data: Path = root / "data"
    mtdata: Path = data / "cloud_classification_export.csv"
    raw: Path = data / "images"
    processed: Path = data / "processed"

@dataclass(frozen=True)
class Splits:
    train: float = 0.7
    val: float = 0.15
    test: float = 0.15