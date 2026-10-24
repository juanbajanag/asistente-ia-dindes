"""
hybrid_retrieval.py
-------------------
Fase 2.3: híbrido TF-IDF + BM25 usando consulta informativa.
"""
from __future__ import annotations

import numpy as np
from typing import Iterable

from .data_processing import KnowledgeRecord
from .embeddings import TfidfEmbeddingModel
from .retrieval import QueryRouter, RetrievalResult
from .bm25 import BM25Retriever


def minmax_normalize(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    if scores.size == 0:
        return scores
    lo, hi = float(scores.min()), float(scores.max())
    if hi - lo <= 1e-12:
        return np.zeros_like(scores)
    return (scores - lo) / (hi - lo)


class HybridRetriever:
    def __init__(
        self,
        tfidf_weight: float = 0.5,
        bm25_weight: float = 0.5,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
    ):
        total = tfidf_weight + bm25_weight
        if tfidf_weight < 0 or bm25_weight < 0 or total <= 0:
            raise ValueError("Pesos inválidos.")
        self.tfidf_weight = tfidf_weight / total
        self.bm25_weight = bm25_weight / total
        self.tfidf_model = TfidfEmbeddingModel()
        self.bm25 = BM25Retriever(k1=bm25_k1, b=bm25_b)
        self.records = []
        self.tfidf_matrix = None
        self._fitted = False

    def fit(self, records: Iterable[KnowledgeRecord]) -> "HybridRetriever":
        self.records = list(records)
        self.tfidf_matrix = self.tfidf_model.fit_transform(
            [r.text for r in self.records]
        )
        self.bm25.fit(self.records)
        self._fitted = True
        return self

    def component_scores(self, query: str):
        tfidf_raw = self.tfidf_model.similarity(query, self.tfidf_matrix)
        bm25_raw = self.bm25.scores(query)
        tfidf_norm = minmax_normalize(tfidf_raw)
        bm25_norm = minmax_normalize(bm25_raw)
        hybrid = (
            self.tfidf_weight * tfidf_norm
            + self.bm25_weight * bm25_norm
        )
        return tfidf_raw, bm25_raw, hybrid

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
        access_level: str | None = "autorizado",
        source_status: str | None = None,
        inventory_status: str | None = None,
        category_contains: str | None = None,
        min_score: float = 0.01,
        auto_route: bool = True,
    ):
        query = query.strip()

        if auto_route:
            inferred = QueryRouter.infer(query)
            source_type = source_type or inferred["source_type"]
            source_status = source_status or inferred["source_status"]
            inventory_status = inventory_status or inferred["inventory_status"]
            category_contains = category_contains or inferred["category_contains"]

        explicit_filter = BM25Retriever._has_explicit_metadata_filter(
            source_status, inventory_status, category_contains
        )
        informative_query = QueryRouter.informative_query(query)
        scoring_query = (
            informative_query
            if explicit_filter and informative_query
            else query
        )

        _, _, scores = self.component_scores(scoring_query)
        candidates = []

        for idx, (record, score) in enumerate(zip(self.records, scores)):
            if not BM25Retriever._passes_filters(
                record, source_type, access_level, source_status,
                inventory_status, category_contains
            ):
                continue

            score = float(score)

            if explicit_filter and not informative_query:
                candidates.append((idx, score))
            elif score > 0.0 and score >= min_score:
                candidates.append((idx, score))

        candidates.sort(key=lambda item: item[1], reverse=True)

        results = []
        for rank, (idx, score) in enumerate(candidates[:top_k], start=1):
            record = self.records[idx]
            results.append(
                RetrievalResult(
                    rank, score, record.record_id, record.source_type,
                    record.title, record.text, record.source_file, record.metadata
                )
            )
        return results
