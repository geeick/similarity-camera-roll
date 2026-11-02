"""Small-library image similarity algorithms using normalized embeddings."""
from __future__ import annotations
import numpy as np

def normalize(vectors: np.ndarray) -> np.ndarray:
    a = np.asarray(vectors, dtype=np.float32)
    if a.ndim != 2:
        raise ValueError("Expected a 2D array of embeddings")
    return a / np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-12)

def find_similar(vectors: np.ndarray, selected: int, limit: int = 12) -> list[tuple[int, float]]:
    arr = normalize(vectors)
    if not 0 <= selected < len(arr):
        raise IndexError("Selected photo is outside the library")
    scores = arr @ arr[selected]
    order = np.argsort(-scores, kind="stable")
    return [(int(i), float(scores[i])) for i in order if i != selected][:limit]

def similarity_groups(vectors: np.ndarray, threshold: float = 0.82) -> list[list[int]]:
    """Greedy centroid clustering; contains every photo, including singletons."""
    arr = normalize(vectors)
    centers: list[np.ndarray] = []
    groups: list[list[int]] = []
    for index, vector in enumerate(arr):
        if not centers:
            centers.append(vector.copy())
            groups.append([index])
            continue
        similarities = np.array([float(center @ vector) for center in centers])
        best = int(np.argmax(similarities))
        if float(similarities[best]) >= threshold:
            groups[best].append(index)
            center = np.mean(arr[groups[best]], axis=0)
            centers[best] = center / max(float(np.linalg.norm(center)), 1e-12)
        else:
            centers.append(vector.copy())
            groups.append([index])
    return sorted(groups, key=lambda group: (-len(group), group[0]))

def continuous_order(vectors: np.ndarray, starting_index: int = 0) -> list[int]:
    """Greedy nearest-neighbor walk through each image exactly once."""
    arr = normalize(vectors)
    n = len(arr)
    if n == 0:
        return []
    if not 0 <= starting_index < n:
        raise IndexError("Starting photo is outside the library")
    available = np.ones(n, dtype=bool)
    available[starting_index] = False
    path = [starting_index]
    for _ in range(n - 1):
        scores = arr @ arr[path[-1]]
        scores[~available] = -np.inf
        nxt = int(np.argmax(scores))
        path.append(nxt)
        available[nxt] = False
    return path
