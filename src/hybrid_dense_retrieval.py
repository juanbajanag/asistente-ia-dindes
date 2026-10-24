"""
hybrid_dense_retrieval.py
-------------------------
Fusión híbrida Dense + BM25 mediante Reciprocal Rank Fusion (RRF).

Se utiliza RRF en lugar de sumar scores directamente porque BM25 y cosine
similarity están en escalas diferentes.
"""

from __future__ import annotations

from typing import Iterable

from .data_processing import KnowledgeRecord
from .dense_retrieval import DenseRetriever
from .bm25 import BM25Retriever
from .retrieval import QueryRouter, RetrievalResult


class DenseBM25HybridRetriever:
    def __init__(
        self,
        dense_model: str = "qwen3-embedding:0.6b",
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        bm25_weight: float = 1.0,
    ):
        self.dense = DenseRetriever(model=dense_model)
        self.bm25 = BM25Retriever()
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.records: list[KnowledgeRecord] = []

    def fit(self, records: Iterable[KnowledgeRecord]) -> "DenseBM25HybridRetriever":
        self.records = list(records)
        self.dense.fit(self.records)
        self.bm25.fit(self.records)
        return self

    @staticmethod
    def _result_key(result: RetrievalResult) -> str:
        if result.source_type == "document":
            return str(result.metadata.get("document_id", result.record_id))
        return str(result.record_id)

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
        access_level: str | None = "autorizado",
        source_status: str | None = None,
        inventory_status: str | None = None,
        category_contains: str | None = None,
        dense_min_score: float = 0.45,
        bm25_min_score: float = 0.01,
        auto_route: bool = True,
    ) -> list[RetrievalResult]:

        # Recuperamos más candidatos de cada rama antes de fusionar.
        candidate_k = max(top_k * 3, 10)

        dense_results = self.dense.search(
            query=query,
            top_k=candidate_k,
            source_type=source_type,
            access_level=access_level,
            source_status=source_status,
            inventory_status=inventory_status,
            category_contains=category_contains,
            min_score=dense_min_score,
            auto_route=auto_route,
        )

        bm25_results = self.bm25.search(
            query=query,
            top_k=candidate_k,
            source_type=source_type,
            access_level=access_level,
            source_status=source_status,
            inventory_status=inventory_status,
            category_contains=category_contains,
            min_score=bm25_min_score,
            auto_route=auto_route,
        )

        combined = {}

        for result in dense_results:
            key = self._result_key(result)
            combined.setdefault(
                key,
                {"result": result, "rrf": 0.0}
            )
            combined[key]["rrf"] += (
                self.dense_weight / (self.rrf_k + result.rank)
            )

        for result in bm25_results:
            key = self._result_key(result)
            combined.setdefault(
                key,
                {"result": result, "rrf": 0.0}
            )
            combined[key]["rrf"] += (
                self.bm25_weight / (self.rrf_k + result.rank)
            )

        ranked = sorted(
            combined.values(),
            key=lambda item: item["rrf"],
            reverse=True,
        )

        final = []
        for rank, item in enumerate(ranked[:top_k], start=1):
            base = item["result"]
            final.append(
                RetrievalResult(
                    rank=rank,
                    score=float(item["rrf"]),
                    record_id=base.record_id,
                    source_type=base.source_type,
                    title=base.title,
                    text=base.text,
                    source_file=base.source_file,
                    metadata=base.metadata,
                )
            )

        return final
