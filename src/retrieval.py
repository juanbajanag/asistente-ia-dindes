"""
retrieval.py
------------
Fase 2.3: abstención basada en contenido informativo.

Problema corregido:
Una consulta no respondible como
"¿Qué herramienta de IA está disponible en DINDES para entrenar modelos?"
podía obtener score positivo debido a palabras estructurales como
"disponible", "DINDES" o "inventario".

Solución:
Cuando existe un filtro de metadatos Y además contenido informativo específico,
la similitud se calcula usando solo los términos informativos de la consulta.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .data_processing import KnowledgeRecord
from .embeddings import TfidfEmbeddingModel


@dataclass
class RetrievalResult:
    rank: int
    score: float
    record_id: str
    source_type: str
    title: str
    text: str
    source_file: str
    metadata: dict

    def citation_label(self) -> str:
        if self.source_type == "document":
            return (
                f"{self.metadata.get('document_id', self.record_id)} | "
                f"{self.metadata.get('section', '')} | "
                f"versión {self.metadata.get('version', '')} | "
                f"estado {self.metadata.get('source_status', '')}"
            ).strip(" |")

        return (
            f"{self.record_id} | inventario | "
            f"{self.metadata.get('categoria', '')} | "
            f"estado {self.metadata.get('estado', '')}"
        ).strip(" |")


class QueryRouter:
    INVENTORY_TERMS = (
        "inventario", "equipo", "equipos", "material", "materiales",
        "computador", "computadores", "herramienta", "herramientas",
        "disponible", "disponibles", "existencia", "stock",
        "impresora", "impresoras",
    )

    DOCUMENT_TERMS = (
        "documento", "documentos", "informe", "informes", "manual",
        "manuales", "acta", "actas", "especificación", "especificaciones",
        "requisito", "requisitos", "proyecto", "proyectos",
        "vigente", "vigentes", "borrador", "borradores",
    )

    QUANTITY_TERMS = (
        "cuántos", "cuántas", "cuantos", "cuantas",
        "cantidad", "cuánto", "cuánta", "cuanto", "cuanta",
    )

    STRUCTURAL_WORDS = {
        "que", "qué", "cual", "cuál", "cuales", "cuáles",
        "existe", "existen", "hay", "esta", "está", "estan", "están",
        "se", "encuentra", "encuentran",
        "en", "el", "la", "los", "las", "un", "una", "unos", "unas",
        "de", "del", "para", "por", "y", "o",
        "dindes",
        "inventario",
        "equipo", "equipos",
        "documento", "documentos",
        "vigente", "vigentes",
        "borrador", "borradores",
        "disponible", "disponibles",
        "operativo", "operativos",
        "stock", "existencia",
    }

    @classmethod
    def infer(cls, query: str) -> dict:
        q = query.lower()

        filters = {
            "source_type": None,
            "source_status": None,
            "inventory_status": None,
            "category_contains": None,
        }

        inv_hits = sum(term in q for term in cls.INVENTORY_TERMS)
        doc_hits = sum(term in q for term in cls.DOCUMENT_TERMS)

        if "inventario" in q or inv_hits > doc_hits:
            filters["source_type"] = "inventory"
        elif doc_hits > inv_hits:
            filters["source_type"] = "document"

        if "vigente" in q or "vigentes" in q:
            filters["source_type"] = "document"
            filters["source_status"] = "vigente"

        if "borrador" in q or "borradores" in q:
            filters["source_type"] = "document"
            filters["source_status"] = "borrador"

        if "operativo" in q or "operativos" in q:
            filters["source_type"] = "inventory"
            filters["inventory_status"] = "operativo"

        asks_quantity = any(term in q for term in cls.QUANTITY_TERMS)

        if ("disponible" in q or "disponibles" in q) and not asks_quantity:
            filters["source_type"] = "inventory"
            filters["inventory_status"] = "disponible"

        if (
            "computación" in q
            or "computacion" in q
            or "computador" in q
            or "computadores" in q
        ):
            filters["source_type"] = "inventory"
            filters["category_contains"] = "comput"

        return filters

    @classmethod
    def informative_terms(cls, query: str) -> list[str]:
        tokens = re.findall(r"\b\w+\b", query.lower(), flags=re.UNICODE)
        return [
            token
            for token in tokens
            if token not in cls.STRUCTURAL_WORDS and len(token) > 1
        ]

    @classmethod
    def informative_query(cls, query: str) -> str:
        return " ".join(cls.informative_terms(query)).strip()

    @classmethod
    def requires_semantic_match(cls, query: str) -> bool:
        return bool(cls.informative_query(query))


class TfidfRetriever:
    def __init__(self, embedding_model: TfidfEmbeddingModel | None = None):
        self.embedding_model = embedding_model or TfidfEmbeddingModel()
        self.records: list[KnowledgeRecord] = []
        self.corpus_matrix = None

    def fit(self, records: Iterable[KnowledgeRecord]) -> "TfidfRetriever":
        self.records = list(records)
        if not self.records:
            raise ValueError("El corpus está vacío.")
        self.corpus_matrix = self.embedding_model.fit_transform(
            [record.text for record in self.records]
        )
        return self

    def _passes_filters(
        self,
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
    ) -> list[RetrievalResult]:

        if self.corpus_matrix is None:
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

        # En consultas con filtro + contenido específico, eliminamos del scoring
        # las palabras puramente estructurales para evitar falsos positivos.
        scoring_query = (
            informative_query
            if explicit_filter and informative_query
            else query
        )

        scores = self.embedding_model.similarity(scoring_query, self.corpus_matrix)
        candidates = []

        for idx, (record, score) in enumerate(zip(self.records, scores)):
            if not self._passes_filters(
                record, source_type, access_level, source_status,
                inventory_status, category_contains
            ):
                continue

            score = float(score)

            # Filtro estructurado puro.
            if explicit_filter and not informative_query:
                candidates.append((idx, score))
                continue

            # Consulta con contenido: requiere evidencia léxica real.
            if score > 0.0 and score >= min_score:
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
        route["informative_terms"] = QueryRouter.informative_terms(query)
        route["informative_query"] = QueryRouter.informative_query(query)
        return route


def format_results_for_console(results: list[RetrievalResult]) -> str:
    if not results:
        return (
            "No se encontró evidencia suficiente con los filtros y el umbral "
            "actuales. El sistema debe abstenerse de responder."
        )

    lines = []
    for result in results:
        lines.append(
            f"[{result.rank}] score={result.score:.4f} | "
            f"{result.citation_label()} | {result.title}"
        )
        lines.append(f"    {result.text}")
        lines.append("")
    return "\n".join(lines)
