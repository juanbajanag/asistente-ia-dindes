"""
bm25.py
-------
Fase 2.3: BM25 usando consulta informativa cuando hay filtros estructurados.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable
import numpy as np

from .data_processing import KnowledgeRecord
from .retrieval import QueryRouter, RetrievalResult

TOKEN_PATTERN = re.compile(r"\b\w+\b", flags=re.UNICODE)

def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.records = []
        self.doc_tokens = []
        self.avgdl = 0.0
        self.idf = {}
        self._fitted = False

    def fit(self, records: Iterable[KnowledgeRecord]) -> "BM25Retriever":
        self.records = list(records)
        if not self.records:
            raise ValueError("El corpus está vacío.")

        self.doc_tokens = [tokenize(r.text) for r in self.records]
        self.avgdl = sum(len(x) for x in self.doc_tokens) / len(self.doc_tokens)

        doc_freqs = Counter()
        for tokens in self.doc_tokens:
            for token in set(tokens):
                doc_freqs[token] += 1

        n_docs = len(self.doc_tokens)
        self.idf = {
            token: math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            for token, df in doc_freqs.items()
        }
        self._fitted = True
        return self

    def _score_one(self, query_tokens, doc_tokens):
        freqs = Counter(doc_tokens)
        dl = len(doc_tokens)
        score = 0.0
        for token in query_tokens:
            tf = freqs.get(token, 0)
            if tf == 0:
                continue
            idf = self.idf.get(token, 0.0)
            denom = tf + self.k1 * (
                1.0 - self.b + self.b * dl / max(self.avgdl, 1e-9)
            )
            score += idf * ((tf * (self.k1 + 1.0)) / denom)
        return float(score)

    def scores(self, query: str) -> np.ndarray:
        q_tokens = tokenize(query)
        return np.array(
            [self._score_one(q_tokens, tokens) for tokens in self.doc_tokens],
            dtype=float,
        )

    @staticmethod
    def _passes_filters(
        record, source_type, access_level, source_status,
        inventory_status, category_contains
    ):
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
    def _has_explicit_metadata_filter(source_status, inventory_status, category_contains):
        return any(
            value is not None
            for value in (source_status, inventory_status, category_contains)
        )

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
