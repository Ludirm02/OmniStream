from __future__ import annotations

import hashlib
import math
import re

import numpy as np

TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingService:
    """Deterministic local embedding service.

    This avoids network dependencies while still mapping semantically similar texts
    into nearby vectors using hashed token projections.
    """

    def __init__(self, dim: int = 192) -> None:
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = TOKEN_RE.findall(text.lower())

        if not tokens:
            return vec

        for i, token in enumerate(tokens):
            token_hash = hashlib.sha256(f"{token}:{i % 3}".encode("utf-8")).hexdigest()
            h_int = int(token_hash, 16)

            idx_a = h_int % self.dim
            idx_b = (h_int // self.dim) % self.dim
            sign_a = 1.0 if (h_int & 1) else -1.0
            sign_b = 1.0 if (h_int & 2) else -1.0
            weight = 1.0 + (len(token) % 5) * 0.1

            vec[idx_a] += sign_a * weight
            vec[idx_b] += sign_b * (weight * 0.7)

        norm = float(np.linalg.norm(vec))
        if norm < 1e-12:
            return vec

        return vec / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if not a.any() or not b.any():
        return 0.0
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / denom)


def recency_decay(days_old: int, half_life_days: int = 45) -> float:
    if days_old <= 0:
        return 1.0
    return float(math.exp(-math.log(2) * days_old / half_life_days))
