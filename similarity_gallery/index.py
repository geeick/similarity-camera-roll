"""Scan a local image folder and cache CLIP embeddings in SQLite.

Nothing is copied, deleted, moved, or uploaded.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os
import sqlite3
from typing import Callable
import numpy as np
from PIL import Image, ImageOps

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}
MODEL_ID = "ViT-B-32/laion2b_s34b_b79k"
CACHE_PATH = Path(__file__).resolve().parent.parent / ".cache" / "photos.sqlite3"

@dataclass
class Photo:
    path: Path
    vector: np.ndarray

def discover_images(folder: Path, limit: int = 300) -> list[Path]:
    folder = folder.expanduser().resolve()
    if not folder.is_dir():
        raise ValueError(f"Folder does not exist: {folder}")
    found: list[Path] = []
    for root, dirs, files in os.walk(folder, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for filename in sorted(files):
            if filename.startswith("."):
                continue
            path = Path(root) / filename
            if path.suffix.lower() in SUPPORTED and not path.is_symlink():
                found.append(path)
                if len(found) >= limit:
                    return found
    return found

def _db() -> sqlite3.Connection:
    CACHE_PATH.parent.mkdir(exist_ok=True, parents=True)
    connection = sqlite3.connect(CACHE_PATH)
    connection.execute("""CREATE TABLE IF NOT EXISTS images (
        path TEXT PRIMARY KEY,
        modified_ns INTEGER NOT NULL,
        file_size INTEGER NOT NULL,
        model_id TEXT NOT NULL,
        vector BLOB NOT NULL
    )""")
    return connection

@lru_cache(maxsize=1)
def load_model():
    import torch
    import open_clip
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    model = model.to(device)
    model.eval()
    return model, preprocess, device

def _read_rgb(path: Path) -> Image.Image:
    with Image.open(path) as original:
        return ImageOps.exif_transpose(original).convert("RGB")

def register_heic() -> None:
    from pillow_heif import register_heif_opener
    register_heif_opener()

def scan(folder: Path, limit: int = 300,
         progress: Callable[[int, int], None] | None = None) -> tuple[list[Photo], list[str]]:
    """Return images with cached or freshly generated embeddings."""
    register_heic()
    paths = discover_images(folder, limit=limit)
    indexed: list[Photo] = []
    errors: list[str] = []
    pending: list[tuple[Path, os.stat_result]] = []
    total = len(paths)
    with _db() as db:
        for path in paths:
            try:
                stat = path.stat()
                row = db.execute(
                    "SELECT vector, modified_ns, file_size, model_id FROM images WHERE path=?",
                    (str(path.resolve()),)
                ).fetchone()
                if row and row[1] == stat.st_mtime_ns and row[2] == stat.st_size and row[3] == MODEL_ID:
                    vector = np.frombuffer(row[0], dtype=np.float32).copy()
                    if vector.size == 512:
                        indexed.append(Photo(path, vector))
                        continue
                pending.append((path, stat))
            except OSError as exc:
                errors.append(f"{path.name}: {exc}")
        if pending:
            import torch
            model, preprocess, device = load_model()
            batch_images = []
            batch_records = []
            def flush() -> None:
                if not batch_images:
                    return
                batch = torch.stack(batch_images).to(device)
                with torch.inference_mode():
                    vectors = model.encode_image(batch)
                    vectors /= vectors.norm(dim=-1, keepdim=True).clamp(min=1e-12)
                arr = vectors.float().cpu().numpy()
                for (path, stat), vector in zip(batch_records, arr):
                    output = np.asarray(vector, dtype=np.float32)
                    db.execute("""INSERT INTO images(path, modified_ns, file_size, model_id, vector)
                                  VALUES(?, ?, ?, ?, ?)
                                  ON CONFLICT(path) DO UPDATE SET
                                  modified_ns=excluded.modified_ns,
                                  file_size=excluded.file_size,
                                  model_id=excluded.model_id,
                                  vector=excluded.vector""",
                               (str(path.resolve()), stat.st_mtime_ns, stat.st_size, MODEL_ID, output.tobytes()))
                    indexed.append(Photo(path, output))
                batch_images.clear()
                batch_records.clear()
                db.commit()
                if progress:
                    progress(len(indexed), total)
            for path, stat in pending:
                try:
                    batch_images.append(preprocess(_read_rgb(path)))
                    batch_records.append((path, stat))
                    if len(batch_images) >= 16:
                        flush()
                except Exception as exc:
                    errors.append(f"{path.name}: {exc}")
            flush()
    by_path = {photo.path: photo for photo in indexed}
    result = [by_path[p] for p in paths if p in by_path]
    if progress:
        progress(total, total)
    return result, errors
