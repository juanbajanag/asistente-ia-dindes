"""
Baseline vectorial TF-IDF para validar el pipeline antes de embeddings densos.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class TfidfEmbeddingModel:
    max_features: int = 5000
    ngram_range: tuple[int, int] = (1, 2)
    min_df: int = 1

    def __post_init__(self) -> None:
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            min_df=self.min_df,
        )
        self._fitted = False

    def fit_transform(self, texts: list[str]) -> csr_matrix:
        if not texts:
            raise ValueError("No se recibieron textos para indexar.")
        matrix = self.vectorizer.fit_transform(texts)
        self._fitted = True
        return matrix

    def transform(self, texts: list[str]) -> csr_matrix:
        if not self._fitted:
            raise RuntimeError("El modelo debe ajustarse antes de transformar consultas.")
        return self.vectorizer.transform(texts)

    def similarity(self, query: str, corpus_matrix: csr_matrix) -> np.ndarray:
        query_vector = self.transform([query])
        return cosine_similarity(query_vector, corpus_matrix).ravel()
