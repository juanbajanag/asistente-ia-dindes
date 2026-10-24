"""
dense_retrieval.py
------------------
Retriever semántico usando qwen3-embedding:0.6b vía Ollama.

Integra:
- QueryRouter de Fase 2.3
- filtros estructurados
- consulta informativa para evitar falsos positivos
- abstención por umbral semántico
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .data_processing import KnowledgeRecord
from .dense_embeddings import OllamaEmbeddingClient
from .retrieval import QueryRouter, RetrievalResult


class DenseRetriever:
    def __init__(
        self,
        embedding_client: OllamaEmbeddingClient | None = None,
        model: str = "qwen3-embedding:0.6b",
    ):
        self.embedding_client = embedding_client or OllamaEmbeddingClient(model=model)
        self.records: list[KnowledgeRecord] = []
        self.corpus_embeddings: np.ndarray | None = None

    def fit(self, records: Iterable[KnowledgeRecord]) -> "DenseRetriever":
        self.records = list(records)
        if not self.records:
            raise ValueError("El corpus está vacío.")

        texts = [record.text for record in self.records]
        self.corpus_embeddings = self.embedding_client.embed(texts)
        return self

    @staticmethod
    def _passes_filters(
        record: KnowledgeRecord,
        source_type: str | None,
        access_level: str | None,
        source_status: str | None,
        inventory_status: str | None,
        category_contains: str | None,
    ) -> bool:
        if source_type and record.source_type != source_type:
            return False

        if record.source_type == "document":
            if access_level and record.metadata.get("access_level") != access_level.lower():
                return False
            if source_status and record.metadata.get("source_status") != source_status.lower():
                return False

        if record.source_type == "inventory":
            if inventory_status and record.metadata.get("estado") != inventory_status.lower():
                return False
            if category_contains:
                category = record.metadata.get("categoria", "").lower()
                if category_contains.lower() not in category:
                    return False

        return True

    @staticmethod
    def _has_explicit_metadata_filter(
        source_status: str | None,
        inventory_status: str | None,
        category_contains: str | None,
    ) -> bool:
        return any(
            value is not None
            for value in (source_status, inventory_status, category_contains)
        )

    def scores(self, query: str) -> np.ndarray:
        if self.corpus_embeddings is None:
            raise RuntimeError("Debe ejecutar fit() antes de scores().")

        query_vector = self.embedding_client.embed([query])[0]
        return self.corpus_embeddings @ query_vector

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: str | None = None,
        access_level: str | None = "autorizado",
        source_status: str | None = None,
        inventory_status: str | None = None,
        category_contains: str | None = None,
        min_score: float = 0.45,
        auto_route: bool = True,
    ) -> list[RetrievalResult]:

        if self.corpus_embeddings is None:
            raise RuntimeError("Debe ejecutar fit() antes de search().")

        query = query.strip()
        if not query:
            raise ValueError("La consulta no puede estar vacía.")

        if auto_route:
            inferred = QueryRouter.infer(query)
            source_type = source_type or inferred["source_type"]
            source_status = source_status or inferred["source_status"]
            inventory_status = inventory_status or inferred["inventory_status"]
            category_contains = category_contains or inferred["category_contains"]

        explicit_filter = self._has_explicit_metadata_filter(
            source_status, inventory_status, category_contains
        )
        informative_query = QueryRouter.informative_query(query)

        scoring_query = (
            informative_query
            if explicit_filter and informative_query
            else query
        )

        scores = self.scores(scoring_query)
        candidates = []

        for idx, (record, score) in enumerate(zip(self.records, scores)):
            if not self._passes_filters(
                record,
                source_type,
                access_level,
                source_status,
                inventory_status,
                category_contains,
            ):
                continue

            score = float(score)

            # Filtro estructurado puro: el metadato es evidencia suficiente.
            if explicit_filter and not informative_query:
                candidates.append((idx, score))
                continue

            # Pregunta semántica: debe superar el umbral.
            if score >= min_score:
                candidates.append((idx, score))

        candidates.sort(key=lambda item: item[1], reverse=True)

        results = []
        for rank, (idx, score) in enumerate(candidates[:top_k], start=1):
            record = self.records[idx]
            results.append(
                RetrievalResult(
                    rank=rank,
                    score=score,
                    record_id=record.record_id,
                    source_type=record.source_type,
                    title=record.title,
                    text=record.text,
                    source_file=record.source_file,
                    metadata=record.metadata,
                )
            )

        return results

    def explain_route(self, query: str) -> dict:
        route = QueryRouter.infer(query)
        route["informative_query"] = QueryRouter.informative_query(query)
        return route
